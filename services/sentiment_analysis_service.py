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

s3 = boto3.client("s3")
gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

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

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name
        s3.download_file(bucket, key, tmp_path)

        uploaded = gemini_client.files.upload(file=tmp_path)
        while uploaded.state.name == "PROCESSING":
            time.sleep(2)
            uploaded = gemini_client.files.get(name=uploaded.name)

        if uploaded.state.name == "FAILED":
            raise RuntimeError(f"Gemini file processing failed for {key}")

        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash",
            contents=[uploaded, PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VideoAnalysis,
                temperature=0.2,
            ),
        )
        return VideoAnalysis.model_validate_json(response.text)

    finally:
        if uploaded is not None:
            try:
                gemini_client.files.delete(name=uploaded.name)
            except Exception:
                logger.warning(f"Failed to delete Gemini file for {key}", exc_info=True)
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)