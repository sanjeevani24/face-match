import cv2
import numpy as np
from collections import deque

class HeadPoseService:

    def __init__(self):
        self.x_history = deque(maxlen=5)
        self.y_history = deque(maxlen=5)
        self.direction = "CENTER"

    LEFT_ENTER = -18
    LEFT_EXIT = -10

    RIGHT_ENTER = 18
    RIGHT_EXIT = 10

    UP_ENTER = -18
    UP_EXIT = -10

    DOWN_ENTER = 18
    DOWN_EXIT = 10

    def estimate(self, face_landmarks, frame):
        h, w = frame.shape[:2]
        image_points = np.array([
            (
                face_landmarks[1].x * w,
                face_landmarks[1].y * h
            ),
            (
                face_landmarks[152].x * w,
                face_landmarks[152].y * h
            ),
            (
                face_landmarks[33].x * w,
                face_landmarks[33].y * h
            ),
            (
                face_landmarks[263].x * w,
                face_landmarks[263].y * h
            ),
            (
                face_landmarks[61].x * w,
                face_landmarks[61].y * h
            ),
            (
                face_landmarks[291].x * w,
                face_landmarks[291].y * h
            )
        ], dtype=np.float64)

        model_points = np.array([
            (0.0, 0.0, 0.0),
            (0.0, -63.6, -12.5),
            (-43.3, 32.7, -26),
            (43.3, 32.7, -26),
            (-28.9, -28.9, -24.1),
            (28.9, -28.9, -24.1)
        ])

        focal_length = w

        camera_matrix = np.array([
            [focal_length, 0, w / 2],
            [0, focal_length, h / 2],
            [0, 0, 1]
        ])

        dist_coeffs = np.zeros((4, 1))

        success, rotation_vector, translation_vector = cv2.solvePnP(
            model_points,
            image_points,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )

        nose_end_point2D, _ = cv2.projectPoints(
            np.array([(0.0, 0.0, 120.0)]),
            rotation_vector,
            translation_vector,
            camera_matrix,
            dist_coeffs
        )

        p1 = (
            int(image_points[0][0]),
            int(image_points[0][1])
        )

        p2 = (
            int(nose_end_point2D[0][0][0]),
            int(nose_end_point2D[0][0][1])
        )

        cv2.line(
            frame,
            p1,
            p2,
            (0,255,255),
            3
        )

        offset_x = p2[0] - p1[0]
        offset_y = p2[1] - p1[1]

        self.x_history.append(offset_x)
        self.y_history.append(offset_y)

        offset_x = sum(self.x_history) / len(self.x_history)
        offset_y = sum(self.y_history) / len(self.y_history)

        direction = "CENTER"

        if abs(offset_x) > abs(offset_y):

            if offset_x < -60:
                direction = "LEFT"

            elif offset_x > 60:
                direction = "RIGHT"

            else:
                direction = "CENTER"

        else:

            if offset_y < -50:
                direction = "UP"

            elif offset_y > 50:
                direction = "DOWN"

            else:
                direction = "CENTER"

        print(
            f"Direction={direction} | X={offset_x} | Y={offset_y}"
        )

        return {
            "nose_x": offset_x,
            "nose_y": offset_y,
            "direction": direction
        }