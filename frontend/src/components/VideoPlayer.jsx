// File: frontend/src/components/VideoPlayer.jsx
// What it does: Simple YouTube embed. Provides a clickable embed that can start at a timestamp.
// Variables to change:
//   - width/height can be adjusted; this is a simple iframe-based player.
// Props:
//   - videoId: string (YouTube video id, e.g., "dQw4w9WgXcQ")
//   - startSec: number (optional) - seconds to start at (will be appended to URL)
import React from "react";

export default function VideoPlayer({ videoId, startSec }) {
  if (!videoId) return null;
  const startParam = startSec ? `?start=${Math.floor(startSec)}` : "";
  const src = `https://www.youtube.com/embed/${videoId}${startParam}`;
  return (
    <div style={{ marginTop: 12 }}>
      <iframe
        width="800"
        height="450"
        src={src}
        title="YouTube player"
        frameBorder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
    </div>
  );
}
