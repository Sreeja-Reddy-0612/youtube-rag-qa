import os
import json
import re
import numpy as np
from typing import List, Dict, Any
from datetime import datetime

from sentence_transformers import SentenceTransformer
from numpy.linalg import norm

# ============================================================
# Paths
# ============================================================
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "transcripts")

# ============================================================
# Lazy-loaded embedding model
# ============================================================
_EMBED_MODEL = None

def get_embed_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBED_MODEL

# ============================================================
# Utils
# ============================================================
def cosine_sim(a, b) -> float:
    if norm(a) == 0 or norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (norm(a) * norm(b)))

def load_doc(doc_id: str) -> Dict[str, Any]:
    path = os.path.join(DATA_DIR, f"{doc_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Document not found: {doc_id}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ============================================================
# Chunking
# ============================================================
def chunk_text(text: str, chunk_size=450, overlap=100) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks

# ============================================================
# Sentence splitting
# ============================================================
def split_sentences(text: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    clean = []
    for s in sentences:
        s = s.strip()
        if 25 <= len(s) <= 220:
            clean.append(s)
    return clean

# ============================================================
# Question classification
# ============================================================
def is_definition_question(question: str) -> bool:
    q = question.lower()
    return any(p in q for p in [
        "what is",
        "what does",
        "stand for",
        "define",
        "what type",
        "what kind",
        "how do"
    ])

# ============================================================
# Clean spoken language
# ============================================================
def clean_sentence(sent: str) -> str:
    sent = re.sub(r"\b(well|so|like|basically|something like)\b", "", sent, flags=re.I)
    sent = re.sub(r"\s+", " ", sent)
    sent = sent.strip(" ,.-")
    return sent

# ============================================================
# MAIN QUERY
# ============================================================
def answer_query_for_doc(doc_id: str, question: str, top_k: int = 3):

    doc = load_doc(doc_id)
    transcript = doc.get("transcript", [])

    if not transcript:
        return {
            "status": "empty",
            "answer": "Transcript is empty.",
            "sources": []
        }

    full_text = " ".join(seg.get("text", "") for seg in transcript)

    chunks = chunk_text(full_text)
    model = get_embed_model()

    chunk_embeddings = model.encode(chunks)
    query_embedding = model.encode(question)

    ranked_chunks = sorted(
        [(cosine_sim(e, query_embedding), c) for e, c in zip(chunk_embeddings, chunks)],
        reverse=True
    )

    top_chunks = [c for s, c in ranked_chunks[:top_k] if s > 0.35]

    if not top_chunks:
        return {
            "status": "irrelevant",
            "answer": "This question is not covered in the provided transcript.",
            "sources": []
        }

    candidate_sentences = []
    for chunk in top_chunks:
        candidate_sentences.extend(split_sentences(chunk))

    sent_embeddings = model.encode(candidate_sentences)

    ranked_sentences = sorted(
        [(cosine_sim(e, query_embedding), s) for e, s in zip(sent_embeddings, candidate_sentences)],
        reverse=True
    )

    # -------- HARD FILTER --------
    filtered = [(s, t) for s, t in ranked_sentences if s >= 0.5]

    if not filtered:
        return {
            "status": "irrelevant",
            "answer": "This question is not covered in the provided transcript.",
            "sources": []
        }

    # -------- FINAL ANSWER --------
    if is_definition_question(question):
        answer = clean_sentence(filtered[0][1])
    else:
        answer = " ".join(clean_sentence(t) for _, t in filtered[:2])

    sources = [
        {
            "score": round(score, 3),
            "preview": sent[:160] + "..."
        }
        for score, sent in ranked_sentences[:top_k]
    ]

    return {
        "status": "ok",
        "doc_id": doc_id,
        "question": question,
        "answer": answer,
        "sources": sources,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }
