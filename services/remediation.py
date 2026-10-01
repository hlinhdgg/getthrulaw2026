"""Persist human review decisions and remediation tasks."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_tasks(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    return json.loads(file_path.read_text(encoding="utf-8"))


def save_tasks(path: str | Path, tasks: list[dict[str, Any]]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


def record_decision(
    path: str | Path,
    proposal: dict[str, Any],
    decision: str,
) -> list[dict[str, Any]]:
    tasks = load_tasks(path)
    task = {
        "document": proposal.get("document"),
        "section": proposal.get("section"),
        "decision": decision,
        "status": "pending_review" if decision == "escalated" else decision,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "reason": proposal.get("reason"),
        "old_text": proposal.get("old_text"),
        "proposed_text": proposal.get("proposed_text"),
        "source_quote": proposal.get("source_quote"),
        "confidence": proposal.get("confidence"),
    }
    tasks = [item for item in tasks if item.get("document") != task["document"]]
    tasks.append(task)
    save_tasks(path, tasks)
    return tasks
