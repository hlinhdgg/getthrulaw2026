"""Low-cost local relevance filter for regulatory updates."""

from __future__ import annotations

import re
from typing import Any


def classify_relevance(
    update: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Classify an update using transparent keyword matching."""
    text = " ".join(
        str(update.get(key, ""))
        for key in ("title", "summary", "description", "topic")
    ).lower()
    topics = [str(topic).lower() for topic in profile.get("topics", [])]
    keywords = [str(keyword).lower() for keyword in profile.get("keywords", [])]
    matches = sorted(
        {
            term
            for term in topics + keywords
            if term and re.search(rf"\b{re.escape(term)}\b", text)
        }
    )

    if len(matches) >= 2:
        classification = "relevant"
    elif matches:
        classification = "possibly_relevant"
    else:
        classification = "irrelevant"

    return {
        **update,
        "classification": classification,
        "matched_topics": matches,
        "reason": (
            f"Matched: {', '.join(matches)}" if matches else "No monitored topics matched"
        ),
    }

