# backend/app/api/query.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
import os

from app.services.query_service import answer_query_for_doc

router = APIRouter()

class QueryRequest(BaseModel):
    doc_id: Optional[str] = Field(None, description="Existing doc_id from ingestion")
    youtube_url: Optional[str] = Field(None, description="YouTube URL (optional when doc_id not provided)")
    question: str = Field(..., description="User question")
    top_k: Optional[int] = Field(5, description="How many top segments to retrieve")

@router.post("/query")
async def query_endpoint(payload: QueryRequest):
    # validation: need either doc_id or youtube_url
    body = payload.dict()
    doc_id = body.get("doc_id")
    youtube_url = body.get("youtube_url")
    question = body.get("question")
    top_k = body.get("top_k") or 5

    if not doc_id and not youtube_url:
        raise HTTPException(status_code=400, detail="Either doc_id or youtube_url must be provided.")

    try:
        result = answer_query_for_doc(
            doc_id=doc_id,
            youtube_url=youtube_url,
            question=question,
            top_k=int(top_k),
        )
        return result
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # catch-all: show helpful message
        raise HTTPException(status_code=500, detail=str(e))
