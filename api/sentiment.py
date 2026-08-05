from fastapi import APIRouter, BackgroundTasks
from services.post_call_analysis_service import run_post_call_analysis


router = APIRouter(prefix="/call/sessions", tags=["analysis"])


@router.post("/{room_id}/analyze")
async def trigger_call_analysis(room_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_post_call_analysis, room_id)
    return {"status": "analysis_started", "room_id": room_id}

