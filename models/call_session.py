from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone
from models.db import Base


class CallSession(Base):
    """
    Persisted session metadata (Phase 2/3), Daily-based.

    Unlike the 100ms version, we do NOT persist a customer meeting
    token here -- Daily's tokens aren't decoded for our gating logic
    (see services/daily_client.py's note on why), so there's nothing
    to check against a stored JWT. Instead customer_link_token is OUR
    OWN random secret, checked and marked used entirely server-side;
    the actual Daily meeting token is minted fresh, lazily, only once
    that check passes (see api/call_session.py's /join route).

    Runtime objects for an ACTIVE call (the DailyCallBot, its frame
    queue, the consumer thread) live in api/call_session.py's in-memory
    registry, not here -- same reasoning as before: they can't be
    serialized, and a restart drops an in-progress call regardless.
    """

    __tablename__ = "call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, unique=True, index=True, nullable=False)  # Daily room "name"
    room_url = Column(String, nullable=False)  # Daily room "url", needed to join via daily-python
    applicant_id = Column(String, index=True, nullable=False)

    officer_meeting_token = Column(String, nullable=False)  # fine to persist, officer-only, short-lived
    customer_link_token = Column(String, nullable=False)  # OUR secret, not a Daily token
    customer_link_used = Column(Boolean, default=False, nullable=False)
    customer_link_used_at = Column(DateTime, nullable=True)

    aadhaar_path = Column(String, nullable=False)

    status = Column(String, default="created", nullable=False)  # created -> started -> stopped
    recording_started = Column(Boolean, default=False, nullable=False)
    tap_started = Column(Boolean, default=False, nullable=False)

    identity_flagged = Column(Boolean, default=False, nullable=False)
    spoof_flagged = Column(Boolean, default=False, nullable=False)
    final_decision = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)