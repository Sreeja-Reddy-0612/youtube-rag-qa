from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uuid
import os
import json
from datetime import datetime

router = APIRouter()

DATA_DIR = os.path.join(os.getcwd(), "data", "transcripts")
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- Schemas ----------------
class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str

class IngestTranscriptRequest(BaseModel):
    youtube_url: Optional[str] = None
    transcript: List[TranscriptSegment]
    title: Optional[str] = None
    channel: Optional[str] = None


# ---------------- Helpers ----------------
def extract_video_id(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None


# ---------------- Endpoint ----------------
@router.post("/ingest")
def ingest_transcript(payload: IngestTranscriptRequest):

    if not payload.transcript or len(payload.transcript) == 0:
        raise HTTPException(status_code=400, detail="Transcript is required")

    doc_id = str(uuid.uuid4())
    video_id = extract_video_id(payload.youtube_url)

    transcript_segments = []
    for seg in payload.transcript:
        transcript_segments.append({
            "start": float(seg.start),
            "end": float(seg.end),
            "duration": float(seg.end - seg.start),
            "text": seg.text.strip()
        })

    doc = {
        "doc_id": doc_id,
        "source": "youtube+manual" if video_id else "manual_paste",
        "video_id": video_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "metadata": {
            "title": payload.title,
            "channel": payload.channel
        },
        "transcript": transcript_segments
    }

    file_path = os.path.join(DATA_DIR, f"{doc_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    return {
        "status": "ingested",
        "doc_id": doc_id,
        "video_id": video_id,
        "segments": len(transcript_segments),
        "metadata": doc["metadata"]
    }
