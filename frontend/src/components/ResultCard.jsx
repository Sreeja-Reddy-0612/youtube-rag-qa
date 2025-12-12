// File: frontend/src/components/ResultCard.jsx
// What it does: Displays the returned answer and list of source snippets with timestamp links.
// Variables to change:
//   - None. Expects `result` prop with structure:
//     { answer: string, sources: [{ start, end, text, score, video_id }], metadata?: {} }
import React from "react";
import VideoPlayer from "./VideoPlayer";

/**
 * Helper: extract video id from sources if present (takes first available).
 */
function findVideoId(sources = []) {
  for (const s of sources) {
    if (s.video_id) return s.video_id;
    if (s.url && s.url.includes("youtube")) {
      try {
        const url = new URL(s.url);
        return url.searchParams.get("v");
      } catch (e) {}
    }
  }
  return null;
}

export default function ResultCard({ result }) {
  if (!result) return null;
  const { answer, sources = [], metadata } = result;
  const primaryVideoId = findVideoId(sources);

  return (
    <div style={{ border: "1px solid #e6e6e6", borderRadius: 8, padding: 12 }}>
      <h3 style={{ marginTop: 0 }}>Answer</h3>
      <div style={{ marginBottom: 12, whiteSpace: "pre-wrap" }}>{answer || "No answer returned"}</div>

      <h4>Sources ({sources.length})</h4>
      {sources.length ? (
        <>
          <div style={{ display: "grid", gap: 10 }}>
            {sources.map((s, i) => (
              <div key={i} style={{ padding: 10, background: "#fbfdff", borderRadius: 6 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontSize: 13, color: "#333" }}>
                    <strong>Segment:</strong> {Math.floor(s.start)}s - {Math.floor(s.end)}s
                  </div>
                  <div style={{ fontSize: 13, color: "#666" }}>score: {typeof s.score === "number" ? s.score.toFixed(3) : s.score}</div>
                </div>

                <div style={{ marginTop: 8, color: "#222" }}>{s.text?.slice(0, 600)}</div>

                <div style={{ marginTop: 8 }}>
                  {s.video_id ? (
                    <a href={`https://www.youtube.com/watch?v=${s.video_id}&t=${Math.floor(s.start)}s`} target="_blank" rel="noreferrer">
                      Open on YouTube at timestamp
                    </a>
                  ) : s.url ? (
                    <a href={s.url} target="_blank" rel="noreferrer">Open source</a>
                  ) : null}
                </div>
              </div>
            ))}
          </div>

          {/* Small inline video player if video id found */}
          {primaryVideoId && (
            <div style={{ marginTop: 14 }}>
              <VideoPlayer videoId={primaryVideoId} />
            </div>
          )}
        </>
      ) : (
        <div>No sources returned from backend</div>
      )}

      {metadata && (
        <div style={{ marginTop: 12, background: "#f6f8fa", padding: 8, borderRadius: 6 }}>
          <strong>Metadata</strong>
          <pre style={{ whiteSpace: "pre-wrap", margin: 6 }}>{JSON.stringify(metadata, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
