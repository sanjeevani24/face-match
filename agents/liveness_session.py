import cv2
import time
from datetime import datetime

from services.landmark_service import LandmarkService
from services.blink_service import BlinkService
from services.headpose_service import HeadPoseService
from services.challenge_service import ChallengeService
from agents.verification_agent import VerificationAgent
from services.capture_service import CaptureService

class LivenessSession:

    def __init__(self, aadhaar_path):
        self.aadhaar_path = aadhaar_path
        self.landmark = LandmarkService()
        self.blink = BlinkService()
        self.headpose = HeadPoseService()
        self.challenge = ChallengeService()
        self.capture = CaptureService()
        self.verification_agent = VerificationAgent()

        self.previous_blink_count = 0
        self.verification_done = False
        self.verification_result = None
        self.capture_path = None

        # debug telemetry, updated every frame
        self.last_pose = None
        self.last_ear = None

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

            # store for telemetry regardless of challenge outcome
            self.last_pose = pose
            self.last_ear = ear

            self.challenge.update(pose["direction"], blink_increment)

            if self.challenge.finished() and not self.capture.ready():
                self.capture.evaluate(frame, pose, ear)

            if self.capture.ready() and not self.verification_done:
                self.verify()

        return self.response(face_detected=face_detected)

    def verify(self):
        
        best_frame = self.capture.frame()
        
        if best_frame is None:
            raise Exception("No capture frame available.")

        self.capture_path = f"uploads/live_{datetime.now():%Y%m%d_%H%M%S}.png"
        cv2.imwrite(self.capture_path, best_frame)

        aadhaar_face = cv2.imread(self.aadhaar_path)
        if aadhaar_face is None:
            raise Exception("Unable to read Aadhaar image.")

        self.verification_result = self.verification_agent.verify(
            aadhaar_face, best_frame
        )
        
        print(self.verification_result)
        
        self.verification_done = True

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
            # debug telemetry — remove once the direction issue is confirmed fixed
            "debug": {
                "direction": self.last_pose["direction"] if self.last_pose else None,
                "yaw": self.last_pose.get("yaw") if self.last_pose else None,
                "pitch": self.last_pose.get("pitch") if self.last_pose else None,
                "ear": self.last_ear,
            },
        }