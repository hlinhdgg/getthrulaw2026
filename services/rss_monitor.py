"""Small, deduplicated RSS monitor for official regulatory sources."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import feedparser


def fetch_feed(feed_url: str) -> list[dict[str, Any]]:
    feed = feedparser.parse(feed_url)
    return [
        {
            "id": entry.get("id") or entry.get("link") or entry.get("title"),
            "title": entry.get("title", "Untitled update"),
            "link": entry.get("link"),
            "published": entry.get("published") or entry.get("updated"),
        }
        for entry in feed.entries
    ]


def load_seen(path: str | Path) -> set[str]:
    file_path = Path(path)
    if not file_path.exists():
        return set()
    return set(json.loads(file_path.read_text(encoding="utf-8")))


def save_seen(path: str | Path, seen: set[str]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(sorted(seen), indent=2), encoding="utf-8")


def check_for_updates(feed_url: str, seen_path: str | Path) -> dict[str, Any]:
    """Return unseen entries and persist their IDs."""
    if not feed_url:
        return {"status": "not_configured", "updates": []}

    entries = fetch_feed(feed_url)
    seen = load_seen(seen_path)
    updates = [entry for entry in entries if entry["id"] not in seen]
    seen.update(entry["id"] for entry in entries if entry["id"])
    save_seen(seen_path, seen)
    return {
        "status": "ok",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "updates": updates,
    }

