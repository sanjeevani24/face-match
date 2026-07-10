from models.db import SessionLocal
from models.verification_record import VerificationRecord


def save_verification_record(
    source: str,
    decision: str,
    similarity: float | None = None,
    threshold: float | None = None,
    confidence: str | None = None,
    duration_seconds: float | None = None,
    error_message: str | None = None,
    spoof_checks_count: int | None = None,
    spoof_live_ratio: float | None = None,
    spoof_min_confidence: float | None = None,
    spoof_max_confidence: float | None = None,
    challenge_timings: str | None = None,
):
    db = SessionLocal()
    try:
        record = VerificationRecord(
            source=source,
            decision=decision,
            similarity=similarity,
            threshold=threshold,
            confidence=confidence,
            duration_seconds=duration_seconds,
            error_message=error_message,
            spoof_checks_count=spoof_checks_count,
            spoof_live_ratio=spoof_live_ratio,
            spoof_min_confidence=spoof_min_confidence,
            spoof_max_confidence=spoof_max_confidence,
            challenge_timings=challenge_timings,
        )
        db.add(record)
        db.commit()
    finally:
        db.close()