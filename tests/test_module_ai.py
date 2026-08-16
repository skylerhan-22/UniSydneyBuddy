from __future__ import annotations

from types import SimpleNamespace
from copy import deepcopy

from unisydneybuddy.pipeline.module_ai import ModuleSummary, summarise_module, validate_module_summary_coverage


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs = None

    def parse(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            output_parsed=ModuleSummary(
                central_topic_zh="创业过程",
                central_topic_en="Entrepreneurship Process",
                knowledge_map=[
                    {
                        "title_zh": "机会创造",
                        "title_en": "Opportunity Creation",
                        "points": [{"title_zh": "识别需求", "title_en": "Recognise Needs"}],
                    }
                ],
                walkthrough=[
                    {
                        "module_label": "2.1 Overview",
                        "title_zh": "机会识别",
                        "title_en": "Opportunity Recognition",
                        "overview_zh": "本节说明如何识别尚未被满足的需求。",
                        "overview_en": "This section explains how to identify unmet needs.",
                        "sections": [
                            {"heading_zh": "识别问题", "heading_en": "Identify problems", "content_zh": "先观察尚未被满足的需求。", "content_en": "Start by observing unmet needs."},
                            {"heading_zh": "形成机会", "heading_en": "Form an opportunity", "content_zh": "再把问题转化为机会假设。", "content_en": "Turn the problem into an opportunity hypothesis."},
                        ],
                    }
                ],
                notices_and_preparation=[
                    {
                        "kind": "workshop_preparation",
                        "source_title": "2.1 Overview",
                        "title_zh": "Workshop 前阅读",
                        "title_en": "Pre-workshop Reading",
                        "detail_zh": "完成指定案例阅读。",
                        "detail_en": "Complete the assigned case reading.",
                    }
                ],
                one_view={
                    "core_sentence_zh": "机会识别是价值创造的起点。",
                    "core_sentence_en": "Opportunity recognition begins value creation.",
                    "takeaways": [
                        {"text_zh": "识别需求", "text_en": "Recognise needs"},
                        {"text_zh": "形成假设", "text_en": "Form a hypothesis"},
                        {"text_zh": "验证价值", "text_en": "Validate value"},
                    ],
                    "logic_chain": [
                        {"title_zh": "需求", "title_en": "Need"},
                        {"title_zh": "机会", "title_en": "Opportunity"},
                        {"title_zh": "价值", "title_en": "Value"},
                    ],
                },
            )
        )


def test_module_summary_is_structured_and_excludes_other_sources() -> None:
    responses = FakeResponses()
    result = summarise_module(
        course_title="Entrepreneurship",
        week_number=2,
        module_names=["Week 2"],
        module_items=["Overview"],
        module_text="Opportunity recognition starts from unmet needs.",
        announcements=[],
        language="中文",
        client=SimpleNamespace(responses=responses),
    )
    assert result["knowledge_map"][0]["title_en"] == "Opportunity Creation"
    assert result["walkthrough"][0]["module_label"] == "2.1 Overview"
    assert result["notices_and_preparation"][0]["kind"] == "workshop_preparation"
    system_prompt = responses.kwargs["input"][0]["content"]
    assert "Treat the WEEK as the unit of analysis" in system_prompt
    assert "both Simplified\nChinese and English" in system_prompt
    assert "Extract only explicit" in system_prompt
    assert validate_module_summary_coverage(
        result,
        expected_items=["2.1 Overview"],
        readable_items=["2.1 Overview"],
        announcement_titles=[],
    )

    missing_module = deepcopy(result)
    missing_module["walkthrough"] = []
    assert not validate_module_summary_coverage(
        missing_module,
        expected_items=["2.1 Overview"],
        readable_items=["2.1 Overview"],
        announcement_titles=[],
    )

    empty_map = deepcopy(result)
    empty_map["knowledge_map"] = []
    assert not validate_module_summary_coverage(
        empty_map,
        expected_items=["2.1 Overview"],
        readable_items=["2.1 Overview"],
        announcement_titles=[],
    )

    assert not validate_module_summary_coverage(
        result,
        expected_items=["2.1 Overview"],
        readable_items=["2.1 Overview"],
        announcement_titles=["Module 2 now live"],
    )
