from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from datetime import datetime, timezone
from models.db import Base


class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Face embedding used in the comparison, JSON-serialized (list of floats)
    embedding = Column(Text, nullable=False)

    similarity = Column(String, nullable=True)
    verification_record_id = Column(Integer, ForeignKey("verification_records.id"), nullable=True)