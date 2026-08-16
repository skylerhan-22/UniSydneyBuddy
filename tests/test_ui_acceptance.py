from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
COURSES = ["QBUS6600", "MKTG6018", "MKTG6104", "SIEN6006"]


def render_app() -> AppTest:
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()


def select_course(app: AppTest, code: str) -> AppTest:
    next(button for button in app.button if button.label.startswith(code)).click().run()
    return app


def open_canvas_project(app: AppTest, project_key: str = "qbus6600-a2", code: str = "QBUS6600") -> AppTest:
    app.session_state[f"parsed-briefs-{code}"] = [{
        "filename": "Canvas Assignment 2",
        "input_kind": "canvas",
        "source_type": "canvas_assignment",
        "chunk_count": 2,
        "sha256": "canvas-test-source",
        "text": "Assignment description and visible rubric",
        "project_key": project_key,
    }]
    app.session_state[f"active-assignment-analysis-{code}"] = project_key
    return app.run()


def fake_analysis() -> dict:
    return {
        "summary": "AI assignment summary",
        "objective": "Produce an evidence-based assignment.",
        "final_deliverables": ["Written report"],
        "key_requirements": [
            {"text": "Use the supplied dataset", "level": "required", "source": "Key requirements page", "evidence": "key-only evidence"}
        ],
        "content_framework": [
            {"section": "Findings", "purpose": "Answer the question", "required_content": ["Connect evidence to the question"], "evidence_suggestions": ["Dataset findings"], "word_share": "About 50% (AI suggestion)", "word_share_level": "ai_suggestion", "level": "required", "source": "Brief", "evidence": "analyse the project", "subsections": [{"title": "Key finding", "guidance": "Explain the result", "writing_points": ["Result", "Meaning"], "level": "ai_plus_required"}]}
        ],
        "required_documents": [
            {"name": "Supplied dataset", "usage": "Complete the analysis", "location": "Canvas > Assignment 2", "requirement": "required", "source": "Brief", "evidence": "use the supplied dataset"}
        ],
    }


def seed_detected_analysis(app: AppTest, language: str = "中文") -> AppTest:
    app.session_state["ai-analyses-v2-QBUS6600"] = {
        "qbus6600-a2": {"source_signature": "test", "results_by_language": {language: fake_analysis()}}
    }
    return app.run()


def test_every_course_and_week_selector_value_renders() -> None:
    for code in COURSES:
        app = select_course(render_app(), code)
        for week_number in range(1, 14):
            next(item for item in app.selectbox if item.label == "周次").select(week_number).run()
            assert len(app.exception) == 0
            assert any(f"Week {week_number} ·" in item.value for item in app.markdown)


def test_course_button_active_state_matches_selected_content() -> None:
    app = select_course(render_app(), "MKTG6104")
    assert next(button for button in app.button if button.label.startswith("MKTG6104")).proto.type == "primary"
    assert any("MKTG6104 · Psychology of Marketing Decisions" in item.value for item in app.markdown)


def test_project_planner_has_canvas_first_flow_without_manual_upload_or_consent() -> None:
    app = render_app()
    assert len(app.text_area) == 0
    assert len(app.file_uploader) == 0
    assert len(app.checkbox) == 0
    assert not any(item.label in {"解析全部资料", "Analyse all material"} for item in app.button)
    assert any("canvas-assignment-card" in item.value for item in app.markdown)
    assert any("选择一项 Canvas 作业" in item.value for item in app.info)


def test_opened_canvas_assignment_has_dedicated_analysis_view() -> None:
    app = open_canvas_project(render_app())
    assert any("Assignment Analysis" in item.value for item in app.markdown)
    assert any("分析资料来自 Canvas" in item.value for item in app.caption)
    assert any(item.label == "AI 分析此作业" for item in app.button) or any("OpenAI API" in item.value for item in app.warning)
    assert any("尚未生成 AI 分析" in item.value for item in app.info)
    assert len(app.download_button) == 0


def test_seeded_ai_result_controls_group_planner() -> None:
    app = seed_detected_analysis(open_canvas_project(render_app()))
    assert any("Assignment Structure" in item.value for item in app.markdown)
    assert any("work-tree-root" in item.value for item in app.markdown)
    assert any("work-tree-module" in item.value for item in app.markdown)
    assert any("work-tree-part" in item.value for item in app.markdown)
    assert any("作业要求" in item.value for item in app.markdown)
    assert any("AI 拆解建议" in item.value for item in app.markdown)
    assert not any("key-only evidence" in item.value for item in app.caption)
    assert any("作业要求或建议使用的文档" in item.value for item in app.markdown)
    assert any(item.label == "确认小组分工" for item in app.button)
    export = next(item for item in app.download_button if item.label == "导出完整小组计划")
    assert export.proto.disabled is True


def test_group_export_requires_explicit_confirmation() -> None:
    app = seed_detected_analysis(open_canvas_project(render_app()))
    for owner_select in [item for item in app.selectbox if item.label == "本部分负责人"]:
        owner_select.select("A")
    app.run()
    next(button for button in app.button if button.label == "确认小组分工").click().run()
    export = next(item for item in app.download_button if item.label == "导出完整小组计划")
    assert export.proto.disabled is False


def test_required_document_cards_show_location_without_source_evidence() -> None:
    app = seed_detected_analysis(open_canvas_project(render_app()))
    assert any("Supplied dataset" in item.value for item in app.markdown)
    assert any("Canvas &gt; Assignment 2" in item.value for item in app.markdown)
    assert not any("use the supplied dataset" in item.value for item in app.caption)


def test_english_mode_has_equivalent_assignment_analysis_output() -> None:
    app = open_canvas_project(render_app())
    next(item for item in app.radio if item.options == ["中", "EN"]).set_value("EN").run()
    seed_detected_analysis(app, language="English")
    assert [tab.label for tab in app.tabs] == ["Semester Overview", "Weekly Brief", "Project Planner"]
    assert len(app.file_uploader) == 0
    assert any("Assignment Analysis" in item.value for item in app.markdown)
    assert any("AI-suggested length" in item.value for item in app.markdown)
    assert any("Documents required or recommended by the assignment" in item.value for item in app.markdown)


def test_language_switch_preserves_ai_result_and_group_state() -> None:
    app = seed_detected_analysis(open_canvas_project(render_app()))
    next(item for item in app.text_input if item.label == "成员 1").set_value("Alex").run()
    next(item for item in app.selectbox if item.label == "本部分负责人").select("Alex").run()
    next(item for item in app.radio if item.options == ["中", "EN"]).set_value("EN").run()
    assert any("English AI version" in item.value for item in app.info)
    next(item for item in app.radio if item.options == ["中", "EN"]).set_value("中").run()
    assert any("Assignment Structure" in item.value for item in app.markdown)
    assert next(item for item in app.text_input if item.label == "成员 1").value == "Alex"
    assert next(item for item in app.selectbox if item.label == "本部分负责人").value == "Alex"


def test_course_analysis_state_is_isolated() -> None:
    app = open_canvas_project(render_app())
    select_course(app, "MKTG6018")
    assert not any("Assignment Analysis · 作业 2" in item.value for item in app.markdown)
    select_course(app, "QBUS6600")
    assert any("Assignment Analysis" in item.value for item in app.markdown)
