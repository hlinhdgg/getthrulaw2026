"""Compare a regulatory change with retrieved company document sections."""

from __future__ import annotations

import re
import json
import os
from typing import Any

from utils.scoring import score_confidence, score_impact

def _terms(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9]{4,}", text.lower()))


def analyze_impact(
    change: dict[str, Any],
    section: dict[str, Any],
) -> dict[str, Any]:
    """Produce a transparent, local impact finding from two cited passages."""
    legal_text = " ".join(
        [change.get("change_summary", ""), change.get("new_requirement", "")]
    )
    legal_terms = _terms(legal_text)
    company_terms = _terms(section.get("text", ""))
    matched_terms = legal_terms & company_terms
    retrieval_score = float(section.get("retrieval_score", 0))

    if retrieval_score >= 0.35 and len(matched_terms) >= 3:
        relationship = "potential_conflict"
        severity = "high"
        confidence = "high"
        recommendation = "Review this section against the new requirement and propose an amendment."
    elif retrieval_score >= 0.15 or len(matched_terms) >= 2:
        relationship = "potentially_affected"
        severity = "medium"
        confidence = "medium"
        recommendation = "Ask the document owner to confirm whether this section remains accurate."
    else:
        relationship = "review"
        severity = "low"
        confidence = "low"
        recommendation = "Escalate for human review if this process handles the affected activity."

    impact_score = score_impact(retrieval_score, len(matched_terms), relationship)
    confidence_score = score_confidence(retrieval_score, len(matched_terms))
    return {
        "document": section["document"],
        "path": section["path"],
        "page": section.get("page"),
        "section": section.get("section"),
        "relationship": relationship,
        "severity": severity,
        "confidence": confidence,
        "impact_score": impact_score,
        "confidence_score": confidence_score,
        "legal_quote": change.get("new_requirement", ""),
        "company_quote": section.get("text", ""),
        "matched_terms": sorted(matched_terms),
        "explanation": (
            f"The company section overlaps with the changed requirement on "
            f"{', '.join(sorted(matched_terms)) or 'related subject matter'}."
        ),
        "recommended_action": recommendation,
        "requires_lawyer": relationship != "aligned",
    }


def ai_analyze_impact(change: dict[str, Any], section: dict[str, Any]) -> dict[str, Any]:
    """Optional OpenRouter analysis for a deliberately selected finding."""
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/jiakai2002/getthrulaw",
            "X-Title": "getthrulaw",
        },
    )
    prompt = (
        "Return JSON with keys relationship, severity, confidence, impact_score, "
        "explanation, recommended_action, requires_lawyer. Use only the evidence.\n\n"
        f"LEGAL REQUIREMENT:\n{change.get('new_requirement', '')}\n\n"
        f"COMPANY PASSAGE:\n{section.get('text', '')}"
    )
    response = client.chat.completions.create(
        model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash-0731"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    result = json.loads(response.choices[0].message.content)
    return {
        **analyze_impact(change, section),
        **result,
        "document": section["document"],
        "path": section["path"],
        "page": section.get("page"),
        "legal_quote": change.get("new_requirement", ""),
        "company_quote": section.get("text", ""),
    }


def analyze_all(
    change: dict[str, Any],
    sections: list[dict[str, Any]],
    use_ai: bool = False,
) -> list[dict[str, Any]]:
    if (
        use_ai
        and os.getenv("USE_OPENROUTER", "false").lower() == "true"
        and os.getenv("OPENROUTER_API_KEY")
    ):
        return [ai_analyze_impact(change, section) for section in sections]
    return [analyze_impact(change, section) for section in sections]
