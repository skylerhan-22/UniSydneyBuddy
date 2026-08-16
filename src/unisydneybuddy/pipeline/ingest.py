"""Local-first document ingestion with traceable source chunks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import re
import subprocess
from typing import Literal


SourceType = Literal[
    "unit_outline",
    "module",
    "lecture",
    "workshop",
    "assignment",
    "rubric",
    "announcement",
    "email",
    "other",
]


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    source_id: str
    index: int
    heading: str | None
    text: str


@dataclass(frozen=True)
class SourceDocument:
    id: str
    title: str
    path: str
    source_type: SourceType
    language: str
    is_private: bool
    sha256: str
    chunks: tuple[DocumentChunk, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def _read_text(path: Path) -> str:
    if path.suffix.lower() in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")

    if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
        script = Path(__file__).resolve().parents[3] / "scripts" / "ocr_image.swift"
        result = subprocess.run(
            ["/usr/bin/swift", "-module-cache-path", "/private/tmp/unisydneybuddy-swift-cache", str(script), str(path)],
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Could not read text from {path.name}: {result.stderr.strip()}")
        return result.stdout

    try:
        from markitdown import MarkItDown
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            f"{path.suffix or 'This file type'} needs MarkItDown. "
            "Install the project dependencies before importing PDF, PPTX or DOCX files."
        ) from exc

    result = MarkItDown().convert(str(path))
    return result.text_content


def classify_document(title: str, text: str) -> SourceType:
    sample = f"{title}\n{text[:3000]}".lower()
    rules: list[tuple[SourceType, tuple[str, ...]]] = [
        ("rubric", ("rubric", "marking criteria", "grading criteria")),
        ("assignment", ("assignment", "assessment task", "due date", "worth:")),
        ("unit_outline", ("unit outline", "learning outcomes", "assessment schedule")),
        ("announcement", ("announcement", "important update", "housekeeping")),
        ("email", ("from:", "subject:", "dear students")),
        ("workshop", ("workshop", "tutorial", "tutor")),
        ("lecture", ("lecture", "recording", "transcript")),
        ("module", ("module", "week 1", "week 2", "weekly content")),
    ]
    for source_type, keywords in rules:
        if any(keyword in sample for keyword in keywords):
            return source_type
    return "other"


def _detect_language(text: str) -> str:
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin_letters = len(re.findall(r"[A-Za-z]", text))
    return "zh-CN" if chinese_chars > latin_letters else "en-AU"


def _chunk_text(source_id: str, text: str, max_chars: int = 3600) -> tuple[DocumentChunk, ...]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    chunks: list[DocumentChunk] = []
    buffer: list[str] = []
    buffer_length = 0
    heading: str | None = None

    def flush() -> None:
        nonlocal buffer, buffer_length
        if not buffer:
            return
        index = len(chunks)
        chunks.append(
            DocumentChunk(
                id=f"{source_id}-chunk-{index:03d}",
                source_id=source_id,
                index=index,
                heading=heading,
                text="\n\n".join(buffer),
            )
        )
        buffer = []
        buffer_length = 0

    for block in blocks:
        if block.startswith("#"):
            flush()
            heading = block.lstrip("# ").strip()
        if buffer and buffer_length + len(block) + 2 > max_chars:
            flush()
        buffer.append(block)
        buffer_length += len(block) + 2
    flush()
    return tuple(chunks)


def ingest_document(path: str | Path, *, private: bool | None = None) -> SourceDocument:
    source_path = Path(path).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    raw_bytes = source_path.read_bytes()
    digest = sha256(raw_bytes).hexdigest()
    source_id = f"src-{digest[:12]}"
    text = _read_text(source_path).strip()
    if not text:
        raise ValueError(f"No readable text found in {source_path.name}")

    is_private = private if private is not None else "data/private" in source_path.as_posix()
    return SourceDocument(
        id=source_id,
        title=source_path.stem,
        path=str(source_path),
        source_type=classify_document(source_path.stem, text),
        language=_detect_language(text),
        is_private=is_private,
        sha256=digest,
        chunks=_chunk_text(source_id, text),
    )
