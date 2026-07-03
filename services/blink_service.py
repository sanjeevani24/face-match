from utils.geometry import Geometry


class BlinkService:

    LEFT_EYE = [
        33, 160, 158, 133, 153, 144
    ]

    RIGHT_EYE = [
        362, 385, 387, 263, 373, 380
    ]

    EAR_THRESHOLD = 0.20

    MIN_CLOSED_FRAMES = 3

    COOLDOWN_FRAMES = 5

    def __init__(self):
        self.eye_closed = False
        self.closed_frames = 0
        self.blink_count = 0
        self.cooldown = 0
        self.calibration = []
        self.threshold = None

    @staticmethod
    def eye_aspect_ratio(landmarks, eye):

        p1 = landmarks[eye[0]]
        p2 = landmarks[eye[1]]
        p3 = landmarks[eye[2]]
        p4 = landmarks[eye[3]]
        p5 = landmarks[eye[4]]
        p6 = landmarks[eye[5]]

        vertical1 = Geometry.euclidean(p2, p6)

        vertical2 = Geometry.euclidean(p3, p5)

        horizontal = Geometry.euclidean(p1, p4)

        return (
            vertical1 + vertical2
        ) / (
            2 * horizontal
        )

    def calculate(self, face):

        left = self.eye_aspect_ratio(
            face,
            self.LEFT_EYE
        )

        right = self.eye_aspect_ratio(
            face,
            self.RIGHT_EYE
        )

        ear = (left + right) / 2

        return ear
    
    def update(self, ear):

        if self.threshold is None:

            self.calibration.append(ear)

            if len(self.calibration) >= 30:

                avg = sum(self.calibration) / len(self.calibration)

                self.threshold = avg * 0.65

                print(
                    "Threshold calibrated:",
                    self.threshold
                )

            return self.blink_count

        if self.cooldown > 0:

            self.cooldown -= 1

            return self.blink_count

        if ear < self.threshold:

            self.closed_frames += 1

        else:

            if self.closed_frames >= self.MIN_CLOSED_FRAMES:

                self.blink_count += 1
                self.cooldown = self.COOLDOWN_FRAMES

            self.closed_frames = 0

        return self.blink_count