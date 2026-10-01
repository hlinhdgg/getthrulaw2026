"""Load company documents into searchable, evidence-linked text chunks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class DocumentChunk:
    document: str
    path: str
    text: str
    page: int | None = None
    section: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _split_text(
    text: str,
    document: str,
    path: str,
    page: int | None = None,
    max_chars: int = 1800,
) -> list[DocumentChunk]:
    """Split long text while retaining its source location."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[DocumentChunk] = []
    current: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        if current and current_length + len(paragraph) > max_chars:
            chunks.append(
                DocumentChunk(document, path, "\n".join(current), page=page)
            )
            current = []
            current_length = 0
        current.append(paragraph)
        current_length += len(paragraph)

    if current:
        chunks.append(DocumentChunk(document, path, "\n".join(current), page=page))
    return chunks


def load_txt(path: Path) -> list[DocumentChunk]:
    text = path.read_text(encoding="utf-8")
    return _split_text(text, path.name, str(path))


def load_pdf(path: Path) -> list[DocumentChunk]:
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError("Install PyMuPDF to load PDF files.") from exc

    chunks: list[DocumentChunk] = []
    with fitz.open(path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            chunks.extend(
                _split_text(
                    page.get_text("text"),
                    path.name,
                    str(path),
                    page=page_number,
                )
            )
    return chunks


def load_docx(path: Path) -> list[DocumentChunk]:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("Install python-docx to load DOCX files.") from exc

    document = Document(path)
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    return _split_text(text, path.name, str(path))


def load_document(path: str | Path) -> list[DocumentChunk]:
    """Load one supported document and return evidence-linked chunks."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(file_path)

    suffix = file_path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return load_txt(file_path)
    if suffix == ".pdf":
        return load_pdf(file_path)
    if suffix == ".docx":
        return load_docx(file_path)
    raise ValueError(f"Unsupported document type: {suffix}")


def load_directory(directory: str | Path) -> list[dict[str, Any]]:
    """Load all supported files in a directory as JSON-ready dictionaries."""
    directory_path = Path(directory)
    chunks: list[dict[str, Any]] = []
    for path in sorted(directory_path.iterdir()):
        if path.is_file() and path.suffix.lower() in {".txt", ".md", ".pdf", ".docx"}:
            chunks.extend(chunk.to_dict() for chunk in load_document(path))
    return chunks

