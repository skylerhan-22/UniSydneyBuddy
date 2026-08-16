from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from unisydneybuddy.pipeline import build_extraction_request, extract_with, ingest_document  # noqa: E402


class FakeClient:
    def extract(self, request):
        return {"schema_title": request.target_schema["title"], "language": request.output_language}


class MapperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = ingest_document(ROOT / "data" / "demo" / "sample_assignment_overview.txt")

    def test_builds_chinese_first_structured_request(self) -> None:
        request = build_extraction_request([self.document], schema_name="assessment")
        self.assertEqual(request.output_language, "zh-CN")
        self.assertEqual(request.target_schema["title"], "Assessment")
        self.assertIn("不得推测", request.instruction)
        self.assertEqual(request.source_documents[0]["source_type"], "assignment")

    def test_supports_english_output_without_changing_sources(self) -> None:
        chinese = build_extraction_request([self.document], schema_name="assessment", output_language="zh-CN")
        english = build_extraction_request([self.document], schema_name="assessment", output_language="en")
        self.assertEqual(chinese.source_documents, english.source_documents)

    def test_provider_adapter_is_replaceable(self) -> None:
        request = build_extraction_request([self.document], schema_name="assessment")
        result = extract_with(FakeClient(), request)
        self.assertEqual(result, {"schema_title": "Assessment", "language": "zh-CN"})

    def test_rejects_unknown_language(self) -> None:
        with self.assertRaises(ValueError):
            build_extraction_request([self.document], schema_name="assessment", output_language="fr")

    def test_private_sources_are_blocked_before_provider_call(self) -> None:
        private_document = ingest_document(
            ROOT / "data" / "demo" / "sample_assignment_overview.txt",
            private=True,
        )
        request = build_extraction_request([private_document], schema_name="assessment")
        with self.assertRaises(PermissionError):
            extract_with(FakeClient(), request)


if __name__ == "__main__":
    unittest.main()
