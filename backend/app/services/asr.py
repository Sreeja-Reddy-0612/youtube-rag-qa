"""
backend/app/services/asr.py

What it does:
- Downloads audio for a YouTube video id using yt-dlp into backend/data/audio/{video_id}.mp3
- Sends the audio file to OpenAI Whisper (whisper-1) for transcription (requires OPENAI_API_KEY in .env)
- Normalizes the result into segments dicts: {start, duration, end, text}
- Updates the existing transcript JSON file (found by video_id) or creates a new one.
"""

import os
import json
import subprocess
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import openai
import shutil

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # backend/app
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
TRANSCRIPTS_DIR = os.path.join(DATA_DIR, "transcripts")
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

openai.api_key = OPENAI_API_KEY

def _find_transcript_path_for_video(video_id: str) -> Optional[str]:
    for fname in os.listdir(TRANSCRIPTS_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(TRANSCRIPTS_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if payload.get("video_id") == video_id:
                return path
        except Exception:
            continue
    return None

def download_audio_youtube(video_id: str, out_path: Optional[str] = None) -> str:
    """
    Downloads audio-only (best audio) with yt-dlp to out_path (mp3/m4a). Returns file path.
    Requires yt-dlp installed (we added to requirements).
    """
    if out_path is None:
        out_path = os.path.join(AUDIO_DIR, f"{video_id}.mp3")
    # Use yt-dlp to extract audio as mp3 (ffmpeg must be on PATH).
    ytdl_cmd = [
        "yt-dlp",
        "--quiet",
        "-f", "bestaudio",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--output", out_path,
        f"https://www.youtube.com/watch?v={video_id}"
    ]
    # Run command
    subprocess.run(ytdl_cmd, check=True)
    if not os.path.exists(out_path):
        raise RuntimeError("Audio download failed, file not found: " + out_path)
    return out_path

def transcribe_with_openai_whisper(audio_file: str) -> List[Dict[str, Any]]:
    """
    Calls OpenAI whisper-1 model to transcribe audio file.
    Returns list of segments: {start, duration, end, text}
    Note: the API returns plain text or a JSON with timestamps depending on endpoint; here we use the Python client
    and request response in 'verbose_json' via 'response_format' if available. If not, we will chunk text as single segment.
    """
    if OPENAI_API_KEY is None:
        raise RuntimeError("OPENAI_API_KEY not set in environment")

    # Using openai.Audio.transcribe (OpenAI python client). Some client versions accept:
    # openai.Audio.transcribe("whisper-1", open(audio_file, "rb"))
    # The returned object may have 'segments' with timestamps depending on API; handle both.
    with open(audio_file, "rb") as af:
        # this uses the standard whisper model; adjust if API changes
        resp = openai.Audio.transcribe(model="whisper-1", file=af)
    # Try to extract segments
    segments = []
    if isinstance(resp, dict):
        # Newer responses sometimes have 'segments' with start/end/ text
        segs = resp.get("segments") or resp.get("results", {}).get("segments")
        if segs:
            for s in segs:
                start = float(s.get("start", 0.0))
                end = float(s.get("end", s.get("start", 0.0)))
                text = s.get("text") or s.get("alternatives", [{}])[0].get("transcript", "")
                segments.append({"start": start, "duration": end - start, "end": end, "text": text.strip()})
            return segments
        # fallback: if 'text' key exists as full transcript
        text_full = resp.get("text") or resp.get("transcript")
        if text_full:
            return [{"start": 0.0, "duration": 0.0, "end": 0.0, "text": text_full.strip()}]
    # if resp not dict or no segments, return full text as single segment
    return [{"start": 0.0, "duration": 0.0, "end": 0.0, "text": str(resp)}]

def run_asr_for_video(video_id: str) -> Dict[str, Any]:
    """
    Full pipeline: download audio, transcribe, update or create transcript JSON file.
    Returns dict similar to ingest response with status/doc_id/file_path/transcript.
    """
    try:
        audio_path = download_audio_youtube(video_id)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("yt-dlp failed: " + str(e))
    except Exception as e:
        raise

    segments = transcribe_with_openai_whisper(audio_path)

    # If there is an existing transcript JSON for this video, update it; else create new doc_id.
    existing_path = _find_transcript_path_for_video(video_id)
    if existing_path:
        with open(existing_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        payload["transcript"] = segments
        with open(existing_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return {"status": "ingested", "doc_id": payload.get("doc_id"), "file_path": existing_path, "video_id": video_id, "message": "ASR completed and existing transcript updated.", "transcript": segments}
    else:
        # create a new JSON doc
        from datetime import datetime
        doc_id = str(uuid.uuid4())
        payload = {
            "doc_id": doc_id,
            "source": f"asr:{video_id}",
            "video_id": video_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "metadata": {},
            "transcript": segments,
        }
        out_path = os.path.join(TRANSCRIPTS_DIR, f"{doc_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return {"status": "ingested", "doc_id": doc_id, "file_path": out_path, "video_id": video_id, "message": "ASR completed and transcript created.", "transcript": segments}
