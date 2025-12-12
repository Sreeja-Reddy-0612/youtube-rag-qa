// File: frontend/src/pages/IngestPage.jsx
// What it does:
//   - Page to submit a YouTube URL or paste a transcript. Calls backend /ingest and /ingest/asr.
//   - Displays returned metadata and transcript inline.
// Variables you may change:
//   - If your backend is on another host, set VITE_API_BASE_URL in frontend .env file.
// Notes:
//   - Requires `runASR` exported from src/api.js (see below).
//   - The Run ASR button will call backend /ingest/asr and replace statusData with the ASR result.

import React, { useState } from "react";
import { ingestUrl, ingestTranscript, runASR } from "../api";
import ProgressSpinner from "../components/ProgressSpinner";

export default function IngestPage() {
  const [url, setUrl] = useState("");
  const [transcript, setTranscript] = useState("");
  const [loading, setLoading] = useState(false);

  // statusRaw: textual JSON string for debugging display
  const [statusRaw, setStatusRaw] = useState(null);
  // statusData: parsed object returned by backend (if available)
  const [statusData, setStatusData] = useState(null);
  const [docId, setDocId] = useState(null);

  async function handleUrlSubmit(e) {
    e.preventDefault();
    setStatusRaw(null);
    setStatusData(null);
    setDocId(null);
    if (!url || !url.trim()) return;
    setLoading(true);
    try {
      const data = await ingestUrl(url.trim());
      // data is expected to be an object with doc_id, status, transcript, metadata, etc.
      setDocId(data.doc_id || data.id || null);
      setStatusData(data);
      // Keep a raw JSON string copy for debug view
      setStatusRaw(JSON.stringify(data, null, 2));
    } catch (err) {
      console.error(err);
      const message = err.response?.data?.detail || err.message || String(err);
      setStatusRaw("Error: " + message);
    } finally {
      setLoading(false);
    }
  }

  async function handleTranscriptSubmit(e) {
    e.preventDefault();
    setStatusRaw(null);
    setStatusData(null);
    setDocId(null);
    if (!transcript || !transcript.trim()) return;
    setLoading(true);
    try {
      const data = await ingestTranscript(transcript, {});
      setDocId(data.doc_id || data.id || null);
      setStatusData(data);
      setStatusRaw(JSON.stringify(data, null, 2));
    } catch (err) {
      console.error(err);
      const message = err.response?.data?.detail || err.message || String(err);
      setStatusRaw("Error: " + message);
    } finally {
      setLoading(false);
    }
  }

  // Helper to render transcript segments (if present)
  function renderTranscriptSegments(transcriptArr) {
    if (!Array.isArray(transcriptArr)) return null;
    if (transcriptArr.length === 0) {
      return (
        <div style={{ color: "#a00", marginTop: 8 }}>
          <strong>No captions found for this video.</strong>
          <div style={{ marginTop: 6 }}>
            Status indicates <code>needs_asr</code>. Click <em>Run ASR</em> to generate a transcript using Whisper (OpenAI) or run a local ASR.
          </div>
        </div>
      );
    }

    return (
      <div
        style={{
          maxHeight: 360,
          overflow: "auto",
          border: "1px solid #eee",
          padding: 10,
          borderRadius: 6,
          background: "#fff",
        }}
      >
        {transcriptArr.map((s, i) => (
          <div key={i} style={{ marginBottom: 12 }}>
            <div style={{ color: "#555", fontSize: 13 }}>
              <strong>{Number.isFinite(s.start) ? Math.floor(s.start) : 0}s</strong> →{" "}
              {Number.isFinite(s.end) ? Math.floor(s.end) : (Number.isFinite(s.duration) ? Math.floor((s.start||0) + (s.duration||0)) : 0)}s
            </div>
            <div style={{ marginTop: 6, whiteSpace: "pre-wrap" }}>{s.text}</div>
          </div>
        ))}
      </div>
    );
  }

  // Handler to run ASR when backend returns needs_asr
  async function handleRunASR() {
    if (!statusData) return;
    setStatusRaw(null);
    setLoading(true);
    try {
      // use doc_id if available, else video_id
      const res = await runASR(statusData.doc_id || null, statusData.video_id || null);
      setStatusData(res);
      setDocId(res.doc_id || statusData.doc_id || docId);
      setStatusRaw(JSON.stringify(res, null, 2));
    } catch (e) {
      console.error(e);
      const message = e.response?.data?.detail || e.message || String(e);
      setStatusRaw("ASR error: " + message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Ingest</h2>

      <section style={{ marginBottom: 18 }}>
        <form onSubmit={handleUrlSubmit}>
          <label style={{ display: "block", marginBottom: 6 }}>YouTube URL</label>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            style={{ width: "100%", padding: 8, boxSizing: "border-box" }}
          />
          <div style={{ marginTop: 8 }}>
            <button type="submit" disabled={!url || loading}>
              Ingest URL
            </button>
          </div>
        </form>
      </section>

      <section style={{ marginBottom: 18 }}>
        <form onSubmit={handleTranscriptSubmit}>
          <label style={{ display: "block", marginBottom: 6 }}>Paste Transcript (optional)</label>
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            rows={10}
            style={{ width: "100%", padding: 8, boxSizing: "border-box" }}
            placeholder="Paste transcript text with timestamps or plain text..."
          />
          <div style={{ marginTop: 8 }}>
            <button type="submit" disabled={!transcript || loading}>
              Ingest Transcript
            </button>
          </div>
        </form>
      </section>

      <section>
        {/* Loading indicator */}
        {loading && (
          <div style={{ marginBottom: 12 }}>
            <ProgressSpinner />
          </div>
        )}

        {/* Raw status JSON / error */}
        {statusRaw && (
          <div style={{ marginTop: 12, padding: 10, background: "#f8f8f8", borderRadius: 6 }}>
            <strong>Response (raw):</strong>
            <pre style={{ marginTop: 8, maxHeight: 220, overflow: "auto" }}>{statusRaw}</pre>
          </div>
        )}

        {/* Parsed / friendly display */}
        {statusData && (
          <div style={{ marginTop: 12 }}>
            <div style={{ marginBottom: 8 }}>
              <strong>doc_id:</strong> <code>{statusData.doc_id || docId}</code>
            </div>

            {/* metadata (title / channel) */}
            {statusData.metadata && (statusData.metadata.title || statusData.metadata.channelTitle) && (
              <div style={{ marginBottom: 10 }}>
                {statusData.metadata.title && (
                  <div>
                    <strong>Title:</strong> {statusData.metadata.title}
                  </div>
                )}
                {statusData.metadata.channelTitle && (
                  <div>
                    <strong>Channel:</strong> {statusData.metadata.channelTitle}
                  </div>
                )}
              </div>
            )}

            {/* Transcript */}
            <div>
              <h4 style={{ marginBottom: 8 }}>Transcript ({(statusData.transcript || []).length})</h4>
              {renderTranscriptSegments(statusData.transcript || [])}
            </div>

            {/* Run ASR button when needed */}
            {statusData && statusData.status === "needs_asr" && (
              <div style={{ marginTop: 12 }}>
                <button onClick={handleRunASR} disabled={loading}>
                  {loading ? "Running ASR..." : "Run ASR (generate transcript)"}
                </button>
              </div>
            )}

            <div style={{ marginTop: 12 }}>
              <small>
                If you want to ask questions about this transcript, go to the <a href="/query">Query</a> page and paste the <code>{statusData.doc_id || docId}</code>.
              </small>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
