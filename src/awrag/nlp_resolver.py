from __future__ import annotations

import re
from collections import Counter
from typing import Any


RESOLVER_ID = "awrag_deterministic_nlp_resolver@1"
SENTENCE_RE = re.compile(r"[^.!?\n]+(?:[.!?]|$)")


def resolve_answer(question: str, answer_packet: dict[str, Any]) -> dict[str, Any]:
    """Convert locked AWRAG evidence locations into a cited readable answer.

    This resolver is intentionally small. It does not search, score, call a
    model, or invent citations. It only selects readable snippets from the
    locations that AWRAG already admitted into the packet.
    """
    locations = list(answer_packet.get("locations") or [])
    if not locations:
        return {
            "schema": "awrag_nlp_answer@1",
            "resolver": RESOLVER_ID,
            "status": "not_enough_information",
            "text": "Not enough information is available in the admitted dataset to answer this question.",
            "citations": [],
            "model_used": "none",
            "model_may_search": False,
            "citation_source": "awrag_locked_packet",
        }

    question_terms = Counter(_terms(question))
    cited_sentences: list[str] = []
    citations: list[str] = []
    for location in locations[:3]:
        citation = str(location.get("citation") or "").strip()
        sentence = best_sentence(str(location.get("text") or ""), question_terms)
        if not sentence:
            continue
        if citation and citation not in sentence:
            sentence = f"{sentence} {citation}"
        cited_sentences.append(sentence)
        if citation:
            citations.append(citation)

    if not cited_sentences:
        return {
            "schema": "awrag_nlp_answer@1",
            "resolver": RESOLVER_ID,
            "status": "not_enough_information",
            "text": "AWRAG found locations, but the admitted text could not be converted into a supported answer.",
            "citations": citations,
            "model_used": "none",
            "model_may_search": False,
            "citation_source": "awrag_locked_packet",
        }

    return {
        "schema": "awrag_nlp_answer@1",
        "resolver": RESOLVER_ID,
        "status": "answered_from_awrag_locations",
        "text": " ".join(cited_sentences),
        "citations": citations,
        "model_used": "none",
        "model_may_search": False,
        "citation_source": "awrag_locked_packet",
    }


def best_sentence(text: str, question_terms: Counter[str]) -> str:
    candidates = [clean_sentence(match.group(0)) for match in SENTENCE_RE.finditer(text)]
    candidates = [candidate for candidate in candidates if candidate]
    if not candidates:
        return clean_sentence(text)
    ranked = sorted(
        candidates,
        key=lambda sentence: (-sentence_score(sentence, question_terms), len(sentence), sentence),
    )
    return ranked[0]


def sentence_score(sentence: str, question_terms: Counter[str]) -> int:
    terms = Counter(_terms(sentence))
    return sum(min(count, terms.get(term, 0)) for term, count in question_terms.items())


def clean_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip(" \t\r\n")


def _terms(text: str) -> list[str]:
    return [match.group(0).casefold() for match in re.finditer(r"[A-Za-z0-9]+", text)]
