from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.query_service import answer_query_for_doc

router = APIRouter()

class QueryRequest(BaseModel):
    doc_id: str
    question: str

@router.post("/query")
def query_doc(payload: QueryRequest):
    try:
        return answer_query_for_doc(payload.doc_id, payload.question)
    except Exception as e:
        print("QUERY ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))
