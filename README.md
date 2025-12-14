# 🎥 YouTube RAG Q&A System

### Retrieval-Augmented Question Answering over Video Transcripts

A **production-style Retrieval-Augmented Generation (RAG) system** that enables users to ask **grounded, explainable questions** over YouTube video transcripts.

This project is built to understand **how modern LLM systems actually work internally** — not just how to call an API.




## 🚀 Key Highlights

✔ Grounded answers (no hallucination)
✔ Retrieval before generation
✔ Semantic search using embeddings
✔ Explainable sources for every answer
✔ Honest fallback when information is missing
✔ Full-stack system (FastAPI + React)




## 🧠 Problem Statement

Large Language Models are powerful but **hallucinate** when asked questions outside their context.

This project solves that by:

1. Retrieving only relevant context from a trusted source
2. Answering **strictly from retrieved content**
3. Returning **no answer** if the information does not exist

This is the core idea behind **Retrieval-Augmented Generation (RAG)**.




## 🏗️ System Architecture

1. Transcript ingestion (manual or YouTube)
2. Text chunking with overlap for semantic continuity
3. Embedding generation using SentenceTransformers
4. Semantic retrieval using cosine similarity
5. Sentence-level re-ranking for precision
6. Clean answer generation from retrieved context
7. Source attribution for transparency



## 🛠️ Tech Stack

**Backend**

* Python
* FastAPI
* SentenceTransformers
* NumPy
* Cosine similarity–based retrieval

**Frontend**

* React (Vite)
* Clean query + answer UI
* Source previews for explainability



## ✨ Features

* Ingest long transcripts without token limits
* Chunk-overlap strategy to preserve meaning
* Top-K semantic retrieval
* Definition-aware answer selection
* Semantic deduplication of answers
* Honest fallback when answer is not present
* Production-ready code structure


## 🎯 Learning Outcomes

Through this project, I gained hands-on understanding of:

* How embeddings represent semantic meaning
* Why cosine similarity works for retrieval
* Chunking strategies for long documents
* Why RAG is essential for trustworthy AI
* How production AI systems differ from demos



## 🔮 Future Improvements

* Vector databases (FAISS / Chroma)
* Metadata-aware retrieval
* Hybrid keyword + semantic search
* Reranking with cross-encoders
* Timestamp-based YouTube jumping
* Evaluation metrics for retrieval quality


