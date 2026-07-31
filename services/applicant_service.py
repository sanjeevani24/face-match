import uuid
import json
from models.db import SessionLocal
from models.applicants import Applicant


def generate_applicant_id():
    return f"APPL-{uuid.uuid4().hex[:10].upper()}"


def save_applicant(embedding, similarity=None, verification_record_id=None):
    applicant_id = generate_applicant_id()

    if hasattr(embedding, "tolist"):
        embedding = embedding.tolist()

    db = SessionLocal()
    try:
        record = Applicant(
            applicant_id=applicant_id,
            embedding=json.dumps(embedding),
            similarity=str(similarity) if similarity is not None else None,
            verification_record_id=verification_record_id,
        )
        db.add(record)
        db.commit()
        return applicant_id
    finally:
        db.close()


def get_applicant_by_id(applicant_id):
    db = SessionLocal()
    try:
        record = db.query(Applicant).filter(Applicant.applicant_id == applicant_id).first()
        if record is None:
            return None
        return {
            "applicant_id": record.applicant_id,
            "created_at": record.created_at.isoformat(),
            "embedding": json.loads(record.embedding),
            "similarity": record.similarity,
            "verification_record_id": record.verification_record_id,
        }
    finally:
        db.close()