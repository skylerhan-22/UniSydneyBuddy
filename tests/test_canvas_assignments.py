from __future__ import annotations

from unisydneybuddy.canvas_assignments import canvas_assignment_material, match_canvas_assignment


def test_matches_canvas_assignment_by_number_and_due_date() -> None:
    candidate = {
        "title_original": "Consulting Presentation",
        "due_at": "2026-10-19T12:59:59Z",
    }
    assignments = [
        {"id": 1, "name": "Assignment 1: Critical Analysis", "due_at": "2026-09-14T13:59:59Z"},
        {"id": 2, "name": "Assignment 2: Consulting Presentation", "due_at": "2026-10-19T12:59:59Z"},
    ]
    assert match_canvas_assignment(candidate, assignments)["id"] == 2


def test_does_not_match_unrelated_participation_item() -> None:
    candidate = {"title_original": "Critical Reflection", "due_at": "2026-11-16T12:59:59Z"}
    assignments = [{"id": 3, "name": "Workshops and group work", "due_at": None}]
    assert match_canvas_assignment(candidate, assignments) is None


def test_builds_material_from_description_and_visible_rubric() -> None:
    assignment = {
        "name": "Assignment 1",
        "due_at": "2026-09-14T13:59:59Z",
        "points_possible": 30,
        "submission_types": ["online_upload"],
        "description": "<p>Write a <strong>critical analysis</strong>.</p>",
        "rubric": [{"description": "Use of evidence", "long_description": "Apply course concepts", "points": 8}],
    }
    material = canvas_assignment_material(assignment)
    assert "Write a critical analysis." in material
    assert "Use of evidence: Apply course concepts (8 points)" in material
    assert "<strong>" not in material
