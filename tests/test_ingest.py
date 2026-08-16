from __future__ import annotations

import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from unisydneybuddy.pipeline.ingest import classify_document, ingest_document  # noqa: E402


class IngestTest(unittest.TestCase):
    def test_assignment_is_classified_and_chunked(self) -> None:
        document = ingest_document(ROOT / "data" / "demo" / "sample_assignment_overview.txt")
        self.assertEqual(document.source_type, "assignment")
        self.assertEqual(document.language, "en-AU")
        self.assertFalse(document.is_private)
        self.assertGreaterEqual(len(document.chunks), 1)
        self.assertTrue(all(chunk.source_id == document.id for chunk in document.chunks))

    def test_same_file_has_stable_source_id(self) -> None:
        path = ROOT / "data" / "demo" / "sample_assignment_overview.txt"
        self.assertEqual(ingest_document(path).id, ingest_document(path).id)

    def test_tba_does_not_become_a_date_during_ingestion(self) -> None:
        document = ingest_document(ROOT / "data" / "demo" / "sample_assignment_overview.txt")
        self.assertIn("TBA", document.chunks[0].text)

    def test_document_classifier_supports_weekly_sources(self) -> None:
        self.assertEqual(classify_document("Week 2", "Weekly content and Engage"), "module")
        self.assertEqual(classify_document("Tutorial preparation", "Bring your notes"), "workshop")

    def test_screenshot_text_is_sent_through_local_ocr(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "assignment_2.png"
            image.write_bytes(b"mock-png")
            completed = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="Assignment 2 group project brief and rubric",
                stderr="",
            )
            with patch("unisydneybuddy.pipeline.ingest.subprocess.run", return_value=completed) as run:
                document = ingest_document(image, private=True)

        self.assertEqual(document.source_type, "rubric")
        self.assertTrue(document.is_private)
        self.assertIn("Assignment 2", document.chunks[0].text)
        self.assertIn("ocr_image.swift", str(run.call_args.args[0]))


if __name__ == "__main__":
    unittest.main()
