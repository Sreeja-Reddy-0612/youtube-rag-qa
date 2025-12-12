// File: frontend/src/components/ProgressSpinner.jsx
// What it does: Tiny inline spinner used during API calls.
// Variables to change: style, size — small inline component.
import React from "react";

export default function ProgressSpinner({ size = 18, label = "Processing..." }) {
  const border = Math.max(2, Math.floor(size / 6));
  const style = {
    width: size,
    height: size,
    borderRadius: size / 2,
    border: `${border}px solid #ddd`,
    borderTopColor: "#333",
    animation: "spin 1s linear infinite",
    display: "inline-block",
  };

  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
      <div style={style} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <div style={{ fontSize: 13, color: "#333" }}>{label}</div>
    </div>
  );
}
