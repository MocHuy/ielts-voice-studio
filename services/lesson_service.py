"""SQLite persistence for local IELTS lessons."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class LessonStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL, data TEXT NOT NULL)""")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def list(self, search: str = "", difficult: bool = False) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM lessons WHERE title LIKE ? ORDER BY updated_at DESC", (f"%{search}%",)).fetchall()
        lessons = [self._decode(row) for row in rows]
        return [x for x in lessons if x.get("difficult_sentences")] if difficult else lessons

    def get(self, lesson_id: int) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,)).fetchone()
        return self._decode(row) if row else None

    def save(self, payload: dict[str, Any], lesson_id: int | None = None) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        title = str(payload.get("title", "Untitled lesson")).strip()[:120] or "Untitled lesson"
        payload["title"] = title
        with self._connect() as db:
            if lesson_id:
                found = db.execute("SELECT created_at FROM lessons WHERE id=?", (lesson_id,)).fetchone()
                if not found: raise KeyError(lesson_id)
                db.execute("UPDATE lessons SET title=?, updated_at=?, data=? WHERE id=?", (title, now, json.dumps(payload), lesson_id))
            else:
                cur = db.execute("INSERT INTO lessons(title,created_at,updated_at,data) VALUES(?,?,?,?)", (title, now, now, json.dumps(payload)))
                lesson_id = int(cur.lastrowid)
        return self.get(lesson_id)  # type: ignore[arg-type,return-value]

    def delete(self, lesson_id: int) -> bool:
        with self._connect() as db:
            return db.execute("DELETE FROM lessons WHERE id=?", (lesson_id,)).rowcount > 0

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        data = json.loads(row["data"])
        data.update(id=row["id"], created_at=row["created_at"], updated_at=row["updated_at"])
        return data
