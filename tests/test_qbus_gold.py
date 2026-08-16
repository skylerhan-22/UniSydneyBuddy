from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from unisydneybuddy.quality import validate_bundle  # noqa: E402


class QbusGoldDatasetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = json.loads(
            (ROOT / "data" / "evals" / "qbus6600_gold.json").read_text(encoding="utf-8")
        )

    def test_all_schema_files_are_valid_json(self) -> None:
        expected = {"course", "assessment", "week", "task", "evidence"}
        found = set()
        for path in (ROOT / "schemas").glob("*.schema.json"):
            schema = json.loads(path.read_text(encoding="utf-8"))
            found.add(path.name.removesuffix(".schema.json"))
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema["type"], "object")
        self.assertEqual(found, expected)

    def test_cross_object_quality_rules_pass(self) -> None:
        self.assertEqual(validate_bundle(self.bundle), [])

    def test_gold_objects_match_json_schemas(self) -> None:
        groups = {
            "course": [self.bundle["course"]],
            "assessment": self.bundle["assessments"],
            "week": self.bundle["weeks"],
            "task": self.bundle["tasks"],
            "evidence": self.bundle["evidence"],
        }
        for schema_name, objects in groups.items():
            schema = json.loads(
                (ROOT / "schemas" / f"{schema_name}.schema.json").read_text(encoding="utf-8")
            )
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            for item in objects:
                errors = list(validator.iter_errors(item))
                self.assertEqual(errors, [], f"{schema_name} {item.get('id')} failed: {errors}")

    def test_assessment_weights_total_one_hundred(self) -> None:
        total = sum(item["weight_percent"] for item in self.bundle["assessments"])
        self.assertEqual(total, 100)

    def test_group_assignment_captures_real_delivery_shape(self) -> None:
        assignment = next(item for item in self.bundle["assessments"] if item["id"] == "qbus6600-a2")
        self.assertEqual(assignment["mode"], "group")
        self.assertEqual(assignment["team_size"], {"min": 3, "max": 4})
        self.assertEqual(
            {item["id"] for item in assignment["deliverables"]},
            {"written_report", "presentation_video", "python_code"},
        )
        self.assertEqual(
            {item["id"] for item in assignment["intermediate_deliverables"]},
            {"responsibilities_outline", "progress_report", "peer_review"},
        )

    def test_tba_dates_remain_unknown(self) -> None:
        assignment = next(item for item in self.bundle["assessments"] if item["id"] == "qbus6600-a2")
        self.assertTrue(all(item["due_at"] is None for item in assignment["intermediate_deliverables"]))
        unknown_fields = {item["field"] for item in self.bundle["course"]["unknowns"]}
        self.assertIn("qbus6600-a2.intermediate_deliverables.due_at", unknown_fields)

    def test_all_user_facing_titles_have_chinese_localization(self) -> None:
        objects = [*self.bundle["assessments"], *self.bundle["weeks"], *self.bundle["tasks"]]
        for item in objects:
            self.assertTrue(item["title_original"])
            self.assertTrue(item["title_localized"]["zh-CN"])

    def test_proposed_team_tasks_are_not_assigned_by_ai(self) -> None:
        for task in self.bundle["tasks"]:
            if task["status"] == "proposed":
                self.assertIsNone(task["owner"])
                self.assertIsNone(task["reviewer"])
                self.assertIsNone(task["backup"])

    def test_private_course_materials_are_gitignored(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("data/private/", gitignore)


if __name__ == "__main__":
    unittest.main()
