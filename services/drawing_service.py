import cv2


class DrawingService:

    @staticmethod
    def draw(frame, result):

        if not result.face_landmarks:
            return frame

        h, w = frame.shape[:2]

        for landmark in result.face_landmarks[0]:

            x = int(landmark.x * w)
            y = int(landmark.y * h)

            cv2.circle(
                frame,
                (x, y),
                1,
                (0, 255, 0),
                -1
            )

        return frame