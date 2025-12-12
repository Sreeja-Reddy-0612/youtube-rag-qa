# backend/app/services/query_service.py
"""
Query service with lazy-loading of heavy ML libs.

- Does NOT import sentence-transformers / torch at module import time.
- Loads embedding model lazily inside _get_embedding_model().
- Falls back to a fast TF-IDF embedding (scikit-learn) if sentence-transformers is unavailable.
- Exposes answer_query_for_doc(doc_id, youtube_url, question, top_k).
"""

import os
import json
import shutil
from typing import Optional, List, Dict, Any
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/
DATA_DIR = os.getenv("DATA_DIR", os.path.join(ROOT, "data"))
TRANSCRIPTS_DIR = os.path.join(DATA_DIR, "transcripts")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
# OpenAI import only when needed
openai = None
if OPENAI_API_KEY:
    try:
        import openai as _openai
        _openai.api_key = OPENAI_API_KEY
        openai = _openai
    except Exception:
        openai = None

# ---- Lazy model state ----
_EMBED_MODEL = None
_EMBED_METHOD = None  # "sbert" or "tfidf"
_TFIDF_VECT = None

def _read_transcript_by_doc_id(doc_id: str) -> Dict[str, Any]:
    path = os.path.join(TRANSCRIPTS_DIR, f"{doc_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"No transcript JSON found for doc_id {doc_id}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _normalize_transcript_field(raw_transcript: Any) -> List[Dict[str, Any]]:
    segments = []
    if raw_transcript is None:
        return []
    if isinstance(raw_transcript, str):
        segments.append({"start": 0.0, "end": 0.0, "duration": 0.0, "text": raw_transcript})
        return segments
    if isinstance(raw_transcript, list):
        for item in raw_transcript:
            if item is None:
                continue
            if isinstance(item, str):
                segments.append({"start": 0.0, "end": 0.0, "duration": 0.0, "text": item})
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content") or item.get("segment_text") or ""
                try:
                    start = float(item.get("start", 0.0) or 0.0)
                except Exception:
                    start = 0.0
                try:
                    end = float(item.get("end", start + (item.get("duration") or 0.0)) or 0.0)
                except Exception:
                    end = start + (float(item.get("duration", 0.0) or 0.0))
                duration = float(item.get("duration", end - start if end and start else 0.0) or (end - start if end else 0.0))
                segments.append({"start": start, "end": end, "duration": duration, "text": text})
            else:
                segments.append({"start": 0.0, "end": 0.0, "duration": 0.0, "text": str(item)})
        return segments
    return [{"start": 0.0, "end": 0.0, "duration": 0.0, "text": str(raw_transcript)}]

# ---- Embedding utilities with lazy imports and TF-IDF fallback ----
def _get_embedding_model():
    """
    Lazy-load an SBERT model if available; if not, use TF-IDF fallback.
    This function ensures imports happen only when needed.
    """
    global _EMBED_MODEL, _EMBED_METHOD, _TFIDF_VECT
    if _EMBED_MODEL is not None:
        return _EMBED_MODEL, _EMBED_METHOD

    # Try to load sentence-transformers (may import torch -> heavy)
    try:
        # Import inside try to avoid module-level import costs
        from sentence_transformers import SentenceTransformer  # type: ignore
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        _EMBED_MODEL = model
        _EMBED_METHOD = "sbert"
        return _EMBED_MODEL, _EMBED_METHOD
    except Exception as e:
        # Sentence-transformers not available or failed -> fallback to TF-IDF
        try:
            # lightweight sklearn import
            from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
            _TFIDF_VECT = TfidfVectorizer(max_features=768, stop_words="english")
            _EMBED_MODEL = _TFIDF_VECT
            _EMBED_METHOD = "tfidf"
            return _EMBED_MODEL, _EMBED_METHOD
        except Exception as e2:
            # both failed -> raise explanatory error
            raise RuntimeError(
                "No embedding backend available. Install 'sentence-transformers' (and torch) "
                "for semantic embeddings or 'scikit-learn' for TF-IDF fallback."
            )

def _compute_embeddings_for_texts(texts: List[str]):
    """
    Compute embeddings for a list of texts.
    Uses SBERT if available else TF-IDF fallback.
    """
    model, method = _get_embedding_model()
    if method == "sbert":
        # SentenceTransformers model.encode returns numpy arrays
        embs = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embs
    elif method == "tfidf":
        # fit_transform returns sparse matrix; convert to dense
        X = model.fit_transform(texts)
        return X.toarray()
    else:
        raise RuntimeError("Unknown embedding method")

import numpy as np
from numpy.linalg import norm

def _cosine_sim(a: np.ndarray, b: np.ndarray):
    na = norm(a)
    nb = norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))

