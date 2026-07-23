import os
import time
import uuid
from typing import Optional

import cv2

from services.landmark_service import LandmarkService
from services.blink_service import BlinkService
from services.headpose_service import HeadPoseService
from services.embedding_service import EmbeddingService
from services.similarity_service import SimilarityService
from services.rolling_buffer import RollingBuffer, PoseEarSample
from agents.antispoof_agent import AntiSpoofAgent
from services.record_service import save_verification_record

FACE_MATCH_THRESHOLD = 0.55  # matches VerificationAgent's threshold
FACE_MATCH_MARGIN = 0.05     # matches VerificationAgent's margin -> review band is [0.50, 0.55)
CONSECUTIVE_LOW_SIMILARITY_REQUIRED = 4  # frames of low similarity before flagging (avoids motion-blur false positives)
CONSECUTIVE_SPOOF_REQUIRED = 3
ROLLING_WINDOW_SECONDS = 10.0


def _confidence_label(similarity: float) -> str:
    """Mirrors VerificationAgent.get_confidence exactly, so labels match
    across the one-shot and continuous verification paths."""
    if similarity >= 0.90:
        return "Very High"
    elif similarity >= 0.70:
        return "High"
    elif similarity >= 0.55:
        return "Medium"
    return "Low"


def _frame_decision(similarity: float) -> str:
    """Mirrors VerificationAgent's pass/review/fail split for a single reading."""
    if similarity >= FACE_MATCH_THRESHOLD:
        return "pass"
    elif similarity <= FACE_MATCH_THRESHOLD - FACE_MATCH_MARGIN:
        return "fail"
    return "review"


