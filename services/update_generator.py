"""Generate reviewable proposed updates without editing source documents."""

from __future__ import annotations

from typing import Any


def suggest_update(change: dict[str, Any], finding: dict[str, Any]) -> dict[str, Any]:
    old_text = finding.get("company_quote", "").strip()
    new_requirement = change.get("new_requirement", "").strip()
    proposed = old_text

    if "five years" in proposed.lower() and "seven years" in new_requirement.lower():
        proposed = proposed.replace("five years", "seven years")
    elif old_text:
        proposed = (
            old_text
            + "\n\n[PROPOSED ADDITION] "
            + new_requirement
        )

    return {
        "document": finding.get("document"),
        "section": finding.get("section"),
        "old_text": old_text,
        "proposed_text": proposed,
        "reason": "Update proposed because the monitored regulatory requirement changed.",
        "source_quote": new_requirement,
        "confidence": finding.get("confidence", "low"),
        "status": "pending_review",
    }


def suggest_updates(
    change: dict[str, Any],
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [suggest_update(change, finding) for finding in findings]

