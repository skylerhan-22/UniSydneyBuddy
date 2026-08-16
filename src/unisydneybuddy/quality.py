"""Deterministic quality checks for canonical course data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


def _ids(items: list[dict[str, Any]]) -> list[str]:
    return [str(item.get("id", "")) for item in items]


def validate_bundle(bundle: dict[str, Any]) -> list[ValidationIssue]:
    """Validate cross-object rules that JSON Schema alone cannot express."""

    issues: list[ValidationIssue] = []
    course = bundle["course"]
    assessments = bundle.get("assessments", [])
    weeks = bundle.get("weeks", [])
    tasks = bundle.get("tasks", [])
    evidence = bundle.get("evidence", [])

    collections = {
        "assessment": assessments,
        "week": weeks,
        "task": tasks,
        "evidence": evidence,
    }
    for name, items in collections.items():
        item_ids = _ids(items)
        if len(item_ids) != len(set(item_ids)):
            issues.append(ValidationIssue("duplicate_id", f"Duplicate {name} id found."))
        if any(not item_id for item_id in item_ids):
            issues.append(ValidationIssue("missing_id", f"A {name} object has no id."))

    assessment_ids = set(_ids(assessments))
    week_ids = set(_ids(weeks))
    evidence_ids = set(_ids(evidence))

    for assessment_id in course.get("assessment_ids", []):
        if assessment_id not in assessment_ids:
            issues.append(ValidationIssue("broken_assessment_ref", assessment_id))
    for week_id in course.get("week_ids", []):
        if week_id not in week_ids:
            issues.append(ValidationIssue("broken_week_ref", week_id))

    weight_total = sum(
        assessment["weight_percent"]
        for assessment in assessments
        if assessment.get("weight_percent") is not None
    )
    if weight_total != 100:
        issues.append(ValidationIssue("assessment_weight_total", f"Weights total {weight_total}, expected 100."))

    for assessment in assessments:
        due_at = assessment.get("due_at")
        if due_at:
            try:
                datetime.fromisoformat(due_at)
            except ValueError:
                issues.append(ValidationIssue("invalid_due_at", assessment["id"]))

        if assessment.get("mode") == "group":
            team_size = assessment.get("team_size")
            if not team_size or team_size["min"] > team_size["max"]:
                issues.append(ValidationIssue("invalid_team_size", assessment["id"]))
            if len(assessment.get("deliverables", [])) < 2:
                issues.append(ValidationIssue("group_deliverables_incomplete", assessment["id"]))

    evidence_ref_owners: list[dict[str, Any]] = [course, *assessments, *weeks, *tasks]
    for owner in evidence_ref_owners:
        for evidence_id in owner.get("evidence_ids", []):
            if evidence_id not in evidence_ids:
                issues.append(ValidationIssue("broken_evidence_ref", evidence_id))

    for task in tasks:
        if task.get("status") == "proposed" and any(
            task.get(field) for field in ("owner", "reviewer", "backup")
        ):
            issues.append(ValidationIssue("unconfirmed_assignment", task["id"]))

    return issues

