from app.services.classifier import classify_phrase


def test_detects_question() -> None:
    result = classify_phrase("Was ist RAID 1?")
    assert result.phrase_type == "question"
    assert result.priority == "high"
    assert result.show_answer is True


def test_detects_deadline() -> None:
    result = classify_phrase("Bitte bis morgen das Blatt abgeben")
    assert result.phrase_type == "deadline"
    assert result.priority == "high"


def test_detects_definition() -> None:
    result = classify_phrase("RAID 1 ist eine Spiegelung von Daten")
    assert result.phrase_type == "definition"
    assert result.priority == "medium"
