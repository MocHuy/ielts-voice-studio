from __future__ import annotations

import re
from datetime import datetime


def audio_filename(title: str, extension: str = "mp3") -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", title.strip()).strip("-")[:60] or "ielts-lesson"
    ext = extension.lower() if extension.lower() in {"mp3", "wav"} else "mp3"
    return f"{datetime.now():%Y-%m-%d}_{safe}.{ext}"


def rate_to_edge(speed: float) -> str:
    return f"{round((max(.6, min(1.5, speed)) - 1) * 100):+d}%"


def pitch_to_edge(pitch: float) -> str:
    return f"{round((max(.5, min(1.5, pitch)) - 1) * 50):+d}Hz"
