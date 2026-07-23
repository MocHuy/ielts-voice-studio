from pathlib import Path

from services.audio_service import audio_filename, pitch_to_edge, rate_to_edge
from services.lesson_service import LessonStore


def test_audio_filename_is_safe() -> None:
    name = audio_filename("My IELTS: lesson / one", "wav")
    assert name.endswith("_My-IELTS-lesson-one.wav")
    assert "/" not in name and ":" not in name


def test_audio_controls() -> None:
    assert rate_to_edge(.6) == "-40%"
    assert rate_to_edge(1.5) == "+50%"
    assert pitch_to_edge(1) == "+0Hz"


def test_lesson_save_load_update_delete(tmp_path: Path) -> None:
    store = LessonStore(tmp_path / "lessons.db")
    payload = {"title": "Practice", "parsed_sentences": [{"text": "Hello."}], "difficult_sentences": []}
    saved = store.save(payload)
    assert store.get(saved["id"])["title"] == "Practice"
    payload["title"] = "Renamed"
    assert store.save(payload, saved["id"])["title"] == "Renamed"
    assert len(store.list("name")) == 1
    assert store.delete(saved["id"])
    assert store.get(saved["id"]) is None
