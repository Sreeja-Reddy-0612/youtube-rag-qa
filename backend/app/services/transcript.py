# backend/app/services/transcript.py
import os
import json
import uuid
import subprocess
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv

# Load env from backend/.env
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/app/services -> backend
load_dotenv(os.path.join(ROOT, ".env"))

DATA_DIR = os.getenv("DATA_DIR", os.path.join(ROOT, "data"))
TRANSCRIPTS_DIR = os.path.join(DATA_DIR, "transcripts")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
YT_DLP_BIN = os.getenv("YT_DLP_BIN", "yt-dlp")
FFMPEG_LOCATION = os.getenv("FFMPEG_LOCATION", None)  # optional explicit ffmpeg path
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)

# Ensure directories exist
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)


class TranscriptError(Exception):
    pass


def _save_json(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def save_transcript_json(doc_id: str, payload_json: Dict[str, Any]) -> str:
    path = os.path.join(TRANSCRIPTS_DIR, f"{doc_id}.json")
    # include file path in payload for convenience
    payload_json["__file_path__"] = path
    _save_json(path, payload_json)
    return path


def _read_transcript_json_if_exists(doc_id: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(TRANSCRIPTS_DIR, f"{doc_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_manual_transcript(transcript_text: str, title: Optional[str] = None, video_id: Optional[str] = None) -> str:
    doc_id = str(uuid.uuid4())
    metadata = {"title": title} if title else {}
    segment = {"start": 0.0, "duration": 0.0, "end": 0.0, "text": transcript_text}
    payload_json = {
        "doc_id": doc_id,
        "source": "manual_paste",
        "video_id": video_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "metadata": metadata,
        "transcript": [segment],
    }
    save_transcript_json(doc_id, payload_json)
    return doc_id


# ----------------- YouTube id extraction -----------------
def _extract_video_id(youtube_url: str) -> str:
    if "v=" in youtube_url:
        parts = youtube_url.split("v=")[1]
        return parts.split("&")[0]
    if "youtu.be/" in youtube_url:
        return youtube_url.split("youtu.be/")[1].split("?")[0]
    return youtube_url.strip()


# ----------------- Captions ingestion (youtube_transcript_api) -----------------
def ingest_youtube_transcript(youtube_url: str, try_languages: Optional[List[str]] = None, title_lookup: bool = True, cookies_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Try to fetch captions from YouTube (youtube_transcript_api). If not found, mark needs_asr.
    Avoid duplicate ingestion by checking transcripts dir for same video_id.
    """
    # Import inside function to avoid import errors at startup
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        # import exception names if present
        try:
            from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
        except Exception:
            try:
                from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound
            except Exception:
                TranscriptsDisabled = Exception
                NoTranscriptFound = Exception
    except Exception:
        # library missing -> treat as no captions available
        YouTubeTranscriptApi = None
        TranscriptsDisabled = Exception
        NoTranscriptFound = Exception

    video_id = _extract_video_id(youtube_url)

    # Check for existing transcript for same video_id
    for fname in os.listdir(TRANSCRIPTS_DIR):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(TRANSCRIPTS_DIR, fname), "r", encoding="utf-8") as f:
                existing = json.load(f)
                if existing.get("video_id") == video_id:
                    return {
                        "status": "already_ingested",
                        "doc_id": existing.get("doc_id"),
                        "file_path": os.path.join(TRANSCRIPTS_DIR, fname),
                        "video_id": video_id,
                        "message": "Video already ingested. Returning existing transcript.",
                        "metadata": existing.get("metadata", {}),
                        "transcript": existing.get("transcript", []),
                    }
        except Exception:
            continue

    doc_id = str(uuid.uuid4())
    metadata: Dict[str, Any] = {}
    transcript_segments: List[Dict[str, Any]] = []
    status = "needs_asr"
    message = "No captions available."

    # Try to fetch captions
    if YouTubeTranscriptApi:
        try:
            # best-effort robust usage across versions
            fetched_list = None
            try:
                if try_languages:
                    transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
                    fetched = None
                    for lang in try_languages:
                        try:
                            fetched = transcripts.find_transcript([lang])
                            break
                        except Exception:
                            continue
                    if fetched:
                        try:
                            fetched_list = fetched.fetch()
                        except Exception:
                            try:
                                fetched_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                            except Exception:
                                fetched_list = None
                else:
                    fetched_list = YouTubeTranscriptApi.get_transcript(video_id)
            except Exception as e:
                fetched_list = None
                err = e

            if fetched_list and isinstance(fetched_list, list):
                for seg in fetched_list:
                    start = float(seg.get("start", 0.0))
                    duration = float(seg.get("duration", 0.0))
                    end = start + duration
                    transcript_segments.append({"start": start, "duration": duration, "end": end, "text": seg.get("text", "")})
                status = "ingested_with_captions"
                message = "Captions fetched from YouTube."
            else:
                status = "needs_asr"
                message = "No captions available; needs ASR."
        except TranscriptsDisabled:
            status = "needs_asr"
            message = "Transcripts disabled on this video."
        except NoTranscriptFound:
            status = "needs_asr"
            message = "No transcript found via youtube_transcript_api."
        except Exception as e:
            status = "error"
            message = f"Exception fetching transcript: {repr(e)}"
    else:
        status = "needs_asr"
        message = "youtube_transcript_api not installed; cannot fetch captions."

    # Try to fetch lightweight metadata (title/description) using yt-dlp (dump json)
    if title_lookup:
        try:
            cmd = [YT_DLP_BIN, "--dump-single-json", f"https://www.youtube.com/watch?v={video_id}"]
            # if caller provided cookies_path, pass it; do not write cookies by default
            if cookies_path:
                cmd = cmd + ["--cookies", cookies_path]
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if p.returncode == 0 and p.stdout:
                try:
                    info = json.loads(p.stdout)
                    metadata["title"] = info.get("title")
                    metadata["description"] = info.get("description")
                    metadata["channelTitle"] = info.get("uploader") or info.get("channel")
                    metadata["publishedAt"] = info.get("upload_date")
                except Exception:
                    pass
        except Exception:
            pass

    payload_json = {
        "doc_id": doc_id,
        "source": "youtube",
        "video_id": video_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "metadata": metadata,
        "transcript": transcript_segments,
    }

    path = save_transcript_json(doc_id, payload_json)
    return {
        "status": status,
        "doc_id": doc_id,
        "file_path": path,
        "video_id": video_id,
        "message": message,
        "metadata": metadata,
        "transcript": transcript_segments,
    }


# ----------------- ASR helpers -----------------
def _download_audio_with_ytdlp(video_id: str, cookies_path: Optional[str] = None) -> str:
    """
    Download audio to data/audio/<video_id>.mp3
    Uses yt-dlp; avoids writing cookies by default. Raises TranscriptError on failure.
    """
    out_path = os.path.join(AUDIO_DIR, f"{video_id}.mp3")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        return out_path

    output_template = os.path.join(AUDIO_DIR, f"{video_id}.%(ext)s")
    cmd = [
        YT_DLP_BIN,
        "--quiet",
        "-f", "bestaudio",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--no-write-cookies",  # avoid creating cookies file
        "--output", output_template,
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    # if provided, pass cookies for restricted videos (caller must supply a valid file)
    if cookies_path:
        cmd = cmd[:-1] + ["--cookies", cookies_path, cmd[-1]]

    # optionally pass ffmpeg location if specified (some distributions)
    if FFMPEG_LOCATION:
        cmd = cmd + ["--ffmpeg-location", FFMPEG_LOCATION]

    # run the command and capture stderr for diagnostics
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        if proc.returncode != 0:
            # write stderr to a log for debugging
            log_path = os.path.join(AUDIO_DIR, f"{video_id}_ytdlp_err.log")
            with open(log_path, "w", encoding="utf-8") as ef:
                ef.write("STDOUT:\n")
                ef.write(proc.stdout or "")
                ef.write("\n\nSTDERR:\n")
                ef.write(proc.stderr or "")
            raise TranscriptError(f"yt-dlp failed: Command {cmd!r} returned non-zero exit status {proc.returncode}. See log: {log_path}")
        # ensure mp3 exists; if not, try to rename candidate
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            return out_path
        # find candidate file
        candidates = [p for p in os.listdir(AUDIO_DIR) if p.startswith(video_id + ".")]
        if candidates:
            src = os.path.join(AUDIO_DIR, candidates[0])
            shutil.move(src, out_path)
            return out_path
        raise TranscriptError("yt-dlp succeeded but audio file not found.")
    except subprocess.TimeoutExpired:
        raise TranscriptError("yt-dlp timed out while downloading audio.")
    except FileNotFoundError as fe:
        raise TranscriptError(f"yt-dlp not found or not executable (YT_DLP_BIN={YT_DLP_BIN}). Install yt-dlp and ensure it's on PATH. Error: {fe}")
    except TranscriptError:
        raise
    except Exception as e:
        raise TranscriptError(f"yt-dlp failed: {repr(e)}")


def _transcribe_with_local_whisper(audio_path: str) -> Dict[str, Any]:
    # try whisperx then openai-whisper
    try:
        import whisperx  # type: ignore
        model = whisperx.load_model("small", device="cpu")
        result = model.transcribe(audio_path)
        segments = []
        for s in result.get("segments", []):
            segments.append({"start": float(s.get("start", 0.0)), "end": float(s.get("end", 0.0)), "duration": float(s.get("end", 0.0) - s.get("start", 0.0)), "text": s.get("text", "")})
        return {"text": result.get("text", ""), "segments": segments}
    except Exception:
        try:
            import whisper  # type: ignore
            model = whisper.load_model("small")
            res = model.transcribe(audio_path)
            segs = []
            for s in res.get("segments", []):
                segs.append({"start": float(s.get("start", 0.0)), "end": float(s.get("end", 0.0)), "duration": float(s.get("end", 0.0) - s.get("start", 0.0)), "text": s.get("text", "")})
            text = res.get("text", "")
            if not segs:
                segs = [{"start": 0.0, "end": 0.0, "duration": 0.0, "text": text}]
            return {"text": text, "segments": segs}
        except Exception as e:
            raise ImportError(f"Local whisper transcription failed or not installed: {e}")


def _transcribe_with_openai_api(audio_path: str) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise TranscriptError("OPENAI_API_KEY not configured in environment; cannot use OpenAI transcription.")
    import requests
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    try:
        with open(audio_path, "rb") as fh:
            files = {"file": ("audio.mp3", fh, "audio/mpeg")}
            data = {"model": "whisper-1"}
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=180)
        if resp.status_code != 200:
            raise TranscriptError(f"OpenAI transcription failed: {resp.status_code} {resp.text}")
        j = resp.json()
        text = j.get("text") or j.get("transcript") or ""
        segments = [{"start": 0.0, "end": 0.0, "duration": 0.0, "text": text}]
        return {"text": text, "segments": segments}
    except TranscriptError:
        raise
    except Exception as e:
        raise TranscriptError(f"OpenAI transcription error: {repr(e)}")


def run_asr_for_doc(doc_id: str, video_id: Optional[str] = None, cookies_path: Optional[str] = None) -> Dict[str, Any]:
    existing = _read_transcript_json_if_exists(doc_id)
    if existing:
        if existing.get("transcript"):
            return {
                "status": "already_transcribed",
                "doc_id": doc_id,
                "file_path": os.path.join(TRANSCRIPTS_DIR, f"{doc_id}.json"),
                "video_id": existing.get("video_id"),
                "message": "Transcript already present",
                "metadata": existing.get("metadata", {}),
                "transcript": existing.get("transcript", []),
            }
        video_id = video_id or existing.get("video_id")
        metadata = existing.get("metadata", {})
    else:
        if not video_id:
            raise TranscriptError("No existing doc found and no video_id supplied for ASR.")
        metadata = {}

    # Download audio
    try:
        audio_path = _download_audio_with_ytdlp(video_id, cookies_path=cookies_path)
    except TranscriptError as e:
        # save placeholder and raise so frontend can show helpful message
        payload = {
            "doc_id": doc_id,
            "source": "youtube",
            "video_id": video_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata,
            "transcript": [],
        }
        save_transcript_json(doc_id, payload)
        raise TranscriptError(str(e))

    # Try local whisper
    transcription_result = None
    local_err = None
    try:
        transcription_result = _transcribe_with_local_whisper(audio_path)
    except ImportError as ie:
        local_err = str(ie)
    except Exception as ex:
        local_err = f"Local whisper error: {repr(ex)}"

    # Fallback to OpenAI if local not available
    if transcription_result is None:
        if OPENAI_API_KEY:
            try:
                transcription_result = _transcribe_with_openai_api(audio_path)
            except Exception as ex:
                raise TranscriptError(f"ASR error (OpenAI fallback failed): {repr(ex)}; local_error={local_err}")
        else:
            payload = {
                "doc_id": doc_id,
                "source": "youtube",
                "video_id": video_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "metadata": metadata,
                "transcript": [],
            }
            save_transcript_json(doc_id, payload)
            raise TranscriptError(f"Local ASR unavailable ({local_err}). Set OPENAI_API_KEY to enable remote ASR fallback.")

    # Build segments
    segments = []
    for seg in transcription_result.get("segments", []):
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", 0.0))
        duration = float(seg.get("duration", end - start if end else 0.0))
        text = seg.get("text", "")
        segments.append({"start": start, "end": end, "duration": duration, "text": text})

    if not segments:
        text = transcription_result.get("text", "")
        segments = [{"start": 0.0, "end": 0.0, "duration": 0.0, "text": text}]

    payload_json = {
        "doc_id": doc_id,
        "source": "youtube",
        "video_id": video_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "metadata": metadata,
        "transcript": segments,
    }
    path = save_transcript_json(doc_id, payload_json)

    return {
        "status": "asr_completed",
        "doc_id": doc_id,
        "file_path": path,
        "video_id": video_id,
        "message": "ASR transcription complete.",
        "metadata": metadata,
        "transcript": segments,
    }
