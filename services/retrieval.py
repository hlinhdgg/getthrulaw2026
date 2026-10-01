"""Low-cost retrieval of potentially affected company document sections."""

from __future__ import annotations

import re
from typing import Any

from services.documents import load_directory


STOPWORDS = {
    "about", "after", "before", "from", "must", "shall", "that", "the",
    "their", "this", "with", "when", "where", "which", "will", "and",
    "for", "into", "only", "outside", "under", "over", "does", "doesn",
}


def _terms(text: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-zA-Z0-9]{3,}", text.lower())
        if term not in STOPWORDS
    }


def retrieve_affected_sections(
    query: str,
    directory: str,
    top_k: int = 8,
) -> list[dict[str, Any]]:
    """Return the highest-overlap document chunks for a regulatory query."""
    query_terms = _terms(query)
    scored: list[dict[str, Any]] = []

    for chunk in load_directory(directory):
        chunk_terms = _terms(chunk["text"])
        overlap = query_terms & chunk_terms
        if not overlap:
            continue
        score = len(overlap) / max(len(query_terms), 1)
        scored.append(
            {
                **chunk,
                "matched_terms": sorted(overlap),
                "retrieval_score": round(score, 3),
            }
        )

    return sorted(scored, key=lambda item: item["retrieval_score"], reverse=True)[:top_k]

