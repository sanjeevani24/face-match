from pydantic import BaseModel
from typing import Literal

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