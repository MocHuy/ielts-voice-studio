"""Parse ChatGPT IELTS feedback into speech-friendly sections."""
from __future__ import annotations

import re
from typing import Any

SECTION_MAP = {
    "original": "original", "corrected": "corrected", "better": "corrected",
    "explanation": "explanation", "detailed explanation": "explanation",
    "example": "example", "examples": "example", "natural examples": "example",
    "next question": "question", "question": "question",
    "estimated level": "meta", "vocabulary explanation": "explanation",
    "grammar explanation": "explanation",
}
HEADING_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(original|corrected|better|explanation|detailed explanation|"
    r"example|examples|natural examples|next question|question|estimated level|"
    r"vocabulary explanation|grammar explanation)\s*:?\s*(.*)$", re.I
)
SENTENCE_HEADING_RE = re.compile(r"^\s*(?:#{1,6}\s*)?sentence\s+\d+\s*:?\s*$", re.I)


def clean_markdown(text: str) -> str:
    """Remove visual/citation markup without damaging useful punctuation."""
    text = re.sub(r"```[\w-]*", "", text)
    text = text.replace("```", "")
    text = re.sub(r"\[writing(?:\s+block)?[^\]]*\]", "", text, flags=re.I)
    text = re.sub(r"\[(?:\d+|[a-z]+\d+|citation needed)\]", "", text, flags=re.I)
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"(?<!\w)[*_~`]{1,3}|[*_~`]{1,3}(?!\w)", "", text)
    text = re.sub(r"^\s*(?:[-*+]\s+|\d+[.)]\s+|>\s*)", "", text, flags=re.M)
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    return re.sub(r"[ \t]+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    """Split prose on natural sentence boundaries while preserving punctuation."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    # Protect common abbreviations and decimals.
    protected = re.sub(r"\b(Mr|Mrs|Ms|Dr|Prof|e\.g|i\.e|etc)\.", lambda m: m.group(0).replace(".", "∯"), text, flags=re.I)
    parts = re.split(r"(?<=[.!?])(?:[\"']+)?\s+(?=[\"']?[A-Z0-9])", protected)
    result = [p.replace("∯", ".").strip() for p in parts if p.strip()]
    return result


def parse_text(raw_text: str) -> list[dict[str, Any]]:
    if not raw_text or not raw_text.strip():
        return []
    cleaned = clean_markdown(raw_text)
    cards: list[dict[str, Any]] = []
    current_type = "example"
    buffer: list[str] = []
    group = 0

    def flush() -> None:
        nonlocal buffer
        body = " ".join(x.strip() for x in buffer if x.strip()).strip()
        for sentence in split_sentences(body):
            cards.append({"id": len(cards), "type": current_type, "text": sentence, "group": group})
        buffer = []

    for line in cleaned.splitlines():
        line = line.strip()
        if not line:
            flush()
            continue
        if SENTENCE_HEADING_RE.match(line):
            flush(); group += 1
            continue
        match = HEADING_RE.match(line)
        if match:
            flush()
            current_type = SECTION_MAP[match.group(1).lower()]
            if match.group(2):
                buffer.append(match.group(2))
        else:
            buffer.append(line)
    flush()
    return cards


def select_cards(cards: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    filters = {
        "corrected": {"corrected"}, "original_corrected": {"original", "corrected"},
        "explanations": {"explanation"},
    }
    return [c for c in cards if c.get("type") in filters[mode]] if mode in filters else cards
