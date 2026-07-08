import cv2
import time
from datetime import datetime

from services.camera_service import CameraService
from services.landmark_service import LandmarkService
from services.drawing_service import DrawingService
from services.blink_service import BlinkService
from services.headpose_service import HeadPoseService
from services.challenge_service import ChallengeService
from services.overlay_service import OverlayService
from agents.verification_agent import VerificationAgent
from services.capture_service import CaptureService

class LivenessAgent:

    def run(self, aadhaar_path, show_ui = True):

        capture = CaptureService()
        camera = CameraService()
        landmark = LandmarkService()
        blink = BlinkService()
        headpose = HeadPoseService()
        challenge = ChallengeService()
        verification_agent = VerificationAgent()

        previous_blink_count = 0
        verification_done = False
        verification_result = None
        filename = None

        while True:

            ret, frame = camera.read()

            if not ret:
                break

            timestamp = int(
                time.time() * 1000
            )

            results = landmark.detect(
                frame,
                timestamp
            )

            if results.face_landmarks:

                face = results.face_landmarks[0]

                pose = headpose.estimate(
                    face,
                    frame
                )

                ear = blink.calculate(face)

                count = blink.update(ear)

                blink_increment = count > previous_blink_count

                previous_blink_count = count

                progress = min(100, int(capture.frames * 100 / capture.required_frames))

                challenge.update(
                    pose["direction"],
                    blink_increment
                )

                if challenge.finished() and not capture.ready():
                    capture.evaluate(frame, pose, ear)

                if capture.ready() and not verification_done:

                    best_frame = capture.frame()

                    filename = f"uploads/live_{datetime.now():%Y%m%d_%H%M%S}.png"
                    cv2.imwrite(filename, best_frame)

                    aadhaar_face = cv2.imread(
                        aadhaar_path
                    )

                    verification_result = verification_agent.verify(
                        aadhaar_face,
                        best_frame
                    )

                    print(verification_result)

                    verification_done = True

                # -----------------------------
                # UI State
                # -----------------------------

                if not challenge.finished():

                    ui_data = {
                        "challenge": challenge.message(),
                        "challenge_index": challenge.index + 1,
                        "challenge_total": len(challenge.challenges),
                        "blink_count": count,
                        "ear": ear,
                        "yaw": pose["yaw"],
                        "pitch": pose["pitch"],
                        "roll": pose["roll"],
                        "direction": pose["direction"],
                        "liveness": "Running",
                        "capture_progress": 0,
                        "verification": None
                    }

                elif not capture.ready():

                    ui_data = {
                        "challenge": "Look straight at the camera",
                        "challenge_index": len(challenge.challenges),
                        "challenge_total": len(challenge.challenges),
                        "blink_count": count,
                        "ear": ear,
                        "yaw": pose["yaw"],
                        "pitch": pose["pitch"],
                        "roll": pose["roll"],
                        "direction": pose["direction"],
                        "liveness": "Verified",
                        "capture_progress": progress,
                        "verification": None
                    }

                else:

                    ui_data = {
                        "challenge": "Verification Complete",
                        "challenge_index": len(challenge.challenges),
                        "challenge_total": len(challenge.challenges),
                        "blink_count": count,
                        "ear": ear,
                        "yaw": pose["yaw"],
                        "pitch": pose["pitch"],
                        "roll": pose["roll"],
                        "direction": pose["direction"],
                        "liveness": "Verified",
                        "capture_progress": 100,
                        "verification": verification_result
                    }

                frame = DrawingService.draw(
                    frame,
                    results
                )
                
                frame = OverlayService.draw(
                    frame,
                    ui_data
                )

            if show_ui:
                cv2.imshow(
                    "Liveness Detection",
                    frame
                )
            
            if cv2.waitKey(1) == ord("q"):
                break

        camera.release()

        if show_ui:
            cv2.destroyAllWindows()

        return {
            "status": "success",
            "liveness": challenge.finished(),
            "verification": verification_result,
            "capture": filename
        }