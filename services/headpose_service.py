import cv2
import numpy as np
from collections import deque

class HeadPoseService:

    def __init__(self):
        self.yaw_history = deque(maxlen=5)
        self.pitch_history = deque(maxlen=5)
        self.roll_history = deque(maxlen=5)
        self.current_direction = "CENTER"  


    LEFT_ENTER = -18
    LEFT_EXIT = -10

    RIGHT_ENTER = 18
    RIGHT_EXIT = 10

    UP_ENTER = 18
    UP_EXIT = -10

    DOWN_ENTER = -18
    DOWN_EXIT = 10

    def normalize_angle(self, angle):

        angle = float(angle)

        # Convert to [-180, 180]
        angle = (angle + 180) % 360 - 180

        # Convert to [-90, 90]
        if angle > 90:
            angle -= 180
        elif angle < -90:
            angle += 180

        return angle

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

        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)

        projection_matrix = np.hstack(
        (
        rotation_matrix,
        translation_vector
        ))

        _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(
        projection_matrix
        )

        pitch = float(euler_angles[0][0])
        yaw = float(euler_angles[1][0])
        roll = float(euler_angles[2][0])

        yaw = self.normalize_angle(yaw)
        pitch = self.normalize_angle(pitch)
        roll = self.normalize_angle(roll)

        self.yaw_history.append(yaw)
        self.pitch_history.append(pitch)
        self.roll_history.append(roll)

        yaw = sum(self.yaw_history) / len(self.yaw_history)
        pitch = sum(self.pitch_history) / len(self.pitch_history)
        roll = sum(self.roll_history) / len(self.roll_history)

        direction = self.current_direction
        
        if direction == "LEFT":
            if yaw > self.LEFT_EXIT:
                direction = "CENTER"
        elif direction == "RIGHT":
            if yaw < self.RIGHT_EXIT:
                direction = "CENTER"
        elif direction == "UP":
            if pitch > self.UP_EXIT:
                direction = "CENTER"
        elif direction == "DOWN":
            if pitch < self.DOWN_EXIT:
                direction = "CENTER"
        else:  # currently CENTER, check for entry
            if yaw < self.LEFT_ENTER:
                direction = "LEFT"
            elif yaw > self.RIGHT_ENTER:
                direction = "RIGHT"
            elif pitch < self.UP_ENTER:
                direction = "UP"
            elif pitch > self.DOWN_ENTER:
                direction = "DOWN"

        print(
            f"Yaw={yaw:.1f}, "
            f"Pitch={pitch:.1f}, "
            f"Roll={roll:.1f}",
            f"Direction={direction}"
        )

        return {
        "yaw": yaw,
        "pitch": pitch,
        "roll": roll,
        "direction": direction
    }