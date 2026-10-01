"""Transparent scoring helpers for impact and confidence."""

from __future__ import annotations


def score_impact(retrieval_score: float, matched_terms: int, relationship: str) -> int:
    base = retrieval_score * 70 + matched_terms * 6
    if relationship == "potential_conflict":
        base += 15
    elif relationship == "potentially_affected":
        base += 5
    return max(0, min(100, round(base)))


def score_confidence(retrieval_score: float, matched_terms: int) -> int:
    return max(0, min(100, round(retrieval_score * 65 + matched_terms * 8)))

