from __future__ import annotations

from types import SimpleNamespace

from unisydneybuddy.pipeline.assignment_ai import AssignmentAnalysis, analyse_assignment_materials


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs = None

    def parse(self, **kwargs):
        self.kwargs = kwargs
        parsed = AssignmentAnalysis.model_validate(
            {
                "summary": "Analyse customer relationships.",
                "objective": "Produce an evidence-based case analysis.",
                "final_deliverables": ["Written report"],
                "key_requirements": [
                    {"text": "Use the supplied dataset", "level": "required", "source": "Canvas page", "evidence": "Use the supplied customer dataset"}
                ],
                "content_framework": [
                    {
                        "section": "Findings",
                        "purpose": "Answer the case question",
                        "required_content": ["Evidence-based findings"],
                        "evidence_suggestions": ["Customer dataset"],
                        "word_share": "About 50% (AI suggestion)",
                        "word_share_level": "ai_suggestion",
                        "level": "required",
                        "source": "Canvas page",
                        "evidence": "analyse the case",
                        "subsections": [
                            {
                                "title": "Key pattern",
                                "guidance": "Explain the pattern",
                                "writing_points": ["Result", "Interpretation"],
                                "level": "ai_plus_required",
                            }
                        ],
                    }
                ],
                "required_documents": [
                    {
                        "name": "Customer dataset",
                        "usage": "Complete the analysis",
                        "location": "Canvas > Assignment 2",
                        "requirement": "required",
                        "source": "Canvas page",
                        "evidence": "use the supplied customer dataset",
                    }
                ],
            }
        )
        return SimpleNamespace(output_parsed=parsed)


def test_assignment_ai_uses_structured_output_and_source_text() -> None:
    responses = FakeResponses()
    client = SimpleNamespace(responses=responses)
    result = analyse_assignment_materials(
        assignment={
            "title_original": "Case analysis",
            "mode": "individual",
            "weight_percent": 30,
            "due_at": "2026-09-07T23:59:00+10:00",
            "deliverables": [{"title_original": "Written report"}],
        },
        materials=[{"title": "Canvas page", "text": "Use the supplied customer dataset."}],
        language="English",
        client=client,
        model="test-model",
    )

    assert result["required_documents"][0]["name"] == "Customer dataset"
    assert responses.kwargs["model"] == "test-model"
    assert responses.kwargs["text_format"] is AssignmentAnalysis
    assert "Use the supplied customer dataset" in responses.kwargs["input"][1]["content"]


def test_assignment_ai_prompt_forbids_invented_document_lists() -> None:
    responses = FakeResponses()
    client = SimpleNamespace(responses=responses)
    analyse_assignment_materials(
        assignment={"title_original": "Reflection", "mode": "individual", "deliverables": []},
        materials=[{"title": "Brief", "text": "Write a reflection."}],
        language="中文",
        client=client,
    )
    system_prompt = responses.kwargs["input"][0]["content"]
    assert "ONLY" in system_prompt
    assert "empty list" in system_prompt
    assert "Simplified Chinese" in system_prompt
    assert "NEVER create structure nodes for uploading" in system_prompt
    assert "content_framework is the ONLY breakdown" in system_prompt
    assert "at most 3 high-value writing points" in system_prompt
    assert "Never use vague filler" in system_prompt
    assert "preserve its top-level section names" in system_prompt
    assert "ai_plus_required" in system_prompt
