import axios from "axios";
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function ingestUrl(youtubeUrl) {
  const res = await axios.post(`${BASE_URL}/ingest`, { youtube_url: youtubeUrl });
  return res.data;
}

export async function ingestTranscript(text) {
  const res = await axios.post(`${BASE_URL}/ingest`, { transcript_text: text });
  return res.data;
}

export async function queryDoc(doc_id, question) {
  const res = await axios.post(`${BASE_URL}/query`, { doc_id, question });
  return res.data;
}

export async function runASR(doc_id, video_id) {
  const res = await axios.post(`${BASE_URL}/ingest/asr`, { doc_id, video_id });
  return res.data;
}
