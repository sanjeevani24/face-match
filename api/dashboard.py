from fastapi import APIRouter, HTTPException
from sqlalchemy import func
from models.db import SessionLocal
from models.verification_record import VerificationRecord
from services.applicant_service import get_applicant_by_id

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/stats")
def get_stats():
    db = SessionLocal()
    try:
        total = db.query(func.count(VerificationRecord.id)).scalar() or 0
        passed = db.query(func.count(VerificationRecord.id)).filter(
            VerificationRecord.decision == "pass"
        ).scalar() or 0
        failed = db.query(func.count(VerificationRecord.id)).filter(
            VerificationRecord.decision == "fail"
        ).scalar() or 0
        review = db.query(func.count(VerificationRecord.id)).filter(
            VerificationRecord.decision == "review"
        ).scalar() or 0
        avg_duration = db.query(func.avg(VerificationRecord.duration_seconds)).scalar()

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "review": review,
            "avg_duration_seconds": round(avg_duration, 2) if avg_duration else None,
        }
    finally:
        db.close()


@router.get("/history")
def get_history(limit: int = 50):
    db = SessionLocal()
    try:
        records = (
            db.query(VerificationRecord)
            .order_by(VerificationRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "source": r.source,
                "decision": r.decision,
                "similarity": r.similarity,
                "threshold": r.threshold,
                "confidence": r.confidence,
                "duration_seconds": r.duration_seconds,
            }
            for r in records
        ]
    finally:
        db.close()

@router.get("/logs")
def get_logs(limit: int = 100):
    db = SessionLocal()
    try:
        records = (
            db.query(VerificationRecord)
            .order_by(VerificationRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "source": r.source,
                "decision": r.decision,
                "level": "error" if r.decision == "error" else "info",
                "similarity": r.similarity,
                "threshold": r.threshold,
                "confidence": r.confidence,
                "duration_seconds": r.duration_seconds,
                "error_message": r.error_message,
                "spoof_checks_count": r.spoof_checks_count,
                "spoof_live_ratio": r.spoof_live_ratio,
                "spoof_min_confidence": r.spoof_min_confidence,
                "spoof_max_confidence": r.spoof_max_confidence,
                "challenge_timings": r.challenge_timings,
                "applicant_id": r.applicant_id,
            }
            for r in records
        ]
    finally:
        db.close()


@router.get("/applicants/{applicant_id}")
def get_applicant(applicant_id: str):
    result = get_applicant_by_id(applicant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return result