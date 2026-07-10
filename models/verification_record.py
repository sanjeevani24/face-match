from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
from models.db import Base


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    source = Column(String, nullable=False)
    decision = Column(String, nullable=False)

    similarity = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    confidence = Column(String, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    error_message = Column(String, nullable=True)

    # New: antispoofing summary
    spoof_checks_count = Column(Integer, nullable=True)
    spoof_live_ratio = Column(Float, nullable=True)
    spoof_min_confidence = Column(Float, nullable=True)
    spoof_max_confidence = Column(Float, nullable=True)

    challenge_timings = Column(String, nullable=True)