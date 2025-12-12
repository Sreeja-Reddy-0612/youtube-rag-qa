// File: frontend/src/pages/QueryPage.jsx
// What it does: Page to query an ingested doc_id and display answer + sources.
// Variables to change:
//   - none. If backend port changes set VITE_API_BASE_URL.

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
      setError(err.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Query</h2>

      <form onSubmit={handleSubmit} style={{ marginBottom: 12 }}>
        <div style={{ marginBottom: 8 }}>
          <label>doc_id</label><br />
          <input value={docId} onChange={(e) => setDocId(e.target.value)} placeholder="doc_id from ingest" style={{ width: "50%", padding: 8 }} />
        </div>

        <div style={{ marginBottom: 8 }}>
          <label>Question</label><br />
          <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask a question about the video content" style={{ width: "100%", padding: 8 }} />
        </div>

        <button type="submit" disabled={!docId || !question || loading}>Ask</button>
      </form>

      <div>
        {loading && <div>Loading...</div>}

        {error && (
          <div style={{ marginTop: 10, padding: 10, background: "#fee", borderRadius: 6 }}>
            <strong>Error:</strong>
            <pre style={{ marginTop: 6 }}>{JSON.stringify(error, null, 2)}</pre>
          </div>
        )}

        {result && !result.error && (
          <div style={{ marginTop: 12 }}>
            <ResultCard result={result} />
          </div>
        )}

        {result && result.error && (
          <div style={{ marginTop: 12, padding: 8, background: "#fff3cd" }}>
            <strong>Backend error:</strong>
            <pre>{JSON.stringify(result.error, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
