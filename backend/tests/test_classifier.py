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


def test_detects_exam_hint() -> None:
    result = classify_phrase("Das kommt oft in der IHK Prufung dran")
    assert result.phrase_type == "exam_hint"
    assert result.priority == "high"


def test_detects_task() -> None:
    result = classify_phrase("Bitte die Hausaufgabe im Portal senden")
    assert result.phrase_type == "task"
    assert result.priority == "medium"


def test_prefers_task_over_soft_deadline() -> None:
    result = classify_phrase("Macht die Hausaufgabe und sendet die Losung morgen")
    assert result.phrase_type == "task"
    assert result.priority == "medium"


def test_detects_important_before_definition() -> None:
    result = classify_phrase("Wichtig: DNS bedeutet Domain Name System")
    assert result.phrase_type == "important"
    assert result.priority == "high"
