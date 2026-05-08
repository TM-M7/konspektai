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
    "welcher",
    "wieso",
    "wo",
    "what",
    "why",
    "how",
    "when",
    "where",
    "which",
)

IMPORTANT_PATTERNS = (
    r"\bwichtig\b",
    r"\bachtung\b",
    r"\bmerken\b",
    r"\bnotier(?:en|t)?\b",
    r"\bremember\b",
    r"\bkey point\b",
)
EXPLICIT_DEADLINE_PATTERNS = (
    r"\bbis\s+\d{1,2}(?::\d{2})?\s*uhr\b",
    r"\bbis\b",
    r"\bnachste woche\b",
    r"\bnachsten montag\b",
    r"\bdeadline\b",
    r"\bnext week\b",
    r"\bdue\b",
)
SOFT_DEADLINE_PATTERNS = (
    r"\bmorgen\b",
    r"\bheute\b",
    r"\btomorrow\b",
)
DEFINITION_PATTERNS = (
    r"\bist\b",
    r"\bsind\b",
    r"\bbedeutet\b",
    r"\bdefinition\b",
    r"\bheisst\b",
    r"\bmeans\b",
    r"\brefers to\b",
)
TASK_PATTERNS = (
    r"\baufgabe\b",
    r"\bhausaufgabe\b",
    r"\bmacht\b",
    r"\bmachen\b",
    r"\babgeben\b",
    r"\bsenden\b",
    r"\bsubmit\b",
    r"\bsend\b",
    r"\bcomplete\b",
    r"\btodo\b",
)
EXAMPLE_PATTERNS = (
    r"\bbeispiel\b",
    r"\bzum beispiel\b",
    r"\bfor example\b",
    r"\bexample\b",
)
EXAM_HINT_PATTERNS = (
    r"\bprufung\b",
    r"\bihk\b",
    r"\bap\b",
    r"\bexam\b",
    r"\btest\b",
    r"\bklausur\b",
)


def classify_phrase(text: str) -> PhraseClassification:
    normalized = normalize_text(text)

    if is_question(normalized, text):
        return PhraseClassification(
            phrase_type="question",
            priority="high",
            show_answer=True,
        )

    if matches_any(normalized, EXAM_HINT_PATTERNS):
        return PhraseClassification(
            phrase_type="exam_hint",
            priority="high",
            show_answer=False,
        )

    if matches_any(normalized, IMPORTANT_PATTERNS):
        return PhraseClassification(
            phrase_type="important",
            priority="high",
            show_answer=False,
        )

    if matches_any(normalized, TASK_PATTERNS):
        if matches_any(normalized, EXPLICIT_DEADLINE_PATTERNS):
            return PhraseClassification(
                phrase_type="deadline",
                priority="high",
                show_answer=False,
            )
        return PhraseClassification(
            phrase_type="task",
            priority="medium",
            show_answer=False,
        )

    if matches_any(normalized, EXPLICIT_DEADLINE_PATTERNS + SOFT_DEADLINE_PATTERNS):
        return PhraseClassification(
            phrase_type="deadline",
            priority="high",
            show_answer=False,
        )

    if matches_any(normalized, EXAMPLE_PATTERNS):
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
    if normalized.startswith(QUESTION_PREFIXES):
        return True
    return bool(re.match(r"^(can|could|should|do|does|is|are)\b", normalized))


def normalize_text(text: str) -> str:
    compact = re.sub(r"\s+", " ", text.strip().lower())
    replacements = {
        "ä": "a",
        "ö": "o",
        "ü": "u",
        "ß": "ss",
    }
    for source, target in replacements.items():
        compact = compact.replace(source, target)
    return compact


def matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def looks_like_definition(text: str) -> bool:
    return (
        len(text.split()) >= 3
        and matches_any(text, DEFINITION_PATTERNS)
        and not text.startswith(QUESTION_PREFIXES)
    )
