"""Extract structured regulatory changes from Gazette/legislation text."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


def _field(text: str, name: str) -> str | None:
    match = re.search(rf"^{re.escape(name)}:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else None


def local_extract(text: str, source_url: str | None = None) -> dict[str, Any]:
    """Extract the predictable fields used by the synthetic demo source."""
    summary = re.search(
        r"AMENDMENT SUMMARY\s*\n(.*?)(?=\n\s*NEW REQUIREMENT|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    requirement = re.search(
        r"NEW REQUIREMENT\s*\n(.*?)(?=\n\s*This file|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    return {
        "title": _field(text, "TITLE") or "Untitled regulatory update",
        "source": _field(text, "SOURCE") or "Singapore Government Gazette",
        "publication_date": _field(text, "PUBLICATION_DATE"),
        "effective_date": _field(text, "EFFECTIVE_DATE"),
        "change_summary": " ".join(summary.group(1).split()) if summary else "",
        "new_requirement": " ".join(requirement.group(1).split()) if requirement else "",
        "old_requirement": None,
        "affected_entities": [],
        "source_url": source_url,
        "extraction_method": "local",
    }


def ai_extract(text: str, source_url: str | None = None) -> dict[str, Any]:
    """Use OpenRouter's OpenAI-compatible Responses API."""
    from openai import OpenAI

    prompt_path = Path(__file__).parents[1] / "prompts" / "extract_change.txt"
    instructions = prompt_path.read_text(encoding="utf-8")
    client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        default_headers={
            "HTTP-Referer": "https://github.com/jiakai2002/getthrulaw",
            "X-Title": "getthrulaw",
        },
    )
    response = client.chat.completions.create(
        model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash-0731"),
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": f"SOURCE TEXT:\n{text}"},
        ],
        temperature=0,
    )
    result = json.loads(response.choices[0].message.content)
    result["source_url"] = source_url
    result["extraction_method"] = "openai"
    return result


def extract_change(path: str | Path, source_url: str | None = None) -> dict[str, Any]:
    """Extract a structured change, with a deterministic fallback."""
    file_path = Path(path)
    if file_path.suffix.lower() == ".pdf":
        from services.documents import load_document

        text = "\n".join(chunk.text for chunk in load_document(file_path))
    else:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    # Keep paid model usage opt-in. Local extraction is enough for the demo.
    if (
        os.getenv("USE_OPENROUTER", "false").lower() == "true"
        and os.getenv("OPENROUTER_API_KEY")
    ):
        try:
            return ai_extract(text, source_url)
        except Exception:
            # A source update should still be visible if the API is unavailable.
            pass
    return local_extract(text, source_url)
