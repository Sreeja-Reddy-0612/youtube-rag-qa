import os
import json
import re
import numpy as np
from typing import List, Dict, Any
from datetime import datetime

from sentence_transformers import SentenceTransformer
from numpy.linalg import norm

# ============================================================
# PROJECT ROOT (VERY IMPORTANT FIX)
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../")
)

DATA_DIR = os.path.join(PROJECT_ROOT, "data", "transcripts")

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

def cosine_sim(a, b):
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

def chunk_text(text: str, chunk_size=450, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# ============================================================
# Sentence splitting
# ============================================================

def split_sentences(text: str):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [
        s.strip()
        for s in sentences
        if 30 <= len(s.strip()) <= 250
    ]

# ============================================================
# Question classification
# ============================================================

def is_definition_question(question: str) -> bool:
    q = question.lower()
    return any(
        p in q for p in [
            "what is",
            "what does",
            "stand for",
            "define",
            "meaning of",
            "what type",
            "what kind"
        ]
    )

# ============================================================
# MAIN QUERY FUNCTION
# ============================================================

def answer_query_for_doc(doc_id: str, question: str, top_k: int = 3):

    doc = load_doc(doc_id)
    transcript_items = doc.get("transcript", [])

    if not transcript_items:
        return {
            "status": "empty",
            "answer": "Transcript is empty.",
            "sources": []
        }

    full_text = " ".join(
        seg.get("text", "")
        for seg in transcript_items
        if isinstance(seg, dict)
    )

    chunks = chunk_text(full_text)

    model = get_embed_model()
    chunk_embeddings = model.encode(chunks)
    query_embedding = model.encode(question)

    ranked_chunks = []
    for chunk, emb in zip(chunks, chunk_embeddings):
        score = cosine_sim(emb, query_embedding)
        ranked_chunks.append((score, chunk))

    ranked_chunks.sort(reverse=True)
    top_chunks = [c for c in ranked_chunks[:top_k] if c[0] > 0.35]

    if not top_chunks:
        return {
            "status": "irrelevant",
            "answer": "This question is not covered in the provided transcript.",
            "sources": []
        }

    candidate_sentences = []
    for _, chunk in top_chunks:
        candidate_sentences.extend(split_sentences(chunk))

    sent_embeddings = model.encode(candidate_sentences)

    ranked_sentences = []
    for sent, emb in zip(candidate_sentences, sent_embeddings):
        ranked_sentences.append((cosine_sim(emb, query_embedding), sent))

    ranked_sentences.sort(reverse=True)

    filtered = [(s, t) for s, t in ranked_sentences if s >= 0.48]

    if not filtered:
        return {
            "status": "irrelevant",
            "answer": "This question is not covered in the provided transcript.",
            "sources": []
        }

    answers = [t for _, t in filtered]

    if is_definition_question(question):
        answer = answers[0]
    else:
        answer = " ".join(answers[:2])

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
