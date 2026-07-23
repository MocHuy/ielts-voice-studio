from services.text_parser import clean_markdown, parse_text, split_sentences


def test_sentence_splitting_preserves_punctuation() -> None:
    assert split_sentences("This is one. Is this two? Yes!") == ["This is one.", "Is this two?", "Yes!"]


def test_detects_original_and_corrected() -> None:
    cards = parse_text("Sentence 1\nOriginal: I goes home.\nCorrected: I go home.\nExplanation: Use go.")
    assert [c["type"] for c in cards] == ["original", "corrected", "explanation"]
    assert cards[1]["text"] == "I go home."


def test_markdown_urls_and_citations_removed() -> None:
    cleaned = clean_markdown("- **Correct** [1] https://example.com `word`")
    assert cleaned == "Correct word"


def test_empty_input() -> None:
    assert parse_text("") == []
    assert split_sentences("   ") == []


def test_long_input() -> None:
    cards = parse_text("Corrected:\n" + "This is a useful sentence. " * 1000)
    assert len(cards) == 1000


def test_special_characters() -> None:
    cards = parse_text('Corrected: “Don\'t” costs £5 — okay?')
    assert cards[0]["text"] == '"Don\'t" costs £5 — okay?'
