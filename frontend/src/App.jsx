// File: frontend/src/App.jsx
// What it does: Top-level app layout + routes.
// Variables to change: None required. Edit header/navigation if you like.
import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import IngestPage from "./pages/IngestPage";
import QueryPage from "./pages/QueryPage";

export default function App() {
  return (
    <div style={{ fontFamily: "Inter, system-ui, Arial", maxWidth: 980, margin: "28px auto", padding: 12 }}>
      <header style={{ marginBottom: 18 }}>
        <h1 style={{ margin: 0 }}>YouTube RAG QA</h1>
        <nav style={{ display: "flex", gap: 12, marginTop: 8 }}>
          <Link to="/">Ingest</Link>
          <Link to="/query">Query</Link>
        </nav>
        <hr />
      </header>

      <main>
        <Routes>
          <Route path="/" element={<IngestPage />} />
          <Route path="/query" element={<QueryPage />} />
        </Routes>
      </main>

      <footer style={{ marginTop: 36, color: "#666", fontSize: 13 }}>
        <div>Local backend BASE_URL: <code>http://localhost:8000</code> (change in <code>src/api.js</code> or via <code>.env</code>)</div>
      </footer>
    </div>
  );
}
