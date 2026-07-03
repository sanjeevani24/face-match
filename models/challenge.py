from dataclasses import dataclass

@dataclass
class Challenge:

    name: str
    instruction: str
    hold_frames: int = 15