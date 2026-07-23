import asyncio
import time
from dataclasses import dataclass

import cv2
import numpy as np

FRAME_SAMPLE_INTERVAL_SEC = 0.75


@dataclass
class SampledFrame:
    room_id: str
    ts: float
    image: np.ndarray


class RoomStreamTap:
    def __init__(self, room_id: str, rtmp_read_url: str):
        self.room_id = room_id
        self.rtmp_read_url = rtmp_read_url
        self._cap: cv2.VideoCapture | None = None
        self._running = False
        self.frame_queue: asyncio.Queue[SampledFrame] = asyncio.Queue(maxsize=50)

    async def start(self):
        self._running = True
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._connect)
        asyncio.create_task(self._sample_loop())

    def _connect(self):
        self._cap = cv2.VideoCapture(self.rtmp_read_url)
        if not self._cap.isOpened():
            raise RuntimeError(f"Could not open RTMP read stream: {self.rtmp_read_url}")

    async def _sample_loop(self):
        loop = asyncio.get_event_loop()
        next_sample_at = time.monotonic()
        while self._running:
            ok, frame = await loop.run_in_executor(None, self._cap.read)
            if not ok:
                await asyncio.sleep(0.1)
                continue
            now = time.monotonic()
            if now >= next_sample_at:
                sampled = SampledFrame(room_id=self.room_id, ts=time.time(), image=frame)
                if self.frame_queue.full():
                    _ = self.frame_queue.get_nowait()
                self.frame_queue.put_nowait(sampled)
                next_sample_at = now + FRAME_SAMPLE_INTERVAL_SEC

    async def stop(self):
        self._running = False
        if self._cap is not None:
            self._cap.release()

# Audio (for Phase 4 later): spawn alongside this, per room --
#   ffmpeg -i <rtmp_read_url> -vn -acodec pcm_s16le -ar 16000 -ac 1 -f s16le pipe:1