"""Local ingestion and AI extraction pipeline."""

from .ingest import DocumentChunk, SourceDocument, ingest_document
from .mapper import ExtractionRequest, StructuredExtractionClient, build_extraction_request, extract_with
from .assignment_ai import AssignmentAnalysis, analyse_assignment_materials

__all__ = [
    "DocumentChunk",
    "ExtractionRequest",
    "SourceDocument",
    "StructuredExtractionClient",
    "build_extraction_request",
    "extract_with",
    "AssignmentAnalysis",
    "analyse_assignment_materials",
    "ingest_document",
]
