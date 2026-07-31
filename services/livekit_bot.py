import asyncio
import queue
import threading
import time
from typing import Optional

import numpy as np
from livekit import rtc
from services import livekit_client

class LiveKitCallBot:

    def __init__(self, livekit_url: str, bot_token: str, customer_identity: str):
        self.livekit_url = livekit_url
        self.bot_token = bot_token
        self.customer_identity = customer_identity
        
        self.frame_queue: "queue.Queue[tuple[float, np.ndarray]]" = queue.Queue(maxsize=50)
        self._joined_event = threading.Event()
        self._join_error: Optional[str] = None
        self._egress_id: Optional[str] = None

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._room: Optional[rtc.Room] = None
        self._stop_flag = threading.Event()

        self._last_sample_at = 0.0
        self._sample_interval = 0.75  # ~1/sec, matches daily_bot.py

    def join(self):
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

    def start_recording(self, room_name: str):
        """Starts a room-composite recording, uploaded directly to S3 by Egress."""
        output_path = f"recordings/{room_name}.mp4"   # S3 key now, not /out/...
        try:
            self._egress_id = livekit_client.start_room_recording(room_name, output_path)
            print(f"[BOT] recording started, egress_id={self._egress_id}, s3_key={output_path}")
        except Exception as exc:
            print(f"[BOT] failed to start recording: {exc}")

    def stop_recording(self):
        if not self._egress_id:
            return
        try:
            livekit_client.stop_room_recording(self._egress_id)
            print(f"[BOT] recording stopped, egress_id={self._egress_id}")
        except Exception as exc:
            print(f"[BOT] failed to stop recording: {exc}")
        finally:
            self._egress_id = None

    def leave(self):
        self._stop_flag.set()
        if self._loop_thread:
            self._loop_thread.join(timeout=5.0)