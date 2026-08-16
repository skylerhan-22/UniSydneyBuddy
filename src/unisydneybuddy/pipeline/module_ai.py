"""Grounded AI briefs for every released Canvas Module item in one week."""

from __future__ import annotations

import os
from typing import Any, Literal

from pydantic import BaseModel, Field


class BilingualLabel(BaseModel):
    title_zh: str
    title_en: str


class BilingualText(BaseModel):
    text_zh: str
    text_en: str


class KnowledgeBranch(BilingualLabel):
    points: list[BilingualLabel] = Field(min_length=1, max_length=4)


class ExplanationSection(BaseModel):
    heading_zh: str
    heading_en: str
    content_zh: str
    content_en: str


class ModuleWalkthrough(BilingualLabel):
    module_label: str
    overview_zh: str
    overview_en: str
    sections: list[ExplanationSection] = Field(max_length=5)


class NoticeOrPreparation(BilingualLabel):
    kind: Literal["notice", "workshop_preparation"]
    source_title: str
    detail_zh: str
    detail_en: str


class OneView(BaseModel):
    core_sentence_zh: str
    core_sentence_en: str
    takeaways: list[BilingualText] = Field(min_length=1, max_length=3)
    logic_chain: list[BilingualLabel] = Field(min_length=2, max_length=7)


class ModuleSummary(BaseModel):
    central_topic_zh: str
    central_topic_en: str
    knowledge_map: list[KnowledgeBranch] = Field(min_length=1, max_length=5)
    walkthrough: list[ModuleWalkthrough] = Field(min_length=1)
    notices_and_preparation: list[NoticeOrPreparation] = Field(default_factory=list)
    one_view: OneView


def validate_module_summary_coverage(
    value: object,
    *,
    expected_items: list[str],
    readable_items: list[str],
    announcement_titles: list[str],
) -> bool:
    """Validate completeness against the exact synced week inputs."""
    if not isinstance(value, dict):
        return False
    required = {
        "central_topic_zh",
        "central_topic_en",
        "knowledge_map",
        "walkthrough",
        "notices_and_preparation",
        "one_view",
    }
    if not required.issubset(value):
        return False
    knowledge_map = value.get("knowledge_map", [])
    if not knowledge_map or any(not branch.get("points") for branch in knowledge_map):
        return False
    walkthrough = value.get("walkthrough", [])
    if [item.get("module_label") for item in walkthrough] != expected_items:
        return False
    readable = set(readable_items)
    for item in walkthrough:
        if not item.get("overview_zh") or not item.get("overview_en") or "sections" not in item:
            return False
        sections = item.get("sections", [])
        if len(sections) > 5 or (item.get("module_label") in readable and len(sections) < 2):
            return False
        if item.get("module_label") not in readable and sections:
            return False
    one_view = value.get("one_view", {})
    if (
        not one_view.get("core_sentence_zh")
        or not one_view.get("core_sentence_en")
        or not one_view.get("takeaways")
        or len(one_view.get("logic_chain", [])) < 2
    ):
        return False
    notice_sources = {
        item.get("source_title")
        for item in value.get("notices_and_preparation", [])
        if item.get("kind") == "notice"
    }
    return set(announcement_titles).issubset(notice_sources)


def summarise_module(
    *,
    course_title: str,
    week_number: int,
    module_names: list[str],
    module_items: list[str],
    module_text: str,
    announcements: list[dict[str, str]] | None = None,
    language: str,
    client: Any | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Summarise all supplied Canvas Module items for one week."""
    if client is None:
        try:
            from openai import OpenAI
        except ModuleNotFoundError as exc:
            raise RuntimeError("OpenAI SDK is not installed.") from exc
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    primary_language = "Simplified Chinese" if language == "中文" else "English"
    system_prompt = f"""
You create a university student's weekly brief from every released Canvas Module
item supplied for that week. Return every user-facing field in both Simplified
Chinese and English in the corresponding _zh and _en fields. The current primary
interface language is {primary_language}, but neither language may be omitted.

HARD RULES
1. Use only the supplied Canvas Module text, item titles and matched Canvas
   announcements. Do not add facts,
   readings, theories, requirements or examples absent from the source.
2. Treat the WEEK as the unit of analysis. Cover every supplied Module item
   (for example 2.1, 2.2 and 2.3), not only the first page. Every substantive
   item must appear in walkthrough. Preserve the original module_label.
3. knowledge_map is one integrated mind map for the whole week. Organise ideas
   by their conceptual relationships rather than merely repeating the item list.
   Use 2-5 branches and 1-4 concise points per branch.
4. walkthrough follows every supplied Module item in source order, including an
   item marked as having no readable body. Preserve its original module_label.
   For each item, write a substantial overview followed by 2-5 logically ordered
   sections, with complete Chinese and English versions of every heading and paragraph.
   Explain definitions, relationships, processes and reasoning in detail. Connect
   each item to the preceding one. Never describe a source as truncated merely
   because the input ends at a natural page boundary. If an item is explicitly
   marked [NO READABLE BODY SYNCED], state only that limitation and return no
   invented content for it.
   Do not split the same material into duplicate 'key concepts' and 'detailed
   explanation' sections.
5. notices_and_preparation appears after walkthrough. Extract only explicit
   administrative notices or work required before a Workshop. Use kind
   'notice' or 'workshop_preparation'. Preserve the exact originating item or
   announcement title in source_title. Every supplied Canvas announcement must
   appear exactly once as kind 'notice'. If neither source exists, return an empty list.
   Do not turn general knowledge, readings, recordings, submission chores or
   inferred study advice into Workshop preparation.
6. one_view gives a GPT-style conclusion: one core sentence, exactly 3 concise
   takeaways when the source supports them, and a 3-7 step logic chain.
7. Focus on Module knowledge. Do not discuss or infer Recording, transcript,
   Ed Lesson, Lecture, Tutorial or Workshop teaching content. Explicit Workshop
   preparation found inside the Module is the only Workshop-related exception.
8. If the supplied material is sparse, say so instead of padding the answer.
""".strip()
    user_content = (
        f"Course: {course_title}\n"
        f"Week: {week_number}\n"
        f"Canvas Modules: {module_names}\n"
        f"Module item titles in source order: {module_items}\n\n"
        f"Released Module text:\n{module_text}\n\n"
        f"Canvas announcements matched to this week:\n{announcements or []}"
    )
    response = client.responses.parse(
        model=model or os.environ.get("OPENAI_MODEL", "gpt-5.4-mini"),
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        text_format=ModuleSummary,
    )
    if response.output_parsed is None:
        raise RuntimeError("The model did not return a usable Module summary.")
    return response.output_parsed.model_dump()
