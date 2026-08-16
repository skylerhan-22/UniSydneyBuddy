from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from unisydneybuddy.demo import (  # noqa: E402
    analyze_date_change,
    build_project_markdown,
    build_project_templates,
    eval_snapshot,
    build_detailed_project_plan,
    format_due,
    propose_work_parts,
    required_project_files,
    weekly_copy,
)


class DemoHelpersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = json.loads((ROOT / "data" / "evals" / "qbus6600_gold.json").read_text(encoding="utf-8"))
        cls.assignment = next(item for item in cls.bundle["assessments"] if item["id"] == "qbus6600-a2")

    def test_announcement_date_change_uses_latest_date(self) -> None:
        result = analyze_date_change(
            "Assignment 2 has moved from 19 October 2026 to 21 October 2026.",
            self.assignment["due_at"],
        )
        self.assertEqual(result["before"], "2026-10-19")
        self.assertEqual(result["after"], "2026-10-21")

    def test_announcement_without_new_date_is_not_a_change(self) -> None:
        self.assertIsNone(analyze_date_change("Please remember Assignment 2.", self.assignment["due_at"]))

    def test_due_date_uses_chinese_date_order_in_chinese_mode(self) -> None:
        self.assertEqual(format_due("2026-10-19T23:59:00", "中文"), "2026年10月19日")
        self.assertEqual(format_due("2026-10-19T23:59:00", "English"), "19 Oct 2026")

    def test_project_export_contains_owners(self) -> None:
        markdown = build_project_markdown(
            self.assignment,
            [{"任务": "合并报告", "负责人": "成员 A", "审核人": "成员 B"}],
            language="中文",
        )
        self.assertIn("成员 A", markdown)
        self.assertIn("合并报告", markdown)
        self.assertIn("## 作业结构", markdown)
        self.assertIn("负责人：成员 A", markdown)
        self.assertNotIn("Owner:", markdown)

    def test_project_export_preserves_document_location(self) -> None:
        markdown = build_project_markdown(
            self.assignment,
            [],
            language="English",
            project_files=[{"Document": "Dataset", "Level": "Required", "Purpose": "Analysis", "Location": "Canvas > A2"}],
        )
        self.assertIn("Location: Canvas > A2", markdown)

    def test_eval_snapshot_counts_required_items(self) -> None:
        metrics = eval_snapshot(self.bundle, automated_tests=20)
        self.assertEqual(metrics["deliverables"], "6/6")
        self.assertEqual(metrics["tba_preserved"], "3/3")
        self.assertEqual(metrics["evidence_coverage"], "5/5")

    def test_work_parts_follow_confirmed_team_size(self) -> None:
        self.assertEqual(len(propose_work_parts(3, "中文")), 3)
        self.assertEqual(len(propose_work_parts(4, "English")), 4)
        self.assertIn("证据", propose_work_parts(3, "中文")[1]["scope"])

    def test_weekly_copy_is_chinese_first_but_keeps_course_terms(self) -> None:
        week = next(item for item in self.bundle["weeks"] if item["id"] == "qbus6600-w2")
        must_do = weekly_copy(week, "must_do", "中文")
        self.assertIn("Explore", must_do[0])
        self.assertIn("完成", must_do[0])

    def test_detailed_project_plan_and_file_list_are_actionable(self) -> None:
        plan = build_detailed_project_plan("中文", "2026-10-19T23:59:00+11:00")
        files = required_project_files("中文")
        self.assertEqual(len(plan), 7)
        self.assertGreaterEqual(len(files), 8)
        self.assertTrue(any("Rubric" in item["文档"] for item in files))
        self.assertTrue(all("/" in item["建议位置"] for item in files))
        self.assertTrue(any("Peer review" in item["阶段产出"] for item in plan))
        self.assertEqual(plan[-1]["建议时间"], "2026年10月17日")

    def test_project_templates_have_downloadable_names_and_content(self) -> None:
        templates = build_project_templates("中文")
        self.assertEqual(len(templates), 9)
        self.assertTrue(all(item["文件名"] and item["内容"] for item in templates))
        self.assertTrue(any(item["文件名"].endswith(".csv") for item in templates))
        self.assertFalse(any(item["文件名"].endswith(".py") for item in templates))

    def test_english_project_templates_have_no_chinese_copy(self) -> None:
        templates = build_project_templates("English", "MKTG6104", "2026-11-06T23:59:00+11:00")
        rendered = json.dumps(templates, ensure_ascii=False)
        self.assertIsNone(re.search(r"[\u4e00-\u9fff]", rendered))
        self.assertTrue(all(set(item) == {"File", "Purpose", "Filename", "Content"} for item in templates))

    def test_work_parts_support_known_four_to_six_person_team(self) -> None:
        self.assertEqual(len(propose_work_parts(5, "English")), 5)
        self.assertEqual(len(propose_work_parts(6, "中文")), 6)


if __name__ == "__main__":
    unittest.main()
