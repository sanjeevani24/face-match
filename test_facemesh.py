import cv2
import time

from services.camera_service import CameraService
from services.landmark_service import LandmarkService
from services.drawing_service import DrawingService


camera = CameraService()

landmark = LandmarkService()

printed = False

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