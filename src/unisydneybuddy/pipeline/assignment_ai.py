"""Structured AI analysis for assignment material."""

from __future__ import annotations

import os
from typing import Any, Literal

from pydantic import BaseModel, Field


SourceLevel = Literal[
    "required",
    "source_recommended",
    "ai_plus_required",
    "ai_plus_recommended",
    "ai_suggestion",
]


class KeyRequirement(BaseModel):
    text: str
    level: Literal["required", "source_recommended"]
    source: str
    evidence: str


class FrameworkSubsection(BaseModel):
    title: str
    guidance: str
    writing_points: list[str]
    level: Literal["ai_plus_required", "ai_plus_recommended", "ai_suggestion"]


class FrameworkSection(BaseModel):
    section: str
    purpose: str
    required_content: list[str]
    evidence_suggestions: list[str]
    word_share: str | None
    word_share_level: Literal["required", "source_recommended", "ai_suggestion"] | None
    level: SourceLevel
    source: str
    evidence: str
    subsections: list[FrameworkSubsection]


class RequiredDocument(BaseModel):
    name: str
    usage: str
    location: str | None
    requirement: Literal["required", "recommended"]
    source: str
    evidence: str


class AssignmentAnalysis(BaseModel):
    summary: str
    objective: str
    final_deliverables: list[str]
    key_requirements: list[KeyRequirement]
    content_framework: list[FrameworkSection] = Field(
        description="The single assignment-structure tree, mapping every output section to the content the student should write"
    )
    required_documents: list[RequiredDocument] = Field(
        description="Only documents, files, data, templates or supporting materials explicitly required or recommended in the sources"
    )


def analyse_assignment_materials(
    *,
    assignment: dict[str, Any],
    materials: list[dict[str, str]],
    language: str,
    client: Any | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Analyse one assignment with OpenAI Structured Outputs.

    The caller is responsible for obtaining consent before transmitting private
    course material to a model provider.
    """

    if client is None:
        try:
            from openai import OpenAI
        except ModuleNotFoundError as exc:
            raise RuntimeError("OpenAI SDK is not installed.") from exc
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    output_language = "Simplified Chinese" if language == "中文" else "English"
    material_text = "\n\n".join(
        f"--- SOURCE: {item['title']} ---\n{item['text']}" for item in materials
    )
    system_prompt = f"""
You analyse university assignment briefs, rubrics and Canvas assessment text.
Return all user-facing fields in {output_language}, while preserving official
course terms and document names when useful.

GROUNDING AND LABELS
1. Ground every result in the supplied sources. Never invent a requirement.
2. Use level=required only for explicit mandatory source requirements.
3. Use level=source_recommended only for explicit source recommendations.
4. Use level=ai_plus_required for AI detail nested under a mandatory source structure.
5. Use level=ai_plus_recommended for AI detail nested under a source-recommended structure.
6. Use level=ai_suggestion only when the source provides no corresponding structure.
7. Copy a short supporting phrase into evidence and name its source document in source.

SUMMARY
8. objective states what the assignment is trying to assess or produce.
9. final_deliverables contains only actual submission outputs.
10. key_requirements contains the 3-5 most important explicit constraints, never AI advice.

UNIFIED ASSIGNMENT STRUCTURE — HARD RULES
11. content_framework is the ONLY breakdown. Do not create a separate task plan.
12. Its tree must answer two student questions for every node: WHERE the content belongs
    in the final deliverable, and WHAT substantive content should be written there.
13. Top-level nodes are the actual report sections, presentation sections, video segments
    or other formal output components. They must be usable directly as group responsibilities.
14. NEVER create structure nodes for uploading, file naming, formatting, merging files,
    proofreading, checking references, arranging meetings, reminders, scheduling,
    progress tracking, team leadership or other administrative chores.
15. Citation style, total word count, file type and submission rules belong in
    key_requirements, not as standalone structure nodes, unless the source explicitly
    requires a bibliography/reference-list section in the final deliverable.
16. If the source mandates a framework, preserve its top-level section names, order and
    constraints exactly. Mark those sections required. AI may only add one subsection
    level beneath them, marked ai_plus_required.
17. If the source recommends a framework, preserve it and mark it source_recommended.
    AI detail beneath it must be ai_plus_recommended.
18. Only when no framework is supplied may AI propose top-level sections, marked
    ai_suggestion. Do not present AI-created structure as a source requirement.
19. Framework depth is limited to: final-deliverable section -> AI subsection -> writing
    points. Do not produce paragraph templates or write the assignment itself.
20. Keep the structure compact but make its advice deep. For each substantive section,
    add only 1-3 useful subsections and at most 3 high-value writing points per subsection.
    Prioritize the analytical question, relevant theory, evidence use and expected critical
    judgement. Do not repeat the same advice across sections or pad formal sections.
21. AI writing points must tell the student how to reason, connect evidence and satisfy the
    brief. Never use vague filler such as "provide details", "write clearly" or "add examples".
22. Never invent extra sections merely to match the number of group members. Students may
    share a substantial section when the source structure has fewer sections than members.
23. Preserve explicit word allocations and label word_share_level accordingly. Otherwise
    word_share must be a clearly phrased AI suggestion with word_share_level=ai_suggestion,
    or both fields must be null when a responsible estimate is not possible.
24. When sources conflict, prioritize rubric/formal requirements, then assignment brief,
    then Canvas explanatory text, then AI suggestions.

DOCUMENTS
25. required_documents must contain ONLY files, documents, datasets, templates, forms,
    readings or supporting materials explicitly required or recommended by the sources.
26. If none are mentioned, return an empty list. Never infer commonly used documents.
27. location records the stated Canvas/module/folder/page location when supplied; otherwise null.
""".strip()
    assignment_context = {
        "title": assignment.get("title_original"),
        "mode": assignment.get("mode"),
        "weight_percent": assignment.get("weight_percent"),
        "due_at": assignment.get("due_at"),
        "team_size": assignment.get("team_size"),
        "known_deliverables": [item.get("title_original") for item in assignment.get("deliverables", [])],
    }
    response = client.responses.parse(
        model=model or os.environ.get("OPENAI_MODEL", "gpt-5.4-mini"),
        input=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Known course metadata:\n{assignment_context}\n\nAssignment sources:\n{material_text}",
            },
        ],
        text_format=AssignmentAnalysis,
    )
    if response.output_parsed is None:
        raise RuntimeError("The model did not return a usable assignment analysis.")
    return response.output_parsed.model_dump()
