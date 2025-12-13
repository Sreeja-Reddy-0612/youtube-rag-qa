// frontend/src/pages/IngestPage.jsx

import React, { useState } from "react";
import { ingestTranscript } from "../api";
import ProgressSpinner from "../components/ProgressSpinner";

export default function IngestPage() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [rawTranscript, setRawTranscript] = useState("");
  const [loading, setLoading] = useState(false);

  const [statusRaw, setStatusRaw] = useState(null);
  const [docId, setDocId] = useState(null);

  // -----------------------------
  // Convert pasted text → segments
  // -----------------------------
  function parseTranscript(text) {
    /*
      Supported formats per line:
      12.3 - 18.5 text
      12.3 --> 18.5 text
      OR plain text (single segment)
    */
    const lines = text
      .split("\n")
      .map(l => l.trim())
      .filter(Boolean);

    const segments = [];

    for (const line of lines) {
      const match = line.match(
        /(\d+(\.\d+)?)\s*(?:-|–|-->|→)\s*(\d+(\.\d+)?)\s*(.*)/
      );

      if (match) {
        segments.push({
          start: parseFloat(match[1]),
          end: parseFloat(match[3]),
          text: match[5]
        });
      }
    }

    // Fallback: whole transcript as one segment
    if (segments.length === 0) {
      segments.push({
        start: 0,
        end: 0,
        text
      });
    }

    return segments;
  }

  // -----------------------------
  // Submit handler
  // -----------------------------
  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setStatusRaw(null);
    setDocId(null);

    try {
      if (!rawTranscript.trim()) {
        alert("Please paste a transcript");
        return;
      }

      const transcriptSegments = parseTranscript(rawTranscript);

      const payload = {
        youtube_url: youtubeUrl || null,
        transcript: transcriptSegments
      };

      const res = await ingestTranscript(payload);

      setDocId(res.doc_id);
      setStatusRaw(JSON.stringify(res, null, 2));
    } catch (err) {
      console.error(err);
      setStatusRaw(
        JSON.stringify(err.response?.data || err.message, null, 2)
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Ingest Transcript</h2>

      <form onSubmit={handleSubmit}>
        <label>YouTube URL (optional)</label>
        <input
          value={youtubeUrl}
          onChange={e => setYoutubeUrl(e.target.value)}
          placeholder="https://www.youtube.com/watch?v=..."
          style={{ width: "100%", padding: 8, marginBottom: 12 }}
        />

        <label>Paste Transcript (required)</label>
        <textarea
          rows={12}
          value={rawTranscript}
          onChange={e => setRawTranscript(e.target.value)}
          placeholder="12.3 --> 18.5 This is a sentence..."
          style={{ width: "100%", padding: 8 }}
        />

        <div style={{ marginTop: 12 }}>
          <button disabled={loading}>
            {loading ? "Ingesting..." : "Ingest"}
          </button>
        </div>
      </form>

      {loading && <ProgressSpinner />}

      {statusRaw && (
        <div style={{ marginTop: 16 }}>
          <strong>Backend Response</strong>
          <pre
            style={{
              background: "#f8f8f8",
              padding: 10,
              maxHeight: 300,
              overflow: "auto"
            }}
          >
            {statusRaw}
          </pre>
        </div>
      )}

      {docId && (
        <div style={{ marginTop: 12 }}>
          <strong>doc_id:</strong> <code>{docId}</code>
          <br />
          Go to <a href="/query">Query</a> page to ask questions.
        </div>
      )}
    </div>
  );
}
