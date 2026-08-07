import boto3
import tempfile
import os
import time
import logging
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Literal

logger = logging.getLogger(__name__)

def _get_s3_client():
    return boto3.client(
        "s3",
        region_name=os.environ.get("AWS_S3_REGION"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )


def _get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not configured")
    return genai.Client(api_key=api_key)


class KeyMoment(BaseModel):
    approx_timestamp: str
    observation: str

class VideoAnalysis(BaseModel):
    overall_sentiment: Literal["calm", "nervous", "distressed", "neutral", "positive"]
    sentiment_score: float
    facial_expression_summary: str
    engagement_level: Literal["low", "medium", "high"]
    stress_indicators: list[str]
    key_moments: list[KeyMoment]
    inferred_intention: str
    deception_risk_flag: bool
    confidence: float


PROMPT = """You are analyzing a recorded identity-verification video call.
Watch the full video and assess the applicant's overall emotional state,
facial expressions over time, engagement level, and any behavioral cues
relevant to fraud risk (nervousness, mismatched affect, apparent coaching,
unnatural pauses before identity questions). Be conservative — only set
deception_risk_flag=true on strong, specific signals, not generic nervousness.
Note timestamps for anything notable. Return JSON matching the schema only."""


async def analyze_recording(bucket: str, key: str) -> VideoAnalysis:
    tmp_path = None
    uploaded = None
    s3_client = _get_s3_client()
    gemini_client = _get_gemini_client()

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name
        s3_client.download_file(bucket, key, tmp_path)

        uploaded = gemini_client.files.upload(file=tmp_path)
        while uploaded.state.name == "PROCESSING":
            time.sleep(2)
            uploaded = gemini_client.files.get(name=uploaded.name)

        if uploaded.state.name == "FAILED":
            raise RuntimeError(f"Gemini file processing failed for {key}")

        models_to_try = [
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
        ]
        response = None
        last_err = None
        for m in models_to_try:
            try:
                response = gemini_client.models.generate_content(
                    model=m,
                    contents=[uploaded, PROMPT],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=VideoAnalysis,
                        temperature=0.2,
                    ),
                )
                logger.info(f"Successfully generated sentiment analysis using model {m}")
                break
            except Exception as e:
                logger.warning(f"Gemini model {m} failed: {e}. Trying fallback...")
                last_err = e

        if response is None:
            raise RuntimeError(f"All Gemini models failed: {last_err}")

        return VideoAnalysis.model_validate_json(response.text)

    finally:
        if uploaded is not None:
            try:
                gemini_client.files.delete(name=uploaded.name)
            except Exception:
                logger.warning(f"Failed to delete Gemini file for {key}", exc_info=True)
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)