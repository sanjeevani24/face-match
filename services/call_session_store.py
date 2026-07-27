from datetime import datetime, timezone

from models.db import SessionLocal
from models.call_session import CallSession


def create_call_session(
    room_id: str,
    room_url: str,
    applicant_id: str,
    officer_meeting_token: str,
    customer_link_token: str,
    aadhaar_path: str,
) -> None:
    db = SessionLocal()
    try:
        db.add(CallSession(
            room_id=room_id,
            room_url=room_url,
            applicant_id=applicant_id,
            officer_meeting_token=officer_meeting_token,
            customer_link_token=customer_link_token,
            aadhaar_path=aadhaar_path,
        ))
        db.commit()
    finally:
        db.close()


def get_call_session(room_id: str) -> CallSession | None:
    db = SessionLocal()
    try:
        return db.query(CallSession).filter(CallSession.room_id == room_id).first()
    finally:
        db.close()


def mark_link_used(room_id: str) -> None:
    db = SessionLocal()
    try:
        session = db.query(CallSession).filter(CallSession.room_id == room_id).first()
        if session:
            session.customer_link_used = True
            db.commit()
    finally:
        db.close()


def mark_started(room_id: str) -> None:
    db = SessionLocal()
    try:
        session = db.query(CallSession).filter(CallSession.room_id == room_id).first()
        if session:
            session.status = "started"
            session.recording_started = True
            session.tap_started = True
            session.started_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def mark_stopped(room_id: str, decision: str, identity_flagged: bool, spoof_flagged: bool) -> None:
    db = SessionLocal()
    try:
        session = db.query(CallSession).filter(CallSession.room_id == room_id).first()
        if session:
            session.status = "stopped"
            session.final_decision = decision
            session.identity_flagged = identity_flagged
            session.spoof_flagged = spoof_flagged
            session.ended_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()