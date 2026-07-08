import cv2


class CaptureService:

    def __init__(self):

        self.frames = 0

        self.required_frames = 5

        self.captured = False

        self.best_frame = None

    def evaluate(self, frame, pose, ear):

        yaw_ok = abs(pose["yaw"]) < 20

        pitch_ok = abs(pose["pitch"]) < 30

        eyes_ok = ear > 0.15

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        sharpness = cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()

        sharp_ok = sharpness > 50

        print(
            f"Yaw={pose['yaw']:.1f} | "
            f"Pitch={pose['pitch']:.1f} | "
            f"EAR={ear:.3f} | "
            f"Sharpness={sharpness:.1f}"
        )

        print(
            f"Yaw={yaw_ok} | "
            f"Pitch={pitch_ok} | "
            f"Eyes={eyes_ok} | "
            f"Sharp={sharp_ok}"
        )

        if yaw_ok and pitch_ok and eyes_ok and sharp_ok:

            self.frames += 1

            self.best_frame = frame.copy()

            print(f"✅ Capture Frames : {self.frames}")

        else:

            print("❌ Capture Reset")

            self.frames = 0

        if self.frames >= self.required_frames:
            print("✅ Best live frame captured")
            self.captured = True

    def ready(self):
        return self.captured
        
    def frame(self):
        return self.best_frame