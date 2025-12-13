// File: frontend/src/pages/QueryPage.jsx
// Purpose: Query an ingested document and display grounded answers + sources

import React, { useState } from "react";
import { queryDoc } from "../api";
import ResultCard from "../components/ResultCard";

export default function QueryPage() {
  const [docId, setDocId] = useState("");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();

    setError(null);
    setResult(null);
    setLoading(true);

    try {
      const res = await queryDoc(docId.trim(), question.trim());
      setResult(res);
    } catch (err) {
      console.error(err);
      setError(
        err?.response?.data ||
        err?.message ||
        "Query failed"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>YouTube RAG – Query</h2>

      <form onSubmit={handleSubmit} style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 10 }}>
          <label>doc_id</label><br />
          <input
            value={docId}
            onChange={(e) => setDocId(e.target.value)}
            placeholder="Paste doc_id from ingest"
            style={{ width: "60%", padding: 8 }}
          />
        </div>

        <div style={{ marginBottom: 10 }}>
          <label>Question</label><br />
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about the video"
            style={{ width: "100%", padding: 8 }}
          />
        </div>

        <button type="submit" disabled={!docId || !question || loading}>
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>

      {/* Loading */}
      {loading && <div>Loading...</div>}

      {/* Error */}
      {error && (
        <div style={{ marginTop: 12, padding: 10, background: "#fee", borderRadius: 6 }}>
          <strong>Error</strong>
          <pre style={{ marginTop: 6 }}>
            {typeof error === "string"
              ? error
              : JSON.stringify(error, null, 2)}
          </pre>
        </div>
      )}

      {/* Result */}
      {result && result.status === "ok" && (
        <div style={{ marginTop: 16 }}>
          <ResultCard result={result} />

          {result.sources && result.sources.length > 0 && (
            <>
              <h4>Sources</h4>
              {result.sources.map((s, i) => (
                <div
                  key={i}
                  style={{
                    marginBottom: 12,
                    padding: 8,
                    border: "1px solid #eee",
                    borderRadius: 6
                  }}
                >
                  <div style={{ marginTop: 4 }}>
                    {s.preview}
                  </div>
                  <small>Similarity: {s.score}</small>
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {/* No answer / irrelevant */}
      {result && result.status !== "ok" && (
        <div style={{ marginTop: 12, padding: 10, background: "#fff3cd" }}>
          {result.answer}
        </div>
      )}
    </div>
  );
}
