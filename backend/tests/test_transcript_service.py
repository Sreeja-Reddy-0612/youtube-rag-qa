# File: backend/tests/test_transcript_service.py
# Run this with: pytest -q

import os
from backend.app.services.transcript import extract_video_id, ingest_youtube_transcript

def test_extract_video_id_from_watch_url():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    vid = extract_video_id(url)
    assert vid == "dQw4w9WgXcQ"

def test_ingest_invalid_url():
    res = ingest_youtube_transcript("not a url")
    assert res["status"] == "error"

# Note: for a live caption test, you need network and a video with captions.
# This test is illustrative and may be skipped in CI or marked as integration test.