def _rank_segments_by_similarity(segments: List[Dict[str, Any]], seg_embs: np.ndarray, query_emb: np.ndarray, top_k: int):
    scores = []
    for i, emb in enumerate(seg_embs):
        score = _cosine_sim(np.asarray(emb), np.asarray(query_emb))
        scores.append((i, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    top = scores[:top_k]
    results = []
    for idx, score in top:
        s = segments[idx]
        results.append({"index": idx, "score": float(score), "start": s.get("start",0.0), "end": s.get("end",0.0), "text": s.get("text","")})
    return results

# OpenAI summarization helper (only if openai configured)
def _synthesize_answer_with_openai(question: str, top_segments: List[Dict[str, Any]]):
    if not openai:
        raise RuntimeError("OpenAI not configured.")
    context = "\n\n".join([f"[{int(seg.get('start',0))}s - {int(seg.get('end',0))}s] {seg.get('text','')}" for seg in top_segments])
    prompt = (
        "You are a helpful assistant. Use the following transcript snippets to answer the question.\n\n"
        f"Transcript snippets:\n{context}\n\nQuestion: {question}\n\nAnswer (concise, cite short timestamps like [12s]):"
    )
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"system","content":"You are a helpful assistant."},{"role":"user","content":prompt}],
        temperature=0.0,
        max_tokens=500,
        n=1,
    )
    return resp["choices"][0]["message"]["content"].strip()

# ---- Public entrypoint ----
def answer_query_for_doc(doc_id: Optional[str], youtube_url: Optional[str], question: str, top_k:int = 5) -> Dict[str, Any]:
    # Load doc JSON
    data = None
    if doc_id:
        data = _read_transcript_by_doc_id(doc_id)
    else:
        if not youtube_url:
            raise ValueError("youtube_url required when doc_id not provided")
        vid = youtube_url.split("v=")[-1].split("&")[0] if "v=" in youtube_url else youtube_url.split("youtu.be/")[-1].split("?")[0]
        found = None
        for fname in os.listdir(TRANSCRIPTS_DIR):
            if not fname.endswith(".json"):
                continue
            try:
                with open(os.path.join(TRANSCRIPTS_DIR, fname), "r", encoding="utf-8") as fh:
                    j = json.load(fh)
                    if j.get("video_id") == vid:
                        found = j
                        break
            except Exception:
                continue
        if found is None:
            raise FileNotFoundError(f"No transcript found for video id {vid}. Ingest first or paste transcript.")
        data = found

    raw_transcript = data.get("transcript", []) if isinstance(data, dict) else []
    segments = _normalize_transcript_field(raw_transcript)
    if not segments:
        raise ValueError("Transcript is empty for this document. Paste transcript or run ASR first.")

    texts = [seg.get("text","")[:2000] for seg in segments]

    # Compute embeddings (lazy)
    try:
        seg_embs = _compute_embeddings_for_texts(texts)
    except Exception as e:
        raise RuntimeError(f"Failed to compute embeddings: {e}")

    # Embed query (use same model)
    try:
        model, method = _get_embedding_model()
        if method == "sbert":
            q_emb = model.encode([question], convert_to_numpy=True)[0]
        elif method == "tfidf":
            # for TF-IDF fallback we must vectorize query in same vectorizer space
            q_emb = model.transform([question]).toarray()[0]
        else:
            raise RuntimeError("Unknown embedding method")
    except Exception as e:
        raise RuntimeError(f"Failed to embed query: {e}")

    # Rank
    top_matches = _rank_segments_by_similarity(segments, seg_embs, q_emb, top_k=top_k)
    top_segments = [{"index": m["index"], "score": m["score"], "start": m["start"], "end": m["end"], "text": m["text"]} for m in top_matches]

    # Build answer
    final_answer = None
    if openai:
        try:
            final_answer = _synthesize_answer_with_openai(question, top_segments)
        except Exception:
            final_answer = " ".join([seg["text"] for seg in top_segments])
    else:
        final_answer = " ".join([seg["text"] for seg in top_segments])

    return {
        "status": "ok",
        "doc_id": data.get("doc_id"),
        "video_id": data.get("video_id"),
        "question": question,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "answer": final_answer,
        "top_segments": top_segments,
    }
