import cv2
import time
import os
import uuid
import json
from datetime import datetime

from services.landmark_service import LandmarkService
from services.blink_service import BlinkService
from services.headpose_service import HeadPoseService
from services.challenge_service import ChallengeService
from agents.verification_agent import VerificationAgent
from services.capture_service import CaptureService
from services.record_service import save_verification_record
from agents.antispoof_agent import AntiSpoofAgent

class LivenessSession:

    def __init__(self, aadhaar_path):
        self.aadhaar_path = aadhaar_path
        self.landmark = LandmarkService()
        self.blink = BlinkService()
        self.headpose = HeadPoseService()
        self.challenge = ChallengeService()
        self.capture = CaptureService()
        self.verification_agent = VerificationAgent()
        self.antispoof = AntiSpoofAgent()

        self.previous_blink_count = 0
        self.verification_done = False
        self.verification_result = None
        self.capture_path = None
        self.start_time = time.time()

        self.frame_count = 0
        self.spoof_checks = []
        self.spoof_confidences = []
        self.SPOOF_CHECK_INTERVAL = 5
        self.MIN_SPOOF_CHECKS = 4
        self.LIVE_RATIO_REQUIRED = 0.7

        self.challenge_timings = {}
        self._current_challenge_name = self.challenge.current().name if self.challenge.current() else None
        self._current_challenge_start = time.time()

        self.last_pose = None
        self.last_ear = None

    def _uploads_dir(self):
        return os.path.join(os.environ.get("DATA_DIR", "."), "uploads")

    def check_spoof(self, frame):
        uploads_dir = self._uploads_dir()
        os.makedirs(uploads_dir, exist_ok=True)
        tmp_path = os.path.join(uploads_dir, f"tmp_spoof_{uuid.uuid4().hex}.jpg")
        cv2.imwrite(tmp_path, frame)
        try:
            result = self.antispoof.verify(tmp_path)
            self.spoof_checks.append(bool(result.get("is_live")))
            self.spoof_confidences.append(float(result.get("confidence", 0)))
            print(f"[SPOOF CHECK] {result}")
        except Exception as exc:
            print(f"[SPOOF CHECK ERROR] {exc}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def is_suspected_spoof(self):
        if len(self.spoof_checks) < self.MIN_SPOOF_CHECKS:
            return False
        live_ratio = sum(self.spoof_checks) / len(self.spoof_checks)
        return live_ratio < self.LIVE_RATIO_REQUIRED

    def spoof_summary(self):
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

    def _record_challenge_transition(self):
        current = self.challenge.current()
        new_name = current.name if current else "FINISHED"

        if new_name != self._current_challenge_name:
            elapsed = time.time() - self._current_challenge_start
            self.challenge_timings[self._current_challenge_name] = round(elapsed, 2)
            self._current_challenge_name = new_name
            self._current_challenge_start = time.time()

    def process_frame(self, frame):
        timestamp = int(time.time() * 1000)
        results = self.landmark.detect(frame, timestamp)

        face_detected = bool(results.face_landmarks)

        if face_detected:
            face = results.face_landmarks[0]

            pose = self.headpose.estimate(face, frame)
            ear = self.blink.calculate(face)
            count = self.blink.update(ear)
            blink_increment = count > self.previous_blink_count
            self.previous_blink_count = count

            self.last_pose = pose
            self.last_ear = ear

            self.challenge.update(pose["direction"], blink_increment)
            self._record_challenge_transition()

            self.frame_count += 1
            if self.frame_count % self.SPOOF_CHECK_INTERVAL == 0:
                self.check_spoof(frame)

                if not self.verification_done and self.is_suspected_spoof():
                    summary = self.spoof_summary()
                    print(f"[SPOOF GATE TRIGGERED] {summary}")

                    self.verification_result = {
                        "decision": "fail",
                        "similarity": None,
                        "threshold": None,
                        "confidence": None,
                        "spoof_detected": True,
                        "spoof_live_ratio": summary["spoof_live_ratio"],
                    }
                    self.verification_done = True

                    duration = time.time() - self.start_time
                    save_verification_record(
                        source="liveness_session",
                        decision="fail",
                        duration_seconds=round(duration, 2),
                        error_message=f"Spoof suspected (live_ratio={summary['spoof_live_ratio']})",
                        challenge_timings=json.dumps(self.challenge_timings),
                        **summary,
                    )
                    return self.response(face_detected=face_detected)

            if self.challenge.finished() and not self.capture.ready():
                self.capture.evaluate(frame, pose, ear)

            if self.capture.ready() and not self.verification_done:
                self.verify()

        return self.response(face_detected=face_detected)

    def verify(self):
        best_frame = self.capture.frame()

        if best_frame is None:
            raise Exception("No capture frame available.")

        uploads_dir = self._uploads_dir()
        os.makedirs(uploads_dir, exist_ok=True)
        self.capture_path = os.path.join(
            uploads_dir, f"live_{datetime.now():%Y%m%d_%H%M%S}.png"
        )
        cv2.imwrite(self.capture_path, best_frame)

        aadhaar_face = cv2.imread(self.aadhaar_path)
        if aadhaar_face is None:
            raise Exception("Unable to read Aadhaar image.")

        self.verification_result = self.verification_agent.verify(
            aadhaar_face, best_frame
        )
        self.verification_result["spoof_detected"] = False

        print(self.verification_result)

        self.verification_done = True

        duration = time.time() - self.start_time
        summary = self.spoof_summary()
        save_verification_record(
            source="liveness_session",
            decision=self.verification_result.get("decision", "fail"),
            similarity=self.verification_result.get("similarity"),
            threshold=self.verification_result.get("threshold"),
            confidence=self.verification_result.get("confidence"),
            duration_seconds=round(duration, 2),
            challenge_timings=json.dumps(self.challenge_timings),
            **summary,
        )

    def response(self, face_detected=True):
        return {
            "finished": self.verification_done,
            "face_detected": face_detected,
            "challenge": self.challenge.message(),
            "challenge_index": self.challenge.index + 1,
            "challenge_total": len(self.challenge.challenges),
            "progress": min(
                100,
                int(self.capture.frames * 100 / self.capture.required_frames),
            ),
            "verification": self.verification_result,
            "capture": self.capture_path,
            "debug": {
                "direction": self.last_pose["direction"] if self.last_pose else None,
                "yaw": self.last_pose.get("yaw") if self.last_pose else None,
                "pitch": self.last_pose.get("pitch") if self.last_pose else None,
                "ear": self.last_ear,
            },
        }