import cv2


class OverlayService:

    @staticmethod
    def draw(frame, data):

        h, w = frame.shape[:2]

        # ==========================
        # Background Panel
        # ==========================

        overlay = frame.copy()

        cv2.rectangle(
            overlay,
            (10, 10),
            (430, 330),
            (40, 40, 40),
            -1
        )

        frame = cv2.addWeighted(
            overlay,
            0.55,
            frame,
            0.45,
            0
        )

        # ==========================
        # Header
        # ==========================

        cv2.putText(
            frame,
            "AI KYC LIVENESS SDK",
            (25, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.line(
            frame,
            (20, 55),
            (420, 55),
            (100, 100, 100),
            2
        )

        cv2.putText(
            frame,
            "Face",
            (25,90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2
        )

        cv2.putText(
            frame,
            "Detected",
            (250,90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0,255,0),
            2
        )

        cv2.putText(
            frame,
            "Liveness",
            (25,120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2
        )

        cv2.putText(
            frame,
            data["liveness"],
            (250,120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0,255,255),
            2
        )

        cv2.putText(
            frame,
            "Anti Spoof",
            (25,150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2
        )

        cv2.putText(
            frame,
            "Enabled",
            (250,150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0,255,0),
            2
        )

        cv2.line(
            frame,
            (20,170),
            (420,170),
            (100,100,100),
            2
        )

        cv2.putText(
            frame,
            f"Challenge {data['challenge_index']}/{data['challenge_total']}",
            (25,205),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255,255,255),
            2
        )

        cv2.putText(
            frame,
            data["challenge"],
            (25,235),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0,255,255),
            2
        )

        return frame