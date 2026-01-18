# YouTube RAG QA System

Enterprise-style **Retrieval-Augmented Generation (RAG)** application that enables
users to **ask grounded questions directly on YouTube video content**.

The system ingests video transcripts, performs semantic retrieval using embeddings,
and returns **precise, hallucination-free answers** backed by retrieved evidence.

This project focuses on **real RAG architecture**, not simple LLM prompting.



## Problem Statement

Most YouTube Q&A tools and AI demos:

- rely purely on LLM prompting
- hallucinate answers not present in the video
- lack retrieval transparency
- cannot scale beyond small inputs
- provide no explainability

In real-world AI systems, this approach is unreliable.

Enterprises require:

- grounded answers
- deterministic retrieval
- explainable evidence
- predictable system behavior



## Solution Overview

This project implements a **true Retrieval-Augmented Generation pipeline** that:

- ingests YouTube transcripts
- chunks content with semantic overlap
- converts text into embeddings
- retrieves relevant context using cosine similarity
- answers questions **strictly from retrieved content**
- refuses to answer when information is missing

The system behaves like a **knowledge-grounded search engine**, not a chatbot.



## Live Deployment

🌐 **Application URL**  
https://youtube-rag-qa-1.onrender.com/

📦 **GitHub Repository**  
https://github.com/Sreeja-Reddy-0612/youtube-rag-qa



## System Architecture

```text
YouTube Video
     ↓
Transcript Extraction
     ↓
Text Normalization
     ↓
Chunking Engine
 (overlap-based)
     ↓
Sentence Embeddings
 (SentenceTransformers)
     ↓
Semantic Retrieval
 (Cosine Similarity)
     ↓
Sentence-Level Re-ranking
     ↓
Grounded Answer Generation
     ↓
Frontend UI with Sources
```



## Key Features

- YouTube transcript ingestion
- Manual transcript upload support
- Semantic text chunking with overlap
- SentenceTransformers embeddings
- Cosine similarity–based retrieval
- Top-K relevant chunk selection
- Sentence-level re-ranking
- Definition-aware answer extraction
- Hallucination prevention
- Honest fallback when answer not present
- Fully integrated frontend and backend
- Deployment-ready architecture



## Technology Stack

### Backend

- Python 3.10
- FastAPI
- SentenceTransformers
- NumPy
- Cosine similarity search
- Uvicorn

### Frontend

- React (Vite)
- JavaScript / JSX
- REST API integration
- Minimal responsive UI

### Storage

- JSON-based transcript store
- File-backed embedding index



## How It Works (Step-by-Step)

1. User submits a YouTube video URL
2. Transcript is extracted or uploaded manually
3. Transcript is normalized and cleaned
4. Text is split into overlapping semantic chunks
5. Each chunk is embedded into vector space
6. User question is embedded
7. Cosine similarity ranks relevant chunks
8. Sentence-level filtering improves precision
9. Only relevant sentences are selected
10. Answer is generated **strictly from retrieved text**
11. Sources and similarity scores are returned
12. If no relevant context exists → system refuses to answer



## Example Queries Supported

- What is a Large Language Model?
- What type of AI model is an LLM?
- How are LLMs different from traditional programming?
- What data are LLMs trained on?
- How do AI agents differ from chatbots?

All answers are derived **only from video content**, not model memory.



## Local Setup

### Backend

```bash
cd backend

python -m venv venv
venv\Scripts\activate

pip install -r ../requirements.txt

uvicorn backend.app.main:app --reload
```

Backend runs at:

```
http://localhost:8000
```



### Frontend

```bash
cd frontend

npm install
npm run dev
```

Frontend runs at:

```
http://localhost:5173
```



## Environment Configuration

### Backend `.env`

```env
OPENAI_API_KEY=optional
```


` .env.example `

```env
YOUTUBE_API_KEY=YOUR_YOUTUBE_API_KEY_HERE
```


> LLM is optional — the system works fully using embeddings and retrieval.



### Frontend `.env.production`

```env
VITE_BACKEND_URL=https://youtube-rag-qa.onrender.com
```



## Design Principles

- Retrieval before generation
- No hallucinated answers
- Explainability over fluency
- Deterministic system behavior
- Production-style architecture
- Clear separation of concerns
- Scalable retrieval logic



## What This Project Demonstrates

- Real-world RAG architecture
- Semantic search fundamentals
- Embedding-based retrieval
- Chunking strategy design
- Similarity scoring
- Sentence-level ranking
- Backend–frontend integration
- Deployment-aware engineering
- AI system reliability thinking



## Future Improvements

- FAISS vector database indexing
- Metadata-aware retrieval
- Timestamp-based video jump links
- Cross-encoder re-ranking
- Hybrid BM25 + vector retrieval
- RAG evaluation metrics
- Multi-document querying
- Caching and performance optimization



## Author

**Sreeja Reddy**  
AI Engineer focused on:

- Retrieval-Augmented Generation (RAG)
- LLM reliability and evaluation
- Semantic search systems
- AI infrastructure engineering

GitHub:  
https://github.com/Sreeja-Reddy-0612

LinkedIn:  
https://www.linkedin.com/in/sreeja-reddy-5ab708288/
