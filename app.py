from __future__ import annotations

import asyncio
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from services.audio_service import audio_filename
from services.lesson_service import LessonStore
from services.text_parser import parse_text, select_cards
from services.tts_service import EdgeTTSProvider

BASE = Path(__file__).resolve().parent
AUDIO_DIR = BASE / "generated_audio"
AUDIO_DIR.mkdir(exist_ok=True)
store = LessonStore(BASE / "storage" / "lessons.db")
tts = EdgeTTSProvider()
app = FastAPI(title="IELTS Voice Studio", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


class ParseRequest(BaseModel):
    text: str = Field(max_length=100_000)


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
    voice: str = "en-GB-SoniaNeural"
    speed: float = Field(1.0, ge=.6, le=1.5)
    pitch: float = Field(1.0, ge=.5, le=1.5)
    title: str = "sentence"

    @field_validator("voice")
    @classmethod
    def english_voice(cls, value: str) -> str:
        if not value.startswith(("en-GB-", "en-US-")): raise ValueError("Choose a supported English voice")
        return value


class ExportRequest(SpeechRequest):
    texts: list[str] = Field(default_factory=list, max_length=500)
    pause_ms: int = Field(700, ge=0, le=5000)
    format: str = "mp3"


class LessonPayload(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    raw_text: str = Field(default="", max_length=100_000)
    parsed_sentences: list[dict[str, Any]] = Field(default_factory=list)
    voice: str = "en-GB-SoniaNeural"
    speed: float = 1.0
    practised_sentences: list[int] = Field(default_factory=list)
    difficult_sentences: list[int] = Field(default_factory=list)
    difficulty: dict[str, str] = Field(default_factory=dict)
    notes: str = Field(default="", max_length=20_000)
    last_sentence: int = 0


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(BASE / "templates" / "index.html")


@app.post("/api/parse")
async def parse(request: ParseRequest) -> dict[str, Any]:
    if not request.text.strip(): raise HTTPException(422, "Paste some English text first.")
    return {"cards": parse_text(request.text)}


@app.get("/api/voices")
async def voices() -> dict[str, Any]:
    try: return {"engine": "edge", "voices": await asyncio.wait_for(tts.voices(), 12)}
    except Exception as exc: return {"engine": "browser", "voices": [], "warning": f"Online voices unavailable: {exc}"}


@app.post("/api/speech")
async def speech(request: SpeechRequest) -> FileResponse:
    path = AUDIO_DIR / f"{uuid.uuid4().hex}.mp3"
    try: await asyncio.wait_for(tts.generate(request.text.strip(), request.voice, request.speed, request.pitch, path), 45)
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(503, f"Edge TTS failed. Use Browser Voice fallback. ({exc})") from exc
    return FileResponse(path, media_type="audio/mpeg", filename=audio_filename(request.title))


@app.post("/api/export")
async def export_audio(request: ExportRequest) -> FileResponse:
    texts = [x.strip() for x in (request.texts or [request.text]) if x.strip()]
    if not texts: raise HTTPException(422, "Nothing to export.")
    ffmpeg = shutil.which("ffmpeg")
    if len(texts) == 1 or not ffmpeg:
        path = AUDIO_DIR / f"{uuid.uuid4().hex}.mp3"
        await tts.generate(" ".join(texts), request.voice, request.speed, request.pitch, path)
        return FileResponse(path, "audio/mpeg", filename=audio_filename(request.title, "mp3"))
    job_dir = Path(tempfile.mkdtemp(prefix="ielts_tts_", dir=AUDIO_DIR))
    try:
        clips: list[Path] = []
        for index, text in enumerate(texts):
            clip = job_dir / f"{index:04}.mp3"; await tts.generate(text, request.voice, request.speed, request.pitch, clip); clips.append(clip)
        target_ext = "wav" if request.format == "wav" else "mp3"
        target = AUDIO_DIR / f"{uuid.uuid4().hex}.{target_ext}"
        inputs: list[str] = []
        for clip in clips: inputs += ["-i", str(clip)]
        delay = request.pause_ms / 1000
        filters = []
        for i in range(len(clips)):
            filters.append(f"[{i}:a]apad=pad_dur={delay}[a{i}]")
        filters.append("".join(f"[a{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=0:a=1[out]")
        subprocess.run([ffmpeg, "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", str(target)], check=True, capture_output=True)
        return FileResponse(target, "audio/wav" if target_ext == "wav" else "audio/mpeg", filename=audio_filename(request.title, target_ext))
    finally: shutil.rmtree(job_dir, ignore_errors=True)


@app.get("/api/lessons")
async def lessons(search: str = Query("", max_length=120), difficult: bool = False) -> list[dict[str, Any]]:
    return store.list(search, difficult)


@app.get("/api/lessons/{lesson_id}")
async def get_lesson(lesson_id: int) -> dict[str, Any]:
    lesson = store.get(lesson_id)
    if not lesson: raise HTTPException(404, "Lesson not found")
    return lesson


@app.post("/api/lessons", status_code=201)
async def save_lesson(payload: LessonPayload) -> dict[str, Any]: return store.save(payload.model_dump())


@app.put("/api/lessons/{lesson_id}")
async def update_lesson(lesson_id: int, payload: LessonPayload) -> dict[str, Any]:
    try: return store.save(payload.model_dump(), lesson_id)
    except KeyError: raise HTTPException(404, "Lesson not found")


@app.delete("/api/lessons/{lesson_id}", status_code=204)
async def delete_lesson(lesson_id: int) -> None:
    if not store.delete(lesson_id): raise HTTPException(404, "Lesson not found")


@app.get("/health")
async def health() -> dict[str, str]: return {"status": "ok"}
