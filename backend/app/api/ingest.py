# backend/app/api/ingest.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict

from app.services import transcript as transcript_service

router = APIRouter()


class IngestRequest(BaseModel):
    youtube_url: Optional[str] = Field(None)
    transcript_text: Optional[str] = Field(None)
    title: Optional[str] = Field(None)
    video_id: Optional[str] = Field(None)
    try_languages: Optional[List[str]] = Field(None)
    # optional cookies path for restricted videos
    cookies_path: Optional[str] = Field(None)


@router.post("/ingest")
async def ingest_endpoint(payload: IngestRequest):
    body = payload.dict()
    youtube_url = body.get("youtube_url")
    transcript_text = body.get("transcript_text")
    try_languages = body.get("try_languages")
    cookies_path = body.get("cookies_path", None)

    # If youtube_url provided -> attempt caption ingestion (or return existing)
    if youtube_url:
        try:
            result: Dict[str, Any] = transcript_service.ingest_youtube_transcript(
                youtube_url,
                try_languages=try_languages,
                title_lookup=True,
                cookies_path=cookies_path,
            )
            return result
        except Exception as e:
            # Return a 500 with the service error message
            raise HTTPException(status_code=500, detail=str(e))

    # If transcript text pasted manually -> save it as a new doc
    if transcript_text:
        try:
            doc_id = transcript_service.save_manual_transcript(
                transcript_text, title=payload.title, video_id=payload.video_id
            )
            # load json to return consistent schema
            data = transcript_service._read_transcript_json_if_exists(doc_id)
            return {
                "status": "ingested",
                "doc_id": doc_id,
                "file_path": data and data.get("__file_path__"),
                "video_id": payload.video_id,
                "message": "Saved pasted transcript.",
                "metadata": data.get("metadata", {}) if data else {},
                "transcript": data.get("transcript", []) if data else [],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=400, detail="Request must include youtube_url OR transcript_text")


class ASRRequest(BaseModel):
    doc_id: str
    video_id: Optional[str] = None
    cookies_path: Optional[str] = None


@router.post("/ingest/asr")
async def ingest_asr_endpoint(payload: ASRRequest):
    try:
        res = transcript_service.run_asr_for_doc(
            doc_id=payload.doc_id, video_id=payload.video_id, cookies_path=payload.cookies_path
        )
        return res
    except transcript_service.TranscriptError as te:
        # Return informative 400 or 500 depending on message
        raise HTTPException(status_code=500, detail=str(te))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