class LiveCallSession:
    def __init__(self, room_id: str, applicant_id: str, aadhaar_path: str):
        self.room_id = room_id
        self.applicant_id = applicant_id
        self.aadhaar_path = aadhaar_path

        self.landmark = LandmarkService()
        self.blink = BlinkService()
        self.headpose = HeadPoseService()
        self.antispoof = AntiSpoofAgent()
        self.embedding_service = EmbeddingService()

        aadhaar_img = cv2.imread(aadhaar_path)
        if aadhaar_img is None:
            raise ValueError(f"Unable to read Aadhaar reference image at {aadhaar_path}")
        # Phase 1 reference embedding, computed once -- this is the anchor
        # Phase 3.3 continuously compares against.
        self.reference_embedding = self.embedding_service.extract(aadhaar_img)

        self.buffer = RollingBuffer(window_seconds=ROLLING_WINDOW_SECONDS)
        self.previous_blink_count = 0

        self.consecutive_low_similarity = 0
        self.consecutive_spoof = 0
        self.consecutive_no_face = 0

        self.spoof_checks: list[bool] = []
        self.spoof_confidences: list[float] = []

        self.last_similarity: Optional[float] = None
        self.identity_flagged = False
        self.spoof_flagged = False

        self.event_log: list[dict] = []
        self.start_time = time.time()

    def _uploads_dir(self) -> str:
        d = os.path.join(os.environ.get("DATA_DIR", "."), "uploads")
        os.makedirs(d, exist_ok=True)
        return d

    def _log_event(self, kind: str, **data) -> dict:
        event = {"ts": time.time(), "kind": kind, **data}
        self.event_log.append(event)
        print(f"[CALL {self.room_id}] {event}")
        return event

    def _check_spoof(self, frame) -> Optional[dict]:
        tmp_path = os.path.join(self._uploads_dir(), f"tmp_spoof_{uuid.uuid4().hex}.jpg")
        cv2.imwrite(tmp_path, frame)
        try:
            return self.antispoof.verify(tmp_path)
        except Exception as exc:
            self._log_event("spoof_check_error", error=str(exc))
            return None
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def process_frame(self, frame, ts: Optional[float] = None) -> dict:
        """Call once per sampled frame (~1/sec) from the stream tap."""
        ts = ts or time.time()
        timestamp_ms = int(ts * 1000)

        results = self.landmark.detect(frame, timestamp_ms)
        face_detected = bool(results.face_landmarks)

        if not face_detected:
            self.consecutive_no_face += 1
            if self.consecutive_no_face == 3:
                self._log_event("face_not_visible")
            return self.status(face_detected=False)

        self.consecutive_no_face = 0
        face = results.face_landmarks[0]

        pose = self.headpose.estimate(face, frame)
        ear = self.blink.calculate(face)
        count = self.blink.update(ear)
        blink_increment = count > self.previous_blink_count
        self.previous_blink_count = count

        self.buffer.push(PoseEarSample(
            timestamp=ts,
            direction=pose["direction"],
            yaw=pose.get("yaw"),
            pitch=pose.get("pitch"),
            ear=ear,
            blink=blink_increment,
        ))

        # --- 3.4 continuous anti-spoofing (pulled up from "future work") ---
        spoof_result = self._check_spoof(frame)
        if spoof_result is not None:
            is_live = bool(spoof_result.get("is_live"))
            confidence = float(spoof_result.get("confidence", 0))
            self.spoof_checks.append(is_live)
            self.spoof_confidences.append(confidence)

            self.consecutive_spoof = 0 if is_live else self.consecutive_spoof + 1
            if self.consecutive_spoof >= CONSECUTIVE_SPOOF_REQUIRED and not self.spoof_flagged:
                self.spoof_flagged = True
                self._log_event("spoof_flagged", confidence=confidence)

        # --- 3.3 continuous face-match ---
        try:
            live_embedding = self.embedding_service.extract(frame)
            similarity = SimilarityService.cosine_similarity(self.reference_embedding, live_embedding)
            self.last_similarity = similarity
            frame_decision = _frame_decision(similarity)

            # Only "fail"-grade frames (below threshold - margin) count toward
            # the mismatch streak; "review"-band frames don't reset OR advance
            # it, so a run of borderline readings doesn't silently clear a
            # building streak the way a full reset-on-any-non-fail would.
            if frame_decision == "fail":
                self.consecutive_low_similarity += 1
            elif frame_decision == "pass":
                self.consecutive_low_similarity = 0

            if self.consecutive_low_similarity >= CONSECUTIVE_LOW_SIMILARITY_REQUIRED and not self.identity_flagged:
                self.identity_flagged = True
                self._log_event("identity_mismatch_flagged", similarity=round(similarity, 4))

        except Exception as exc:
            # MediaPipe found a face but InsightFace couldn't embed it
            # (angle/blur/occlusion) -- skip, don't count as a mismatch.
            self._log_event("embedding_skip", error=str(exc))

        return self.status(face_detected=True)

    def status(self, face_detected: bool) -> dict:
        """What the officer's dashboard polls/subscribes to."""
        return {
            "room_id": self.room_id,
            "face_detected": face_detected,
            "similarity": round(self.last_similarity, 4) if self.last_similarity is not None else None,
            "confidence": _confidence_label(self.last_similarity) if self.last_similarity is not None else None,
            "identity_flagged": self.identity_flagged,
            "spoof_flagged": self.spoof_flagged,
            "consecutive_no_face": self.consecutive_no_face,
        }

    def spoof_summary(self) -> dict:
        """Mirrors LivenessSession.spoof_summary() exactly, so audit
        records look the same shape regardless of which flow produced them."""
        if not self.spoof_confidences:
            return {
                "spoof_checks_count": 0,
                "spoof_live_ratio": None,
                "spoof_min_confidence": None,
                "spoof_max_confidence": None,
            }
        live_ratio = sum(self.spoof_checks) / len(self.spoof_checks)
        return {
            "spoof_checks_count": len(self.spoof_checks),
            "spoof_live_ratio": round(live_ratio, 3),
            "spoof_min_confidence": round(min(self.spoof_confidences), 3),
            "spoof_max_confidence": round(max(self.spoof_confidences), 3),
        }

    def finalize(self, decision_override: Optional[str] = None) -> dict:
        """Call when the officer ends the call -- writes the audit record."""
        duration = time.time() - self.start_time
        decision = decision_override or ("fail" if (self.identity_flagged or self.spoof_flagged) else "pass")

        error_message = None
        if self.identity_flagged:
            error_message = f"Identity mismatch flagged (similarity={self.last_similarity})"
        elif self.spoof_flagged:
            error_message = "Spoof suspected during call"

        save_verification_record(
            source="live_call_session",
            decision=decision,
            similarity=self.last_similarity,
            threshold=FACE_MATCH_THRESHOLD,
            confidence=_confidence_label(self.last_similarity) if self.last_similarity is not None else None,
            duration_seconds=round(duration, 2),
            error_message=error_message,
            challenge_timings=None,
            **self.spoof_summary(),
        )
        return {"decision": decision, "events": self.event_log}