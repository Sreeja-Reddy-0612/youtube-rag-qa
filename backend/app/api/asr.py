"""
backend/app/api/asr.py

POST /ingest/asr
- body: { "doc_id": "...", "video_id": "..." }  (you can send either)
- If doc_id provided -> read doc to get video_id
- Runs ASR (using services.asr.run_asr_for_video) and returns result
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import os
from backend.app.services import asr as asr_service

router = APIRouter()

class ASRRequest(BaseModel):
    doc_id: Optional[str] = Field(None)
    video_id: Optional[str] = Field(None)

@router.post("/ingest/asr")
async def ingest_asr(payload: ASRRequest):
    vid = payload.video_id
    # If doc_id given, try to read its video_id
    if payload.doc_id and not vid:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "transcripts", f"{payload.doc_id}.json")
        path = os.path.normpath(path)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="doc_id not found")
        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                j = json.load(f)
                vid = j.get("video_id")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not read doc: {e}")

    if not vid:
        raise HTTPException(status_code=400, detail="video_id or doc_id required")

    try:
        result = asr_service.run_asr_for_video(vid)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
