import os
import logging
import tempfile
import subprocess
import boto3
from faster_whisper import WhisperModel

import shutil

logger = logging.getLogger(__name__)
_model = None

def _get_model():
    global _model
    if _model is None:
        logger.info("Initializing Faster-Whisper base model...")
        data_dir = os.environ.get("DATA_DIR", "./data")
        cache_dir = os.path.abspath(os.path.join(data_dir, ".cache"))
        os.makedirs(cache_dir, exist_ok=True)
        os.environ["HF_HOME"] = cache_dir
        _model = WhisperModel("base", device="cpu", compute_type="int8", download_root=cache_dir)
    return _model


def _download_from_s3(bucket: str, key: str, dest_path: str):
    s3 = boto3.client(
        "s3",
        region_name=os.environ.get("AWS_S3_REGION"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )
    s3.download_file(bucket, key, dest_path)


def _extract_audio(video_path: str, audio_path: str):
    ffmpeg_bin = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
    res = subprocess.run(
        [ffmpeg_bin, "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000", audio_path],
        check=True,
        capture_output=True,
    )


def transcribe_recording(room_id: str) -> dict:
    bucket = os.environ.get("AWS_S3_BUCKET")
    if not bucket:
        raise ValueError("AWS_S3_BUCKET environment variable is not configured")

    s3_key = f"recordings/{room_id}.mp4"

    with tempfile.TemporaryDirectory() as tmp:
        video_path = os.path.join(tmp, "recording.mp4")
        audio_path = os.path.join(tmp, "audio.wav")

        logger.info(f"Downloading s3://{bucket}/{s3_key} to {video_path}...")
        try:
            _download_from_s3(bucket, s3_key, video_path)
        except Exception as exc:
            logger.error(f"Failed to download recording s3://{bucket}/{s3_key}: {exc}", exc_info=True)
            raise RuntimeError(f"S3 download failed for s3://{bucket}/{s3_key}: {exc}") from exc

        logger.info(f"Extracting audio using ffmpeg from {video_path} to {audio_path}...")
        try:
            _extract_audio(video_path, audio_path)
        except subprocess.CalledProcessError as cpe:
            stderr = cpe.stderr.decode("utf-8", errors="ignore") if cpe.stderr else str(cpe)
            logger.error(f"FFmpeg audio extraction failed: {stderr}", exc_info=True)
            raise RuntimeError(f"FFmpeg failed to extract audio: {stderr}") from cpe

        logger.info(f"Running speech-to-text transcription on {audio_path}...")
        model = _get_model()
        segments_iter, info = model.transcribe(audio_path, language="en")

        segments = []
        full_text_parts = []
        for seg in segments_iter:
            segments.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()})
            full_text_parts.append(seg.text.strip())

        full_text = " ".join(full_text_parts)
        logger.info(f"Transcription completed for room {room_id}: '{full_text[:80]}...'")
        return {"text": full_text, "segments": segments, "language": info.language}