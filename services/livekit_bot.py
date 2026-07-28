"""
services/livekit_bot.py

Self-hosted LiveKit replacement for services/daily_bot.py. Same job:
join as a silent, non-publishing bot and receive raw video frames
in-process, no RTMP/media server in between.

Architectural difference from daily_bot.py worth knowing: daily-python
is callback-based and can be driven from a plain thread. livekit-python
(the `livekit.rtc` package) is asyncio-native -- Room, VideoStream, and
track events all expect a running event loop. Since the rest of this
FastAPI app is sync (call_session.py's routes are `def`, not `async
def`), this module runs its OWN asyncio event loop on a dedicated
background thread, and bridges out to the same thread-safe
queue.Queue frame_queue that _consume_frames() in call_session.py
already expects -- so call_session.py's consumer loop doesn't change
at all, only how the queue gets filled.

CAVEAT: I've confirmed livekit.rtc exposes VideoStream(track) with
`async for frame_event in stream: ...` and frame_event.frame giving a
VideoFrame with .data/.width/.height, but I have not verified the
exact default pixel format against your installed package version. If
frames look scrambled (green tint, half-image), check
`rtc.VideoBufferType` and pass `format=rtc.VideoBufferType.RGB24`
explicitly to VideoStream() -- see https://docs.livekit.io/reference/python/
and adjust the numpy reshape below to match.

pip install livekit
"""

import asyncio
import queue
import threading
import time
from typing import Optional

import numpy as np
from livekit import rtc


class LiveKitCallBot:
    """One instance per active call room. frame_queue is a plain
    thread-safe queue.Queue -- the asyncio loop below runs on its own
    thread and pushes into it, same shape as DailyCallBot."""

    def __init__(self, livekit_url: str, bot_token: str, customer_identity: str):
        self.livekit_url = livekit_url
        self.bot_token = bot_token
        self.customer_identity = customer_identity

        self.frame_queue: "queue.Queue[tuple[float, np.ndarray]]" = queue.Queue(maxsize=50)
        self._joined_event = threading.Event()
        self._join_error: Optional[str] = None

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._room: Optional[rtc.Room] = None
        self._stop_flag = threading.Event()

        self._last_sample_at = 0.0
        self._sample_interval = 0.75  # ~1/sec, matches daily_bot.py

    def join(self):
        """Starts the background asyncio loop and connects. Mirrors
        DailyCallBot.join()'s fire-and-forget signature -- use
        wait_until_joined() afterward, same as the Daily version."""
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect_and_listen())

    async def _connect_and_listen(self):
        self._room = rtc.Room()

        @self._room.on("track_subscribed")
        def on_track_subscribed(track, publication, participant):
            print(f"[BOT] track_subscribed from participant.identity={participant.identity!r}, expecting={self.customer_identity!r}")   # <-- add this    
            if participant.identity != self.customer_identity:
                return
            if track.kind != rtc.TrackKind.KIND_VIDEO:
                return
            video_stream = rtc.VideoStream(track, format=rtc.VideoBufferType.RGB24)
            asyncio.ensure_future(self._consume_stream(video_stream))

        try:
            await self._room.connect(
                self.livekit_url,
                self.bot_token,
                options=rtc.RoomOptions(auto_subscribe=True),
            )
            self._joined_event.set()
        except Exception as exc:
            self._join_error = str(exc)
            self._joined_event.set()
            return

        # Keep the loop alive (driving room events / the video stream
        # task above) until stop() flips this flag.
        while not self._stop_flag.is_set():
            await asyncio.sleep(0.2)

        await self._room.disconnect()

    async def _consume_stream(self, video_stream: "rtc.VideoStream"):
        print(f"[BOT] subscribed to customer video stream")   # <-- add this
        async for event in video_stream:
            now = time.monotonic()
            if now - self._last_sample_at < self._sample_interval:
                continue
            self._last_sample_at = now

            frame = event.frame
            try:
                rgb = np.frombuffer(frame.data, dtype=np.uint8).reshape(frame.height, frame.width, 3)
            except ValueError as exc:
                print(f"[BOT] frame reshape failed: {exc} (data size={len(frame.data)}, {frame.width}x{frame.height})")
                continue
            bgr = rgb[:, :, ::-1]

            print(f"[BOT] sampled frame {frame.width}x{frame.height}")

            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            self.frame_queue.put_nowait((time.time(), bgr))

    def wait_until_joined(self, timeout: float = 10.0) -> bool:
        ok = self._joined_event.wait(timeout=timeout)
        if self._join_error:
            raise RuntimeError(f"LiveKitCallBot failed to join: {self._join_error}")
        return ok

    def start_recording(self):
        """No-op placeholder -- self-hosted LiveKit recording needs a
        separate Egress service (https://docs.livekit.io/home/egress/overview/),
        which isn't part of the free single-binary --dev setup. Skipping
        it here since call_session.py only uses this for the optional
        enable_recording flag; wire up Egress later if you need it."""
        pass

    def stop_recording(self):
        pass

    def leave(self):
        self._stop_flag.set()
        if self._loop_thread:
            self._loop_thread.join(timeout=5.0)