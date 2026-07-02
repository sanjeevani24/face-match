import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class LandmarkService:

    def __init__(self):

        base_options = python.BaseOptions(
            model_asset_path="models/face_landmarker.task"
        )

        options = vision.FaceLandmarkerOptions(

            base_options=base_options,

            running_mode=vision.RunningMode.VIDEO,

            num_faces=1,

            output_face_blendshapes=True,

            output_facial_transformation_matrixes=True,

            min_face_detection_confidence=0.5,

            min_tracking_confidence=0.5,

            min_face_presence_confidence=0.5
        )

        self.detector = vision.FaceLandmarker.create_from_options(
            options
        )

    def detect(self, frame, timestamp):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        results = self.detector.detect_for_video(
            mp_image,
            timestamp
        )

        return results