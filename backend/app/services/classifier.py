from __future__ import annotations

import re

from app.schemas import PhraseClassification


QUESTION_PREFIXES = (
    "was",
    "warum",
    "wie",
    "wann",
    "wer",
    "welche",
    "what",
    "why",
    "how",
)

IMPORTANT_WORDS = ("wichtig", "prufung", "prüfung", "merken", "achtung")
DEADLINE_WORDS = ("bis", "morgen", "nächste woche", "next week", "deadline")
DEFINITION_WORDS = ("ist", "bedeutet", "definition", "heisst", "heißt")
TASK_WORDS = ("mache", "mach", "todo", "aufgabe", "send", "submit")
EXAMPLE_WORDS = ("beispiel", "for example", "zum beispiel")
EXAM_HINT_WORDS = ("prüfung", "exam", "test", "ihk", "ap")


def classify_phrase(text: str) -> PhraseClassification:
    normalized = normalize_text(text)

    if is_question(normalized, text):
        return PhraseClassification(
            phrase_type="question",
            priority="high",
            show_answer=True,
        )

    if contains_any(normalized, EXAM_HINT_WORDS):
        return PhraseClassification(
            phrase_type="exam_hint",
            priority="high",
            show_answer=False,
        )

    if contains_any(normalized, IMPORTANT_WORDS):
        return PhraseClassification(
            phrase_type="important",
            priority="high",
            show_answer=False,
        )

    if contains_any(normalized, DEADLINE_WORDS):
        return PhraseClassification(
            phrase_type="deadline",
            priority="high",
            show_answer=False,
        )

    if contains_any(normalized, TASK_WORDS):
        return PhraseClassification(
            phrase_type="task",
            priority="medium",
            show_answer=False,
        )

    if contains_any(normalized, EXAMPLE_WORDS):
        return PhraseClassification(
            phrase_type="example",
            priority="medium",
            show_answer=False,
        )

    if looks_like_definition(normalized):
        return PhraseClassification(
            phrase_type="definition",
            priority="medium",
            show_answer=False,
        )

    return PhraseClassification(
        phrase_type="normal",
        priority="low",
        show_answer=False,
    )


def is_question(normalized: str, original: str) -> bool:
    if "?" in original:
        return True
    return normalized.startswith(QUESTION_PREFIXES)


def normalize_text(text: str) -> str:
    compact = re.sub(r"\s+", " ", text.strip().lower())
    return compact


def contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def looks_like_definition(text: str) -> bool:
    return (
        len(text.split()) >= 3
        and contains_any(text, DEFINITION_WORDS)
        and not text.startswith(QUESTION_PREFIXES)
    )
