"""Provider-neutral interface for structured course fact extraction."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Protocol

from .ingest import SourceDocument


ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ExtractionRequest:
    instruction: str
    target_schema: dict[str, Any]
    source_documents: tuple[dict[str, Any], ...]
    output_language: str

    @property
    def contains_private_sources(self) -> bool:
        return any(source["is_private"] for source in self.source_documents)


class StructuredExtractionClient(Protocol):
    """Small adapter surface for a future OpenAI or alternative provider."""

    def extract(self, request: ExtractionRequest) -> dict[str, Any]: ...


def build_extraction_request(
    documents: list[SourceDocument],
    *,
    schema_name: str,
    output_language: str = "zh-CN",
) -> ExtractionRequest:
    if output_language not in {"zh-CN", "en"}:
        raise ValueError("output_language must be 'zh-CN' or 'en'")

    schema_path = ROOT / "schemas" / f"{schema_name}.schema.json"
    if not schema_path.is_file():
        raise ValueError(f"Unknown schema: {schema_name}")

    prompt = (ROOT / "prompts" / "course_mapper.zh-CN.md").read_text(encoding="utf-8")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    sources = tuple(
        {
            "id": document.id,
            "title": document.title,
            "source_type": document.source_type,
            "language": document.language,
            "is_private": document.is_private,
            "chunks": [
                {
                    "id": chunk.id,
                    "heading": chunk.heading,
                    "text": chunk.text,
                }
                for chunk in document.chunks
            ],
        }
        for document in documents
    )
    return ExtractionRequest(
        instruction=prompt,
        target_schema=schema,
        source_documents=sources,
        output_language=output_language,
    )


def extract_with(
    client: StructuredExtractionClient,
    request: ExtractionRequest,
    *,
    allow_private: bool = False,
) -> dict[str, Any]:
    """Run one extraction call while keeping provider logic outside the pipeline."""

    if request.contains_private_sources and not allow_private:
        raise PermissionError(
            "Private course sources are blocked. Confirm the provider data boundary before transmission."
        )
    result = client.extract(request)
    if not isinstance(result, dict):
        raise TypeError("Structured extraction client must return a JSON object.")
    return result
