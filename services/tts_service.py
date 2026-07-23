"""Swappable TTS provider interface and Microsoft Edge implementation."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

import edge_tts

from .audio_service import pitch_to_edge, rate_to_edge


class TTSProvider(Protocol):
    async def voices(self) -> list[dict[str, Any]]: ...
    async def generate(self, text: str, voice: str, speed: float, pitch: float, output: Path) -> None: ...


class EdgeTTSProvider:
    async def voices(self) -> list[dict[str, Any]]:
        voices = await edge_tts.list_voices()
        return [{"name": v["ShortName"], "display_name": v.get("FriendlyName", v["ShortName"]),
                 "locale": v["Locale"], "gender": v.get("Gender", "")}
                for v in voices if v["Locale"] in {"en-GB", "en-US"}]

    async def generate(self, text: str, voice: str, speed: float, pitch: float, output: Path) -> None:
        communicate = edge_tts.Communicate(text, voice, rate=rate_to_edge(speed), pitch=pitch_to_edge(pitch))
        await communicate.save(str(output))
