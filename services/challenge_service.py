from models.challenge import Challenge
import random


class ChallengeService:

    def __init__(self):

        self.challenges = [
            Challenge("LEFT", "Turn your head left", hold_frames=10),
            Challenge("RIGHT", "Turn your head right", hold_frames=10),
            Challenge("UP", "Look up", hold_frames=10 ),
            Challenge("BLINK", "Blink once", hold_frames=1)
        ]

        random.shuffle(self.challenges)

        self.index =0
        self.success_frames = 0

    def current(self):

        if self.index >= len(self.challenges):
            return None

        return self.challenges[self.index]

    def finished(self):

        return self.index >= len(self.challenges)
    
    def update(self, direction, blink_increment):

        if self.finished():
            return

        challenge = self.current()
        success = False

        if challenge.name == "LEFT":
            success = direction == "LEFT"

        elif challenge.name == "RIGHT":
            success = direction == "RIGHT"

        elif challenge.name == "UP":
            success = direction == "UP"

        elif challenge.name == "BLINK":
            success = blink_increment

        if success:
            self.success_frames += 1
        else:
            self.success_frames = max(0, self.success_frames - 1)

        print(
            f"Challenge={challenge.name} | "
            f"Direction={direction} | "
            f"Success={success} | "
            f"Frames={self.success_frames}"
        )

        if self.success_frames >= challenge.hold_frames:
            # print(f"✅ {challenge.name} COMPLETED")
            self.index += 1
            self.success_frames = 0
            if self.finished():
                print("🎉 LIVENESS VERIFIED")

    def message(self):
        if self.finished():
            return "LIVENESS VERIFIED"
        return self.current().instruction
    
    