from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectStatusTest(unittest.TestCase):
    def test_status_has_at_most_one_active_phase_and_bilingual_titles(self) -> None:
        status = json.loads((ROOT / "project_status.json").read_text(encoding="utf-8"))
        active = [item for item in status["milestones"] if item["status"] == "in_progress"]
        self.assertLessEqual(len(active), 1)
        if not active:
            self.assertTrue(all(item["status"] == "completed" for item in status["milestones"]))
        for item in status["milestones"]:
            self.assertTrue(item["title_zh"])
            self.assertTrue(item["title_en"])
            self.assertIn(item["status"], {"completed", "in_progress", "pending"})


if __name__ == "__main__":
    unittest.main()
