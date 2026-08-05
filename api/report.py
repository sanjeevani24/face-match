from fastapi import APIRouter, HTTPException, Response
from services.report_generation_service import generate_pdf_report
from models.sentiment import VideoAnalysis
from services.call_session_store import get_call_session

router = APIRouter(prefix="/call/sessions", tags=["report"])


@router.get("/{room_id}/report")
async def get_report_data(room_id: str):
    session = get_call_session(room_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.transcript and not session.sentiment_summary:
        raise HTTPException(status_code=404, detail="Report not ready yet")

    return {
        "room_id": room_id,
        "transcript": session.transcript,
        "sentiment": session.sentiment_summary,
    }


@router.get("/{room_id}/report/pdf")
async def download_report_pdf(room_id: str):
    session = get_call_session(room_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.transcript and not session.sentiment_summary:
        raise HTTPException(status_code=404, detail="Report not ready yet")

    sentiment = (
        VideoAnalysis.model_validate_json(session.sentiment_summary)
        if session.sentiment_summary else None
    )
    pdf_bytes = generate_pdf_report(room_id, session.transcript or "", sentiment)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="kyc_report_{room_id}.pdf"'},
    )