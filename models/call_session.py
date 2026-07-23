from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime, timezone
from models.db import Base


class CallSession(Base):

    __tablename__ = "call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, unique=True, index=True, nullable=False)
    applicant_id = Column(String, index=True, nullable=False)

    # NOTE: storing raw JWTs is convenient for a prototype/college project
    # but is a real secret at rest. Before this goes anywhere near
    # production, store only customer_jti (already here, used for the
    # single-use check) and regenerate tokens on demand instead of
    # persisting officer_token/customer_token verbatim.
    officer_token = Column(String, nullable=False)
    customer_token = Column(String, nullable=False)
    customer_jti = Column(String, nullable=False)
    customer_link_used = Column(Boolean, default=False, nullable=False)

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