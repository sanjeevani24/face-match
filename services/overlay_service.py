import cv2

class OverlayService:

    @staticmethod
    def draw(frame, data):

        overlay = frame.copy()

        # =============================
        # Background Panel
        # =============================

        cv2.rectangle(
            overlay,
            (10, 10),
            (430, 520),
            (35, 35, 35),
            -1
        )

        frame = cv2.addWeighted(
            overlay,
            0.60,
            frame,
            0.40,
            0
        )

        # =============================
        # Header
        # =============================

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
            (120, 120, 120),
            2
        )

        # =============================
        # Status Section
        # =============================

        status = [

            ("Face", "Detected", (0,255,0)),

            ("Liveness", data["liveness"], (0,255,255)),

            ("Anti Spoof", "Enabled", (0,255,0))

        ]

        y = 90

        for title, value, color in status:

            cv2.putText(
                frame,
                title,
                (25, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.60,
                (255,255,255),
                2
            )

            cv2.putText(
                frame,
                value,
                (250, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.60,
                color,
                2
            )

            y += 30

        cv2.line(
            frame,
            (20,170),
            (420,170),
            (120,120,120),
            2
        )

        # =============================
        # Challenge
        # =============================

        cv2.putText(
            frame,
            f"Challenge {data['challenge_index']} / {data['challenge_total']}",
            (25,205),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255,255,255),
            2
        )

        cv2.putText(
            frame,
            data["challenge"],
            (25,240),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0,255,255),
            2
        )

        # =============================
        # Pose
        # =============================

        cv2.putText(
            frame,
            f"Yaw   : {data['yaw']:.1f}",
            (25,280),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (255,255,255),
            2
        )

        cv2.putText(
            frame,
            f"Pitch : {data['pitch']:.1f}",
            (160,280),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (255,255,255),
            2
        )

        cv2.putText(
            frame,
            f"Roll : {data['roll']:.1f}",
            (310,280),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (255,255,255),
            2
        )

        # =============================
        # Blink
        # =============================

        cv2.putText(
            frame,
            f"Blink Count : {data['blink_count']}",
            (25,315),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (255,255,255),
            2
        )

        cv2.putText(
            frame,
            f"EAR : {data['ear']:.3f}",
            (250,315),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (255,255,255),
            2
        )

        cv2.line(
            frame,
            (20,335),
            (420,335),
            (120,120,120),
            2
        )

        # =============================
        # Capture Progress
        # =============================

        progress = data["capture_progress"]

        cv2.putText(
            frame,
            "Capture Progress",
            (25,365),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (255,255,255),
            2
        )

        bar_width = 300

        filled = int(bar_width * progress / 100)

        cv2.rectangle(
            frame,
            (25,380),
            (25 + bar_width,405),
            (80,80,80),
            -1
        )

        cv2.rectangle(
            frame,
            (25,380),
            (25 + filled,405),
            (0,255,0),
            -1
        )

        cv2.rectangle(
            frame,
            (25,380),
            (25 + bar_width,405),
            (255,255,255),
            1
        )

        cv2.putText(
            frame,
            f"{progress}%",
            (340,398),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (255,255,255),
            2
        )

        # =============================
        # Verification
        # =============================

        if data["verification"] is not None:

            result = data["verification"]

            color = (
                (0,255,0)
                if result["verified"]
                else (0,0,255)
            )

            cv2.line(
                frame,
                (20,430),
                (420,430),
                (120,120,120),
                2
            )

            cv2.putText(
                frame,
                f"Similarity : {result['similarity']:.3f}",
                (25,460),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2
            )

            cv2.putText(
                frame,
                result["reason"],
                (25,495),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2
            )

        return frame