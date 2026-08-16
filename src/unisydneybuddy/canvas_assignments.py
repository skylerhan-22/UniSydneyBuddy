from __future__ import annotations

from html import unescape
import re
from typing import Any


GENERIC_TITLE_TOKENS = {
    "assignment",
    "assessment",
    "project",
    "report",
    "individual",
    "group",
    "presentation",
}


def canvas_text(value: str) -> str:
    """Convert Canvas HTML into readable text without executing embedded markup."""
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = re.sub(r"\s+", " ", unescape(text)).strip()
    return re.sub(r"\s+([.,;:!?])", r"\1", text)


def match_canvas_assignment(candidate: dict[str, Any], assignments: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Match one local assessment to its Canvas Assignment conservatively."""
    candidate_title = str(candidate.get("title_original") or "").lower()
    candidate_due = str(candidate.get("due_at") or "")[:10]
    candidate_number = re.search(r"(?:assignment|assessment)\s*(\d+)", candidate_title)
    candidate_tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", candidate_title)
        if len(token) >= 4 and token not in GENERIC_TITLE_TOKENS
    }

    scored: list[tuple[int, dict[str, Any]]] = []
    for assignment in assignments:
        canvas_title = str(assignment.get("name") or "").lower()
        if not canvas_title:
            continue
        score = 0
        if candidate_title == canvas_title:
            score += 100
        canvas_number = re.search(r"(?:assignment|assessment)\s*(\d+)", canvas_title)
        if candidate_number and canvas_number and candidate_number.group(1) == canvas_number.group(1):
            score += 35
        canvas_due = str(assignment.get("due_at") or "")[:10]
        if candidate_due and canvas_due and candidate_due == canvas_due:
            score += 25
        canvas_tokens = set(re.findall(r"[a-z0-9]+", canvas_title))
        score += 4 * len(candidate_tokens & canvas_tokens)
        scored.append((score, assignment))

    if not scored:
        return None
    best_score, best_assignment = max(scored, key=lambda item: item[0])
    return best_assignment if best_score >= 8 else None


def canvas_assignment_material(assignment: dict[str, Any]) -> str:
    """Build the analysis source from the assignment description and visible rubric."""
    lines = [f"Assignment: {assignment.get('name') or 'Untitled assignment'}"]
    if assignment.get("due_at"):
        lines.append(f"Due at: {assignment['due_at']}")
    if assignment.get("points_possible") is not None:
        lines.append(f"Points possible: {assignment['points_possible']}")
    submission_types = assignment.get("submission_types") or []
    if submission_types:
        lines.append("Submission types: " + ", ".join(str(item) for item in submission_types))
    description = canvas_text(str(assignment.get("description") or ""))
    if description:
        lines.extend(["", "Assignment description:", description])

    rubric_lines: list[str] = []
    for criterion in assignment.get("rubric") or []:
        if not isinstance(criterion, dict):
            continue
        title = canvas_text(str(criterion.get("description") or ""))
        detail = canvas_text(str(criterion.get("long_description") or ""))
        points = criterion.get("points")
        row = title or detail
        if detail and detail != title:
            row = f"{row}: {detail}" if row else detail
        if points is not None:
            row = f"{row} ({points} points)" if row else f"{points} points"
        if row:
            rubric_lines.append(row)
    if rubric_lines:
        lines.extend(["", "Visible rubric:", *[f"- {row}" for row in rubric_lines]])
    return "\n".join(lines).strip()
