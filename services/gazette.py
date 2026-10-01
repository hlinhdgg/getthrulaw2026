"""Best-effort scraper for the official Singapore Gazette listing page."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def scrape_latest_gazettes(source_url: str, limit: int = 20) -> list[dict[str, Any]]:
    response = requests.get(
        urljoin(source_url, "/gazettes/"),
        headers={"User-Agent": "getthrulaw/0.1 (regulatory research tool)"},
        timeout=20,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    updates: list[dict[str, Any]] = []
    seen: set[str] = set()

    for link in soup.select("a[href]"):
        href = urljoin(source_url, link.get("href", ""))
        title = " ".join(link.get_text(" ", strip=True).split())
        if not title or href in seen or href.rstrip("/") == source_url.rstrip("/"):
            continue
        if not ("gazette" in href.lower() or href.lower().endswith(".pdf")):
            continue
        seen.add(href)
        updates.append(
            {
                "id": href,
                "title": title,
                "link": href,
                "date": _find_date(link.parent.get_text(" ", strip=True)),
            }
        )
        if len(updates) >= limit:
            break
    return updates


def _find_date(text: str) -> str | None:
    match = re.search(r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b", text)
    return match.group(0) if match else None


def download_gazette(entry: dict[str, Any], destination: str | Path) -> Path:
    """Download one Gazette entry for local, evidence-linked analysis."""
    response = requests.get(
        entry["link"],
        headers={"User-Agent": "getthrulaw/0.1 (regulatory research tool)"},
        timeout=30,
    )
    response.raise_for_status()
    folder = Path(destination)
    folder.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", entry["title"]).strip("_")[:100]
    content_type = response.headers.get("content-type", "").lower()
    if "pdf" in content_type or entry["link"].lower().endswith(".pdf"):
        output = folder / f"gazette_{safe_name}.pdf"
        output.write_bytes(response.content)
    else:
        output = folder / f"gazette_{safe_name}.txt"
        text = BeautifulSoup(response.text, "html.parser").get_text("\n", strip=True)
        output.write_text(text, encoding="utf-8")
    return output


def load_seen(path: str | Path) -> set[str]:
    file_path = Path(path)
    if not file_path.exists():
        return set()
    return set(json.loads(file_path.read_text(encoding="utf-8")))


def save_seen(path: str | Path, values: set[str]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(sorted(values), indent=2), encoding="utf-8")
