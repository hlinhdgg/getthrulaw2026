"""Build and inspect regulation-to-asset dependency relationships."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_dependencies(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    return json.loads(file_path.read_text(encoding="utf-8"))


def downstream_assets(
    root: str,
    dependencies: list[dict[str, Any]],
) -> list[str]:
    """Return all direct and indirect dependants of a root node."""
    found: set[str] = set()
    frontier = [root]
    while frontier:
        current = frontier.pop()
        for edge in dependencies:
            if edge["from"] == current and edge["to"] not in found:
                found.add(edge["to"])
                frontier.append(edge["to"])
    return sorted(found)

