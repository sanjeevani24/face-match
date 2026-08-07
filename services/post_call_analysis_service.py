import os
import asyncio
import logging

import boto3
from botocore.exceptions import ClientError

from services.transcription_service import transcribe_recording
from services.sentiment_analysis_service import analyze_recording
from services.call_session_store import save_analysis_results

logger = logging.getLogger(__name__)


def _get_s3_client():
    return boto3.client(
        "s3",
        region_name=os.environ.get("AWS_S3_REGION"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )


async def _wait_for_s3_object(bucket: str, key: str, timeout: float = 60.0, interval: float = 3.0):
    """Egress uploads asynchronously after recording stops — poll until
    the object actually exists (or give up after `timeout` seconds)."""
    elapsed = 0.0
    s3_check = _get_s3_client()
    while elapsed < timeout:
        try:
            await asyncio.to_thread(s3_check.head_object, Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") != "404":
                logger.error(f"S3 head_object error checking {key}: {e}", exc_info=True)
                raise
        except Exception as e:
            logger.error(f"Unexpected error checking S3 object {key}: {e}", exc_info=True)
        await asyncio.sleep(interval)
        elapsed += interval
    return False


async def run_post_call_analysis(room_id: str):
    bucket = os.environ.get("AWS_S3_BUCKET")
    if not bucket:
        logger.error(f"AWS_S3_BUCKET is not set. Cannot run post-call analysis for room {room_id}")
        return

    key = f"recordings/{room_id}.mp4"

    try:
        logger.info(f"Starting post-call analysis for room {room_id}, checking S3 key {key} in bucket {bucket}...")
        found = await _wait_for_s3_object(bucket, key)
        if not found:
            logger.error(f"Recording file s3://{bucket}/{key} never appeared in S3 for room {room_id}")
            return

        logger.info(f"Recording found in S3. Starting transcription for room {room_id}...")
        transcript_result = await asyncio.to_thread(transcribe_recording, room_id)
        transcript_text = transcript_result["text"]

        try:
            sentiment = await analyze_recording(bucket, key)
            sentiment_json = sentiment.model_dump_json()
        except Exception:
            logger.error(f"Sentiment analysis failed for room {room_id}, saving transcript only", exc_info=True)
            sentiment_json = None

        save_analysis_results(room_id, transcript_text, sentiment_json)
        logger.info(f"Post-call analysis successfully saved for room {room_id}")

    except Exception:
        logger.error(f"Post-call analysis failed for room {room_id}", exc_info=True)