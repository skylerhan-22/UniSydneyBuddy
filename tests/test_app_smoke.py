from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def render_app() -> AppTest:
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=10).run()


def upload_assignment_brief(app: AppTest) -> AppTest:
    code = app.session_state["selected_course"].split(" · ")[0]
    project_keys = {
        "QBUS6600": "qbus6600-a2",
        "MKTG6018": "MKTG6018-data-case-assignment",
        "MKTG6104": "MKTG6104-group-project",
        "SIEN6006": "SIEN6006-consulting-presentation",
    }
    project_key = project_keys[code]
    app.session_state[f"parsed-briefs-{code}"] = [{
        "filename": "Canvas Assignment",
        "input_kind": "canvas",
        "source_type": "canvas_assignment",
        "chunk_count": 2,
        "sha256": "test-canvas-source",
        "text": "Assignment brief and visible rubric",
        "project_key": project_key,
    }]
    app.session_state[f"active-assignment-analysis-{code}"] = project_key
    return app.run()


def seed_qbus_group_analysis(app: AppTest) -> AppTest:
    app.session_state["ai-analyses-v2-QBUS6600"] = {
        "qbus6600-a2": {
            "source_signature": "test",
            "results_by_language": {"中文": {
                "summary": "根据 Brief 生成的小组项目解析。",
                "objective": "完成一份基于证据的商业分析。",
                "final_deliverables": ["Written report"],
                "key_requirements": [
                    {"text": "使用指定数据", "level": "required", "source": "Assignment Brief", "evidence": "use the supplied dataset"}
                ],
                "content_framework": [{"section": "业务问题", "purpose": "回答核心问题", "required_content": ["使用证据回答问题"], "evidence_suggestions": ["数据结果"], "word_share": "约 40%（AI 建议）", "word_share_level": "ai_suggestion", "level": "required", "source": "Assignment Brief", "evidence": "analyse the business problem", "subsections": [{"title": "核心发现", "guidance": "解释发现", "writing_points": ["结果", "含义"], "level": "ai_plus_required"}]}],
                "required_documents": [{"name": "Assignment Brief", "usage": "核对要求", "location": "Canvas > Assignment 2", "requirement": "required", "source": "Canvas", "evidence": "follow the Assignment Brief"}],
            }},
        }
    }
    return app.run()


def test_student_demo_renders_without_runtime_errors() -> None:
    app = render_app()
    assert len(app.exception) == 0
    assert [tab.label for tab in app.tabs] == ["学期总览", "每周简报", "项目计划"]


def test_engineering_features_are_not_student_navigation() -> None:
    app = render_app()
    labels = [tab.label for tab in app.tabs]
    assert "通知变更" not in labels
    assert "Eval" not in labels
    assert all("本地隐私模式" not in success.value for success in app.success)


def test_weekly_brief_is_chinese_and_has_no_todo_panel() -> None:
    app = render_app()
    markdown_values = [item.value for item in app.markdown]
    assert any("当前课程尚未同步或未在 Canvas Connector 结果中匹配" in item.value for item in app.info)
    assert not any("brief-text-title'>Lecture / Recording" in value for value in markdown_values)
    assert not any("brief-text-title'>Tutorial / Workshop" in value for value in markdown_values)
    assert not any("To-do" in value for value in markdown_values)


def test_course_menu_contains_all_current_courses() -> None:
    app = render_app()
    course_buttons = [item for item in app.button if item.label.split(" · ")[0] in {"QBUS6600", "MKTG6018", "MKTG6104", "SIEN6006"}]
    assert len(course_buttons) == 4
    assert course_buttons[0].label.startswith("QBUS6600")


def test_course_button_updates_selected_course_before_render() -> None:
    app = render_app()
    mktg_button = next(item for item in app.button if item.label.startswith("MKTG6018"))
    mktg_button.click().run()
    assert app.session_state["selected_course"].startswith("MKTG6018")
    assert any("客户关系管理" in item.value for item in app.markdown)
    assert len(app.file_uploader) == 0
    upload_assignment_brief(app)
    assert any("Assignment Analysis" in item.value for item in app.markdown)
    assert not any(item.label == "确认小组分工" for item in app.button)


def test_all_remaining_courses_render_real_content() -> None:
    expected = {
        "MKTG6018": "客户关系管理",
        "MKTG6104": "心理偏差",
        "SIEN6006": "创业与创新",
    }
    for code, phrase in expected.items():
        app = render_app()
        next(item for item in app.button if item.label.startswith(code)).click().run()
        assert len(app.exception) == 0
        assert any(phrase in item.value for item in app.markdown)
        assert len(app.dataframe) == 0
        assert any("canvas-assignment-card" in item.value for item in app.markdown)
        assert sum("summary-card" in item.value for item in app.markdown) >= 10


def test_mktg6104_group_project_preview_preserves_team_size() -> None:
    app = render_app()
    next(item for item in app.button if item.label.startswith("MKTG6104")).click().run()
    upload_assignment_brief(app)
    metric_values = [item.value for item in app.metric]
    assert "45%" in metric_values
    assert "4–6" in metric_values
    assert not any(item.label == "小组人数" for item in app.selectbox)
    assert any("尚未生成 AI 分析" in item.value for item in app.info)


def test_sidebar_removes_redundant_navigation_labels() -> None:
    app = render_app()
    markdown_values = [item.value for item in app.sidebar.markdown]
    assert not any("SKILL HUB" in value for value in markdown_values)
    assert not any("课程菜单" in value for value in markdown_values)
    assert not any(">学期<" in value for value in markdown_values)


def test_learning_overview_cards_and_project_detail_render() -> None:
    app = render_app()
    upload_assignment_brief(app)
    markdown_values = [item.value for item in app.markdown]
    assert any("Learning Overview · Week 1–13" in value for value in markdown_values)
    assert any("week-summary" in value for value in markdown_values)
    assert not any("Session details" in value for value in markdown_values)
    assert any("作业资料" in value for value in markdown_values)
    assert not any("详细执行计划" in value for value in markdown_values)
    assert any(item.label == "AI 分析此作业" for item in app.button) or any("OpenAI API" in item.value for item in app.warning)


def test_required_documents_show_locations_without_template_downloads() -> None:
    app = seed_qbus_group_analysis(upload_assignment_brief(render_app()))
    labels = [button.label for button in app.download_button]
    assert "下载全部作业模板（ZIP）" not in labels
    assert "下载模板" not in labels
    assert any("Assignment Brief" in item.value for item in app.markdown)
    assert any("Canvas &gt; Assignment 2" in item.value for item in app.markdown)
    assert not any("建议位置" in item.value for item in app.markdown)


def test_group_size_controls_number_of_member_fields() -> None:
    app = seed_qbus_group_analysis(upload_assignment_brief(render_app()))
    member_inputs = [item for item in app.text_input if item.label.startswith("成员 ")]
    assert len(member_inputs) == 3
    team_size = next(item for item in app.selectbox if item.label == "小组人数")
    team_size.select(4).run()
    member_inputs = [item for item in app.text_input if item.label.startswith("成员 ")]
    assert len(member_inputs) == 4


def test_part_confirmation_requires_every_owner() -> None:
    app = seed_qbus_group_analysis(upload_assignment_brief(render_app()))
    confirm = next(button for button in app.button if button.label == "确认小组分工")
    confirm.click().run()
    assert any("请先为每个作业部分选择负责人" in error.value for error in app.error)
