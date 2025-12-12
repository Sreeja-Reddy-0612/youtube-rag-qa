"""
backend/app/main.py

What it does:
- Creates FastAPI app for the backend.
- Adds CORS so your frontend at http://localhost:5173 can call the API.
- Mounts API router(s) (ingest currently).
- Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Variables you may change:
- ALLOWED_ORIGINS: set to your frontend origin(s) if needed.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.asr import router as asr_router

from app.api.ingest import router as ingest_router
from app.api import query   # <- make sure this exists and is imported

app = FastAPI(title="YouTube RAG QA - Backend (Day 1)")

# Allow local frontend origin(s)
ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(ingest_router, prefix="", tags=["ingest"])
app.include_router(asr_router, prefix="", tags=["asr"])
app.include_router(query.router, prefix="", tags=["query"])


@app.get("/")
async def root():
    return {"status": "ok", "message": "YouTube RAG QA backend is running"}
