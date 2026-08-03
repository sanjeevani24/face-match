import os
import tempfile
import subprocess
import boto3
from faster_whisper import WhisperModel

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def _download_from_s3(bucket: str, key: str, dest_path: str):
    s3 = boto3.client(
        "s3",
        region_name=os.environ["AWS_S3_REGION"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )
    s3.download_file(bucket, key, dest_path)


def _extract_audio(video_path: str, audio_path: str):
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000", audio_path],
        check=True,
        capture_output=True,
    )


def transcribe_recording(room_id: str) -> dict:
    bucket = os.environ["AWS_S3_BUCKET"]
    s3_key = f"/out/{room_id}.mp4" 

    with tempfile.TemporaryDirectory() as tmp:
        video_path = os.path.join(tmp, "recording.mp4")
        audio_path = os.path.join(tmp, "audio.wav")

        _download_from_s3(bucket, s3_key, video_path)
        _extract_audio(video_path, audio_path)

        model = _get_model()
        segments_iter, info = model.transcribe(audio_path, language="en")  # drop language= to auto-detect

        segments = []
        full_text_parts = []
        for seg in segments_iter:
            segments.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()})
            full_text_parts.append(seg.text.strip())

        return {"text": " ".join(full_text_parts), "segments": segments, "language": info.language}