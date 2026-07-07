import cv2
import time

from services.camera_service import CameraService
from services.landmark_service import LandmarkService
from services.drawing_service import DrawingService
from services.blink_service import BlinkService
from services.headpose_service import HeadPoseService
from services.challenge_service import ChallengeService
from services.overlay_service import OverlayService

camera = CameraService()
landmark = LandmarkService()
blink = BlinkService()
headpose = HeadPoseService()
challenge = ChallengeService()

printed = False
previous_blink_count = 0

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

        challenge.update(
            pose["direction"],
            blink_increment
        )

        message = challenge.message()

        ui_data = {

            "challenge": message,
            "challenge_index": challenge.index + 1,
            "challenge_total": len(challenge.challenges),
            "blink_count": count,
            "ear": ear,
            "yaw": pose["yaw"],
            "pitch": pose["pitch"],
            "roll": pose["roll"],
            "direction": pose["direction"],
            "liveness": "Running"
        }

        frame = OverlayService.draw(
            frame,
            ui_data
        )

        # cv2.putText(
        #     frame,
        #     f"Blink Count : {count}",
        #     (20,40),
        #     cv2.FONT_HERSHEY_SIMPLEX,
        #     1,
        #     (0,255,0),
        #     2
        # )

        # cv2.putText(
        #     frame,
        #     f"EAR : {ear:.3f}",
        #     (20,80),
        #     cv2.FONT_HERSHEY_SIMPLEX,
        #     0.8,
        #     (255,0,0),
        #     2
        # )

        # cv2.putText(
        #     frame,
        #     f"Direction : {pose['direction']}",
        #     (20,120),
        #     cv2.FONT_HERSHEY_SIMPLEX,
        #     0.8,
        #     (0,255,255),
        #     2
        # )

        # cv2.putText(
        #     frame,
        #     f"Yaw : {pose['yaw']:.1f}",
        #     (20,160),
        #     cv2.FONT_HERSHEY_SIMPLEX,
        #     0.7,
        #     (0,255,255),
        #     2
        # )

        # cv2.putText(
        #     frame,
        #     f"Pitch : {pose['pitch']:.1f}",
        #     (20,200),
        #     cv2.FONT_HERSHEY_SIMPLEX,
        #     0.7,
        #     (0,255,255),
        #     2
        # )

        # cv2.putText(
        #     frame,
        #     f"Roll : {pose['roll']:.1f}",
        #     (20,240),
        #     cv2.FONT_HERSHEY_SIMPLEX,
        #     0.7,
        #     (0,255,255),
        #     2
        # )
        # cv2.putText(
        #     frame,
        #     message,
        #     (20,300),
        #     cv2.FONT_HERSHEY_SIMPLEX,
        #     0.9,
        #     (255,255,0),
        #     2
        # ) 

    if results.face_landmarks and not printed:

        print("Faces Detected:", len(results.face_landmarks))
        print("Landmarks:", len(results.face_landmarks[0]))

        printed = True

    frame = DrawingService.draw(
        frame,
        results
    )

    cv2.imshow(
        "Liveness Detection",
        frame
    )

    if cv2.waitKey(1) == ord("q"):
        break


camera.release()

cv2.destroyAllWindows()