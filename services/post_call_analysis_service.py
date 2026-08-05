import os
import asyncio
import logging

import boto3
from botocore.exceptions import ClientError

from services.transcription_service import transcribe_recording
from services.sentiment_analysis_service import analyze_recording
from services.call_session_store import save_analysis_results

logger = logging.getLogger(__name__)
s3_check = boto3.client("s3")

async def _wait_for_s3_object(bucket: str, key: str, timeout: float = 60.0, interval: float = 3.0):
    """Egress uploads asynchronously after recording stops — poll until
    the object actually exists (or give up after `timeout` seconds)."""
    elapsed = 0.0
    while elapsed < timeout:
        try:
            await asyncio.to_thread(s3_check.head_object, Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] != "404":
                raise
        await asyncio.sleep(interval)
        elapsed += interval
    return False

async def run_post_call_analysis(room_id: str):
    bucket = os.environ["AWS_S3_BUCKET"]
    key = f"/out/{room_id}.mp4"

    try:
        found = await _wait_for_s3_object(bucket, key)
        if not found:
            logger.error(f"Recording never appeared in S3 for room {room_id}")
            return

        transcript_result = await asyncio.to_thread(transcribe_recording, room_id)
        transcript_text = transcript_result["text"]

        try:
            sentiment = await analyze_recording(bucket, key)
            sentiment_json = sentiment.model_dump_json()
        except Exception:
            logger.error(f"Sentiment analysis failed for room {room_id}, saving transcript only", exc_info=True)
            sentiment_json = None

        save_analysis_results(room_id, transcript_text, sentiment_json)
        logger.info(f"Post-call analysis saved for room {room_id}")

    except Exception:
        logger.error(f"Post-call analysis failed for room {room_id}", exc_info=True)