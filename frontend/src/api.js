import axios from "axios";

const BASE_URL = import.meta.env.VITE_BACKEND_URL.replace(/\/$/, "");

export async function ingestTranscript(payload) {
  const res = await axios.post(`${BASE_URL}/ingest`, payload);
  return res.data;
}

export async function queryDoc(doc_id, question, top_k = 3) {
  const res = await axios.post(`${BASE_URL}/query`, {
    doc_id,
    question,
    top_k,
  });
  return res.data;
}


export async function ingestUrl(youtubeUrl) {
  const res = await axios.post(`${BASE_URL}/ingest`, { youtube_url: youtubeUrl });
  return res.data;
}



export async function runASR(doc_id, video_id) {
  const res = await axios.post(`${BASE_URL}/ingest/asr`, { doc_id, video_id });
  return res.data;
}
