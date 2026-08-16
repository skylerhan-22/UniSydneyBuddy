from __future__ import annotations

import json
import hashlib
from html import escape, unescape
from importlib import reload
import os
from pathlib import Path
import re
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import streamlit as st

from unisydneybuddy.demo import (
    build_project_markdown,
    format_due,
    localized,
)
from unisydneybuddy.canvas_bridge import load_canvas_snapshot, start_canvas_bridge, validate_canvas_snapshot
from unisydneybuddy.canvas_assignments import canvas_assignment_material, match_canvas_assignment
from unisydneybuddy.pipeline import assignment_ai as assignment_ai_module
from unisydneybuddy.pipeline.module_ai import summarise_module, validate_module_summary_coverage
from unisydneybuddy.state_store import load_json_state, record_snapshot, save_feedback, save_json_state, snapshot_changes


ANALYSIS_SCHEMA_VERSION = 4
if "work_modules" in assignment_ai_module.AssignmentAnalysis.model_fields:
    assignment_ai_module = reload(assignment_ai_module)
analyse_assignment_materials = assignment_ai_module.analyse_assignment_materials


ROOT = Path(__file__).resolve().parent
CANVAS_SNAPSHOT_PATH = Path(
    os.environ.get("CANVAS_SNAPSHOT_PATH", ROOT / "data" / "local" / "canvas_snapshot.json")
)
APP_DB_PATH = Path(os.environ.get("APP_DB_PATH", ROOT / "data" / "app.db"))
CANVAS_SYNC_API_URL = os.environ.get("CANVAS_SYNC_API_URL", "").rstrip("/")


@st.cache_resource
def canvas_bridge_running() -> bool:
    return start_canvas_bridge(CANVAS_SNAPSHOT_PATH)


if not CANVAS_SYNC_API_URL:
    canvas_bridge_running()


@st.cache_data
def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_remote_canvas_snapshot(base_url: str, sync_id: str) -> dict | None:
    if not base_url or not re.fullmatch(r"[A-Za-z0-9_-]{16,80}", sync_id):
        return None
    try:
        with urlopen(f"{base_url}/canvas-snapshot?{urlencode({'sync_id': sync_id})}", timeout=4) as response:
            return validate_canvas_snapshot(json.loads(response.read().decode("utf-8")))
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return None


def tr(language: str, zh: str, en: str) -> str:
    return zh if language == "中文" else en


def feedback_form(*, context: str, course_code: str, language: str, user_namespace: str) -> None:
    with st.expander(tr(language, "反馈这个结果", "Give feedback")):
        with st.form(f"feedback-{context}-{course_code}-{language}", clear_on_submit=True):
            rating = st.radio(
                tr(language, "这个结果怎么样？", "How was this result?"),
                [tr(language, "有帮助", "Helpful"), tr(language, "内容遗漏", "Missing content"), tr(language, "不准确", "Inaccurate")],
                horizontal=True,
            )
            comment = st.text_area(
                tr(language, "补充说明（选填）", "Comment (optional)"),
                placeholder=tr(language, "告诉我们哪里需要改进", "Tell us what should improve"),
            )
            submitted = st.form_submit_button(tr(language, "提交反馈", "Submit feedback"))
        if submitted:
            save_feedback(
                APP_DB_PATH,
                context=f"{user_namespace}:{context}",
                course_code=course_code,
                language=language,
                rating=rating,
                comment=comment,
            )
            st.success(tr(language, "反馈已保存，谢谢。", "Feedback saved. Thank you."))


def configure_openai_api_key() -> bool:
    """Load the API key from the process or local Streamlit secrets."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        try:
            key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()
        except Exception:
            key = ""
    if key:
        os.environ["OPENAI_API_KEY"] = key
    return bool(key)


def analysis_badge(level: str, language: str) -> str:
    labels = {
        "required": tr(language, "必须要求", "Required"),
        "source_recommended": tr(language, "原文建议", "Source recommendation"),
        "ai_plus_required": tr(language, "AI＋要求", "AI + requirement"),
        "ai_plus_recommended": tr(language, "AI＋建议", "AI + recommendation"),
        "ai_suggestion": tr(language, "AI 建议", "AI suggestion"),
        "recommended": tr(language, "原文建议", "Source recommendation"),
    }
    css_level = level.replace("_", "-")
    return f"<span class='analysis-badge badge-{css_level}'>{escape(labels.get(level, level))}</span>"


def analysis_list(items: list[str]) -> None:
    if not items:
        return
    rows = "".join(f"<li>{escape(str(item))}</li>" for item in items)
    st.markdown(f"<ul class='analysis-list'>{rows}</ul>", unsafe_allow_html=True)


def source_evidence(item: dict, language: str) -> None:
    source = item.get("source") or tr(language, "上传资料", "Uploaded material")
    with st.expander(tr(language, f"来源 · {source}", f"Source · {source}")):
        st.caption(item.get("evidence") or "—")


def content_origin(level: str, language: str) -> tuple[str, str]:
    if level == "required":
        return tr(language, "作业要求", "Assignment requirement"), "source"
    if level == "source_recommended":
        return tr(language, "作业建议", "Assignment recommendation"), "recommended"
    if level in {"ai_plus_required", "ai_plus_recommended"}:
        return tr(language, "AI 拆解建议", "AI breakdown suggestion"), "ai"
    return tr(language, "AI 建议", "AI suggestion"), "ai"


def structure_tree_html(title: str, framework: list[dict]) -> str:
    section_rows: list[str] = []
    for section_index, section in enumerate(framework, start=1):
        subsections = "".join(
            "<li><span class='work-tree-part'>"
            f"{section_index}.{subsection_index} · {escape(subsection['title'])}"
            "</span></li>"
            for subsection_index, subsection in enumerate(section["subsections"], start=1)
        )
        child_tree = f"<ul>{subsections}</ul>" if subsections else ""
        section_rows.append(
            "<li><span class='work-tree-module'>"
            f"{section_index:02d} · {escape(section['section'])}"
            f"</span>{child_tree}</li>"
        )
    return (
        "<div class='work-tree'><ul><li>"
        f"<span class='work-tree-root'>{escape(title)}</span>"
        f"<ul>{''.join(section_rows)}</ul>"
        "</li></ul></div>"
    )


def annotated_content(level: str, text: str, language: str, items: list[str] | None = None) -> None:
    label, css_kind = content_origin(level, language)
    list_html = ""
    if items:
        list_html = "<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in items) + "</ul>"
    st.markdown(
        "<div class='content-annotation'>"
        f"<div class='content-origin origin-{css_kind}'>{escape(label)}</div>"
        f"<div class='content-annotation-copy'>{escape(text)}{list_html}</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def summary_card(title: str, body: str, *, label: str | None = None, items: list[str] | None = None) -> None:
    label_html = f"<div class='summary-card-label'>{escape(label)}</div>" if label else ""
    items_html = ""
    if items:
        items_html = "<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in items) + "</ul>"
    st.markdown(
        "<div class='summary-card'>"
        f"{label_html}<div class='summary-card-title'>{escape(title)}</div>"
        f"<div class='summary-card-copy'>{escape(body)}{items_html}</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def text_brief_section(title: str, body: str, *, label: str | None = None, items: list[str] | None = None) -> None:
    label_html = f"<div class='brief-text-label'>{escape(label)}</div>" if label else ""
    items_html = ""
    if items:
        items_html = "<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in items) + "</ul>"
    st.markdown(
        "<section class='brief-text-section'>"
        f"{label_html}<div class='brief-text-title'>{escape(title)}</div>"
        f"<div class='brief-text-copy'>{escape(body)}{items_html}</div>"
        "</section>",
        unsafe_allow_html=True,
    )


def stacked_bilingual_label(title_zh: str, title_en: str, language: str) -> str:
    primary, secondary = (title_en, title_zh) if language == "English" else (title_zh, title_en)
    return (
        f"<span class='knowledge-keyword-primary'>{escape(primary)}</span>"
        f"<span class='knowledge-keyword-secondary'>{escape(secondary)}</span>"
    )


def render_week_knowledge_map(module_analysis: dict, language: str) -> None:
    root_title = stacked_bilingual_label(
        module_analysis["central_topic_zh"], module_analysis["central_topic_en"], language
    )
    branches_html = []
    for branch in module_analysis["knowledge_map"]:
        branch_title = stacked_bilingual_label(branch["title_zh"], branch["title_en"], language)
        points = "".join(
            "<div class='knowledge-leaf'>"
            f"{stacked_bilingual_label(point['title_zh'], point['title_en'], language)}"
            "</div>"
            for point in branch["points"]
        )
        branches_html.append(
            "<div class='knowledge-branch'>"
            f"<div class='knowledge-branch-title'>{branch_title}</div>"
            f"<div class='knowledge-leaves'>{points}</div>"
            "</div>"
        )
    st.html(
        "<div class='knowledge-tree'>"
        f"<div class='knowledge-root'>{root_title}</div>"
        "<div class='knowledge-trunk' aria-hidden='true'></div>"
        f"<div class='knowledge-branches'>{''.join(branches_html)}</div>"
        "</div>"
    )


def evidence_block(language: str, evidence_ids: list[str], evidence_map: dict[str, dict]) -> None:
    with st.expander(tr(language, "课程来源", "Course sources")):
        for evidence_id in evidence_ids:
            item = evidence_map[evidence_id]
            st.markdown(f"**{item['source_title']} · {item['locator']}**")
            st.caption(item.get("excerpt") or "—")


def category_for(item: dict, language: str) -> str:
    if item["id"] == "qbus6600-a1":
        return tr(language, "个人数据分析", "Individual data analysis")
    if item["id"] == "qbus6600-a2":
        return "Group Project"
    return tr(language, "个人反思", "Individual reflection")


def localized_duration(item: dict, language: str) -> str:
    raw = item.get("duration", "—")
    if language == "English":
        return item.get("duration_en", raw)
    duration_labels = {
        "1 hour": "1小时",
        "1.5 hours": "1.5小时",
        "2 hours": "2小时",
        "3 hours": "3小时",
        "Allocated timetable slot": "以个人课表安排为准",
        "Monday 13:30–15:00": "星期一 13:30–15:00",
    }
    return duration_labels.get(raw, raw)


def localized_week_session(item: dict, field: str, language: str) -> str:
    raw = item.get(field) or ""
    if language == "English":
        return raw or "Not scheduled"
    lowered = raw.lower()
    if not raw:
        return "未安排"
    if lowered.startswith("no lecture"):
        return "本周无 Lecture（公共假期）" if "public holiday" in lowered else "本周无 Lecture"
    if lowered.startswith("no workshop"):
        return "Unit Outline 未安排 Workshop"
    topic = item.get("title_zh") or item.get("title_en") or "本周主题"
    if field == "lecture":
        return topic
    return f"围绕“{topic}”开展；详细活动内容尚未导入"


def plain_canvas_text(value: str, limit: int = 520) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = re.sub(r"\s+", " ", unescape(text)).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def canvas_week_extract(course: dict | None, week_number: int) -> dict | None:
    if not course:
        return None
    week_pattern = re.compile(rf"\bweek\s*0?{week_number}\b", re.IGNORECASE)
    item_prefix_pattern = re.compile(rf"^\s*{week_number}\.\d+\b")
    matching_modules = [
        module
        for module in course.get("modules", [])
        if week_pattern.search(module.get("name", ""))
        or any(item_prefix_pattern.search(item.get("title", "")) for item in module.get("items", []))
    ]
    if not matching_modules:
        return None
    module_items: list[str] = []
    readable_module_items: list[str] = []
    page_sections: list[str] = []
    for module in matching_modules:
        for item in module.get("items", []):
            title = item.get("title") or "Canvas item"
            module_items.append(title)
            page_text = plain_canvas_text((item.get("page") or {}).get("body", ""), limit=12000)
            if page_text:
                readable_module_items.append(title)
                page_sections.append(f"{title}\n{page_text}")
            else:
                page_sections.append(f"{title}\n[NO READABLE BODY SYNCED]")
    announcement_pattern = re.compile(rf"\b(?:week|module)\s*0?{week_number}\b", re.IGNORECASE)
    announcements = []
    for announcement in course.get("announcements", []):
        title = announcement.get("title") or "Canvas announcement"
        message = plain_canvas_text(announcement.get("message", ""), limit=2500)
        if announcement_pattern.search(f"{title} {message}"):
            announcements.append(
                {
                    "title": title,
                    "message": message,
                    "posted_at": announcement.get("posted_at") or "",
                }
            )
    content_text = "\n\n".join(page_sections)[:30000]
    source_preview = plain_canvas_text(content_text, limit=1800)
    return {
        "module_names": [module.get("name", "") for module in matching_modules],
        "module_items": list(dict.fromkeys(module_items))[:20],
        "readable_module_items": list(dict.fromkeys(readable_module_items))[:20],
        "announcements": announcements,
        "content_text": content_text,
        "source_preview": source_preview,
    }


def select_course(course: str) -> None:
    st.session_state.selected_course = course


st.set_page_config(page_title="UniSydneyBuddy", page_icon="🎓", layout="wide")
st.markdown(
    """
    <style>
    .stApp {background:#fbfaf8; color:#303030;}
    #MainMenu, [data-testid="stAppDeployButton"] {display:none !important;}
    [data-testid="stSidebar"] {background:#e64626;}
    [data-testid="stSidebar"] * {color:#fff;}
    [data-testid="stSidebar"] div[role="radiogroup"] {position:fixed; bottom:22px; left:26px; width:145px; z-index:99; background:rgba(255,255,255,.16); padding:5px 8px; border-radius:10px;}
    [data-testid="stSidebar"] div[role="radiogroup"] label {padding:0 .35rem;}
    [data-testid="stSidebar"] .stButton button {justify-content:flex-start; min-height:2.7rem; padding:.55rem .7rem; border:1px solid rgba(255,255,255,.42); background:rgba(255,255,255,.08); text-align:left;}
    [data-testid="stSidebar"] .stButton button p {width:100%; text-align:left !important;}
    [data-testid="stSidebar"] .stButton button[kind="secondary"] * {color:#fff !important; font-size:.82rem; line-height:1.25;}
    [data-testid="stSidebar"] .stButton button[kind="primary"] {background:#fff; border-color:#fff;}
    [data-testid="stSidebar"] .stButton button[kind="primary"] * {color:#c8381d !important; font-size:.82rem; line-height:1.25;}
    .semester-value {font-size:1rem; font-weight:750; padding:.35rem 0 .7rem; border-bottom:1px solid rgba(255,255,255,.35); margin-bottom:.65rem;}
    .course-title {display:flex; justify-content:space-between; align-items:end; gap:1rem; padding:.35rem 0 1rem; border-bottom:3px solid #e64626; margin-bottom:.8rem;}
    .course-title-text {margin:0; font-size:2rem !important; line-height:1.2; font-weight:800; color:#282828; letter-spacing:-.025em;}
    .course-title span {font-size:.9rem; color:#777; white-space:nowrap; padding-bottom:.15rem;}
    .compact-title {font-size:1.3rem; line-height:1.35; font-weight:760; margin:.55rem 0 .7rem; color:#303030;}
    .weekly-title {font-size:1.55rem; line-height:1.3; font-weight:780; margin:.35rem 0 .8rem; color:#2b2b2b;}
    .course-summary {padding:.9rem 1rem; background:#fff; border:1px solid #eee3dc; border-radius:8px; line-height:1.7; margin-bottom:.8rem;}
    .demo-status {padding:.68rem .85rem; margin:.15rem 0 1rem; background:#fff7f2; border-left:4px solid #e64626; border-radius:0 8px 8px 0; color:#675851; font-size:.84rem; line-height:1.55;}
    .summary-card {height:100%; padding:.9rem 1rem; margin:.15rem 0 .65rem; background:#fff; border:1px solid #eee3dc; border-radius:10px;}
    .summary-card-label {font-size:.7rem; font-weight:820; color:#bd3c23; letter-spacing:.055em; text-transform:uppercase; margin-bottom:.28rem;}
    .summary-card-title {font-size:1rem; line-height:1.4; font-weight:790; color:#332f2d; margin-bottom:.3rem;}
    .summary-card-copy {font-size:.86rem; line-height:1.6; color:#655d59;}
    .summary-card-copy ul {margin:.4rem 0 0; padding-left:1.05rem;}
    .summary-card-copy li {margin:.25rem 0;}
    .assessment-meta {display:flex; flex-wrap:wrap; gap:.35rem; margin:.35rem 0 .5rem;}
    .assessment-tag {display:inline-flex; padding:.18rem .48rem; border-radius:999px; background:#f8eee9; color:#99412e; font-size:.7rem; font-weight:760;}
    .canvas-assignment-card {min-height:10.4rem; padding:1rem 1.05rem; margin:.15rem 0 .45rem; background:#fff; border:1px solid #eee3dc; border-radius:10px;}
    .canvas-assignment-source {font-size:.7rem; font-weight:820; color:#bd3c23; letter-spacing:.055em; text-transform:uppercase; margin-bottom:.3rem;}
    .canvas-assignment-title {font-size:1.02rem; line-height:1.4; font-weight:790; color:#332f2d; margin-bottom:.45rem;}
    .canvas-assignment-status {font-size:.82rem; line-height:1.55; color:#655d59; margin-top:.55rem;}
    .week-summary {padding:1rem 1.1rem; margin:.25rem 0 1rem; background:linear-gradient(135deg,#fff 0%,#fff7f2 100%); border:1px solid #f0d8cc; border-left:5px solid #e64626; border-radius:12px;}
    .week-summary-title {font-size:.76rem; color:#b43b23; font-weight:820; letter-spacing:.07em; text-transform:uppercase; margin-bottom:.3rem;}
    .week-summary-copy {font-size:.96rem; line-height:1.7; color:#47403c;}
    .brief-text-flow {margin:.2rem 0 1rem; border-top:1px solid #ded6d1;}
    .module-coverage {font-size:.86rem; line-height:1.55; color:#6a625d; margin:-.35rem 0 1.15rem;}
    .knowledge-tree {display:grid; grid-template-columns:minmax(155px,.7fr) 34px minmax(0,2fr); align-items:center; margin:.2rem 0 1.5rem;}
    .knowledge-root {padding:.9rem 1rem; background:#fff1ea; border-left:5px solid #e64626; border-radius:10px; font-weight:760; color:#332b27;}
    .knowledge-trunk {height:1px; background:#d8b7a8;}
    .knowledge-branches {display:grid; gap:.7rem; border-left:1px solid #d8b7a8; padding-left:1rem;}
    .knowledge-branch {display:grid; grid-template-columns:minmax(145px,.75fr) minmax(0,1.6fr); align-items:center; gap:.8rem; position:relative;}
    .knowledge-branch:before {content:""; position:absolute; left:-1rem; width:1rem; border-top:1px solid #d8b7a8;}
    .knowledge-branch-title {background:#f8f2ef; border-radius:8px; padding:.7rem .8rem; font-weight:720; color:#3e3632;}
    .knowledge-leaves {display:grid; gap:.35rem;}
    .knowledge-leaf {padding:.35rem 0 .45rem; border-bottom:1px solid #ece4df; color:#514945; line-height:1.45;}
    .knowledge-leaf:last-child {border-bottom:0;}
    .knowledge-keyword-primary {display:block; font-weight:780; line-height:1.35; color:inherit;}
    .knowledge-keyword-secondary {display:block; margin-top:.12rem; font-size:.78rem; line-height:1.35; font-weight:560; color:#8a746a;}
    .walkthrough-flow {margin:.1rem 0 1.2rem; border-top:1px solid #ded6d1;}
    .walkthrough-module {padding:1.25rem 0; border-bottom:1px solid #ded6d1;}
    .walkthrough-module-title {font-size:1.12rem; line-height:1.4; font-weight:800; color:#302d2b; margin-bottom:.55rem;}
    .walkthrough-module-overview {font-size:.94rem; line-height:1.8; color:#514b48; max-width:72rem; margin-bottom:.8rem;}
    .walkthrough-subsection {display:grid; grid-template-columns:minmax(130px,.28fr) minmax(0,1fr); gap:1rem; padding:.7rem 0; border-top:1px solid #eee7e3;}
    .walkthrough-subsection-title {font-size:.88rem; line-height:1.55; font-weight:780; color:#b43b23;}
    .walkthrough-subsection-copy {font-size:.92rem; line-height:1.78; color:#514b48;}
    .weekly-action-grid {display:grid; grid-template-columns:1fr 1fr; gap:.85rem; margin:.2rem 0 1.2rem;}
    .weekly-action-card {height:100%; padding:1rem 1.05rem; background:#fff; border:1px solid #eee3dc; border-top:4px solid #e64626; border-radius:10px;}
    .weekly-action-title {font-size:1rem; line-height:1.4; font-weight:800; color:#332f2d; margin-bottom:.55rem;}
    .weekly-action-item {font-size:.88rem; line-height:1.65; color:#5d5551; padding:.5rem 0; border-top:1px solid #eee7e3;}
    .weekly-action-item:first-of-type {border-top:0; padding-top:0;}
    .weekly-action-item strong {display:block; color:#3d3632; margin-bottom:.12rem;}
    .weekly-action-detail {display:block; margin-top:.28rem;}
    .weekly-action-empty {font-size:.86rem; line-height:1.6; color:#8a817c;}
    .one-view {margin:1rem 0; padding:1.1rem 1.2rem; background:#2c2724; color:#fffaf7; border-radius:12px;}
    .one-view-title {font-size:1.06rem; font-weight:780; margin-bottom:.6rem;}
    .one-view-core {line-height:1.65; margin-bottom:.7rem;}
    .one-view ol {margin:.3rem 0 .8rem; padding-left:1.3rem;}
    .one-view li {margin:.28rem 0; line-height:1.55;}
    .one-view-chain {color:#ffc0aa; font-weight:720; line-height:1.5;}
    @media (max-width:700px) {
        .knowledge-tree {grid-template-columns:1fr; gap:.55rem;}
        .knowledge-trunk {width:1px; height:18px; justify-self:center;}
        .knowledge-branches {border-left:0; padding-left:0;}
        .knowledge-branch {grid-template-columns:1fr; gap:.3rem;}
        .knowledge-branch:before {display:none;}
        .walkthrough-subsection {grid-template-columns:1fr; gap:.2rem;}
        .weekly-action-grid {grid-template-columns:1fr;}
    }
    .brief-text-section {padding:1rem .05rem; border-bottom:1px solid #ded6d1;}
    .brief-text-label {font-size:.7rem; line-height:1.4; color:#b43b23; font-weight:820; letter-spacing:.06em; text-transform:uppercase; margin-bottom:.22rem;}
    .brief-text-title {font-size:1.05rem; line-height:1.45; font-weight:800; color:#302d2b; margin-bottom:.24rem;}
    .brief-text-copy {font-size:.92rem; line-height:1.75; color:#514b48; max-width:72rem;}
    .brief-text-copy ul {margin:.45rem 0 0; padding-left:1.2rem;}
    .brief-text-copy li {margin:.28rem 0;}
    div[data-testid="stTabs"] button {font-weight:750; font-size:1rem;}
    div[data-testid="stTabs"] button[aria-selected="true"] {color:#d63d20; border-bottom-color:#e64626;}
    div.stButton > button[kind="primary"] {background:#e64626; border-color:#e64626;}
    div.stDownloadButton > button {border-color:#e64626; color:#c8381d;}
    div[data-testid="stMetric"] {padding:.6rem .75rem; border:1px solid #eee4de; border-radius:8px; background:#fff;}
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {font-size:.86rem;}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {font-size:1.65rem; line-height:1.25;}
    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {border:1px solid #ece3dd; border-radius:8px; overflow:hidden;}
    .reference-note {font-size:.78rem; color:#74645e; margin:.25rem 0 .7rem;}
    .file-row {padding:.55rem .1rem; border-bottom:1px solid #eee4de;}
    .file-name {font-size:.96rem; font-weight:730; color:#303030;}
    .file-purpose {font-size:.82rem; color:#70645f; line-height:1.45;}
    .analysis-hero {padding:1.15rem 1.25rem; background:linear-gradient(135deg,#fff 0%,#fff7f2 100%); border:1px solid #f0d8cc; border-left:5px solid #e64626; border-radius:12px; margin:.75rem 0 1.25rem;}
    .analysis-kicker {font-size:.76rem; color:#b43b23; font-weight:800; letter-spacing:.08em; text-transform:uppercase; margin-bottom:.35rem;}
    .analysis-objective {font-size:1.08rem; line-height:1.7; font-weight:650; color:#332f2d; margin:.15rem 0 .65rem;}
    .analysis-summary {font-size:.92rem; line-height:1.7; color:#655b56; margin:0;}
    .analysis-section {display:flex; align-items:center; gap:.65rem; margin:1.55rem 0 .8rem;}
    .analysis-section-number {display:inline-flex; align-items:center; justify-content:center; width:2rem; height:2rem; border-radius:8px; background:#e64626; color:#fff; font-size:.78rem; font-weight:850;}
    .analysis-section-title {font-size:1.35rem; font-weight:800; color:#2f2d2c;}
    .analysis-card-title {font-size:1.08rem; font-weight:800; color:#302d2b; margin-bottom:.35rem;}
    .analysis-card-copy {font-size:.93rem; line-height:1.7; color:#514b48; margin:.15rem 0 .65rem;}
    .analysis-label {font-size:.76rem; font-weight:800; color:#84756e; letter-spacing:.035em; text-transform:uppercase; margin:.5rem 0 .15rem;}
    .analysis-badge {display:inline-flex; align-items:center; border-radius:999px; padding:.18rem .55rem; font-size:.7rem; line-height:1.35; font-weight:800; border:1px solid transparent; white-space:nowrap;}
    .badge-required {background:#fff0ed; color:#b32d1e; border-color:#f2c0b8;}
    .badge-source-recommended, .badge-recommended {background:#fff7dc; color:#82620a; border-color:#ead68b;}
    .badge-ai-plus-required {background:#f4edff; color:#65419a; border-color:#d8c3f1;}
    .badge-ai-plus-recommended {background:#eef5ff; color:#325f93; border-color:#c8daf1;}
    .badge-ai-suggestion {background:#edf6f1; color:#31694e; border-color:#c5dfd1;}
    .analysis-list {margin:.25rem 0 .7rem; padding-left:1.15rem; color:#4d4845;}
    .analysis-list li {margin:.3rem 0; line-height:1.55;}
    .work-tree {overflow-x:auto; padding:1rem 1.1rem; margin:.25rem 0 1rem; background:#fff; border:1px solid #eee1da; border-radius:12px;}
    .work-tree ul {position:relative; list-style:none; margin:0; padding-left:1.7rem; min-width:max-content;}
    .work-tree > ul {padding-left:0;}
    .work-tree ul ul::before {content:""; position:absolute; top:0; bottom:1rem; left:.55rem; border-left:2px solid #e6b8a8;}
    .work-tree li {position:relative; margin:.6rem 0; padding-left:1.2rem;}
    .work-tree > ul > li {padding-left:0; margin:0;}
    .work-tree ul ul > li::before {content:""; position:absolute; top:1rem; left:-1.15rem; width:1.75rem; border-top:2px solid #e6b8a8;}
    .work-tree ul ul > li:last-child::after {content:""; position:absolute; top:1.05rem; bottom:-.65rem; left:-1.2rem; width:5px; background:#fff;}
    .work-tree-root,.work-tree-module,.work-tree-part {position:relative; z-index:1; display:inline-block; border-radius:8px; line-height:1.35;}
    .work-tree-root {padding:.55rem .8rem; background:#e64626; color:#fff; font-weight:820;}
    .work-tree-module {padding:.48rem .7rem; background:#f7e9e3; border:1px solid #e8c5b8; color:#7e3020; font-weight:790;}
    .work-tree-part {padding:.43rem .65rem; background:#fffaf7; border:1px solid #eadfd9; color:#443d39; font-size:.88rem; font-weight:650;}
    .module-heading {padding:.65rem .8rem; margin:1rem 0 .55rem; background:#f8eee9; border-left:4px solid #e64626; border-radius:0 8px 8px 0;}
    .module-heading-title {font-size:1rem; font-weight:820; color:#3b332f;}
    .module-heading-copy {font-size:.84rem; color:#71645e; margin-top:.15rem;}
    .structure-deliverable {padding:.7rem .85rem; margin:-.15rem 0 .55rem; background:#fff7f2; border-left:3px solid #e64626; border-radius:0 8px 8px 0; color:#514944; font-size:.9rem; line-height:1.6;}
    .word-share-tag {display:inline-flex; align-items:center; margin-left:.5rem; padding:.2rem .52rem; border-radius:999px; background:#fff1eb; border:1px solid #efc2b4; color:#a83a23; font-size:.72rem; line-height:1.35; font-weight:780; vertical-align:middle;}
    .content-annotation {display:grid; grid-template-columns:9rem 1fr; gap:.85rem; padding:.7rem 0; border-top:1px dashed #e6ddd8;}
    .content-annotation:first-of-type {border-top:0;}
    .content-origin {font-size:.76rem; font-weight:820; line-height:1.5;}
    .origin-source {color:#356fa4;}
    .origin-recommended {color:#8a6810;}
    .origin-ai {color:#c43d21;}
    .content-annotation-copy {font-size:.9rem; line-height:1.65; color:#4e4845;}
    .content-annotation-copy ul {margin:.35rem 0 0; padding-left:1.1rem;}
    .content-annotation-copy li {margin:.28rem 0;}
    .framework-child {padding:.75rem .9rem; margin:.55rem 0; background:#faf8f6; border-left:3px solid #d8c3b8; border-radius:0 8px 8px 0;}
    .framework-child-title {font-weight:780; color:#373230; margin-bottom:.3rem;}
    .document-location {display:inline-flex; padding:.28rem .55rem; border-radius:6px; background:#f5f1ee; color:#6d5e57; font-size:.78rem; margin:.25rem 0 .45rem;}
    @media (max-width:700px) {.content-annotation {grid-template-columns:1fr; gap:.15rem;}}
    </style>
    """,
    unsafe_allow_html=True,
)

gold = load_json(ROOT / "data" / "evals" / "qbus6600_gold.json")
schedule = load_json(ROOT / "data" / "evals" / "qbus6600_schedule.json")
remaining_courses = load_json(ROOT / "data" / "evals" / "remaining_courses.json")
evidence_map = {item["id"]: item for item in gold["evidence"]}
assignment_2 = next(item for item in gold["assessments"] if item["id"] == "qbus6600-a2")

language_switch = st.sidebar.radio(
    "Language",
    ["中", "EN"],
    horizontal=True,
    label_visibility="collapsed",
)
language = "中文" if language_switch == "中" else "English"
st.sidebar.markdown("## UniSydneyBuddy")
st.sidebar.markdown(
    "<div class='semester-value'>Semester 2 · 2026</div>",
    unsafe_allow_html=True,
)
courses = [
    "QBUS6600 · Data Analytics for Business Capstone",
    "MKTG6018 · Customer Analytics and Relationship Management",
    "MKTG6104 · Psychology of Marketing Decisions",
    "SIEN6006 · Entrepreneurship",
]
if "selected_course" not in st.session_state:
    st.session_state.selected_course = courses[0]
for course in courses:
    if st.sidebar.button(
        course,
        key=f"course-{course.split(' · ')[0]}",
        type="primary" if st.session_state.selected_course == course else "secondary",
        width="stretch",
        on_click=select_course,
        args=(course,),
    ):
        pass
selected_course = st.session_state.selected_course
selected_code = selected_course.split(" · ")[0]
selected_course_data = remaining_courses.get(selected_code)

st.markdown(
    f"<div class='course-title'><div class='course-title-text'>{selected_course}</div><span>Semester 2 · 2026</span></div>",
    unsafe_allow_html=True,
)
if CANVAS_SYNC_API_URL:
    sync_id = str(st.query_params.get("sync_id", ""))
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,80}", sync_id):
        sync_id = st.session_state.setdefault("canvas_sync_id", secrets.token_urlsafe(24))
        st.query_params["sync_id"] = sync_id
    canvas_snapshot = load_remote_canvas_snapshot(CANVAS_SYNC_API_URL, sync_id)
    with st.expander(tr(language, "连接 Canvas Connector", "Connect Canvas Connector")):
        st.code(f"{CANVAS_SYNC_API_URL}/canvas-sync?sync_id={sync_id}")
        st.caption(
            tr(
                language,
                "把该地址填入浏览器插件的“UniSydneyBuddy 同步地址”，同步完成后点击“检查最新同步”。请勿公开分享这个私人同步地址。",
                "Paste this into the extension’s UniSydneyBuddy sync address, then use 'Check latest sync'. Do not share this private sync address.",
            )
        )
else:
    sync_id = "local"
    canvas_snapshot = load_canvas_snapshot(CANVAS_SNAPSHOT_PATH)
user_namespace = hashlib.sha256(sync_id.encode("utf-8")).hexdigest()[:20]
if canvas_snapshot:
    new_sync_detected = record_snapshot(APP_DB_PATH, canvas_snapshot)
    sync_change_counts = snapshot_changes(APP_DB_PATH, canvas_snapshot, namespace=user_namespace) if new_sync_detected else {"added": 0, "changed": 0, "removed": 0}
    synced_course_count = len(canvas_snapshot.get("courses", []))
    synced_at = canvas_snapshot.get("synced_at", "—")
    synced_course = next(
        (
            course
            for course in canvas_snapshot.get("courses", [])
            if selected_code.lower() in f"{course.get('course_code', '')} {course.get('name', '')}".lower()
        ),
        None,
    )
    connection_copy = tr(
        language,
        f"Canvas Connector 已连接 · 最近同步 {synced_at} · {synced_course_count} 门课程。" + ("当前课程已匹配，Weekly Brief 将优先读取同步 Module。" if synced_course else "当前所选课程尚未在同步结果中匹配。"),
        f"Canvas Connector connected · last sync {synced_at} · {synced_course_count} courses. " + ("This course is matched; Weekly Brief prioritises synced Modules." if synced_course else "The selected course is not matched in the current snapshot."),
    )
else:
    new_sync_detected = False
    sync_change_counts = {"added": 0, "changed": 0, "removed": 0}
    synced_course = None
    connection_copy = tr(
        language,
        "当前使用预置课程资料。安装 Canvas Connector 后，可从已登录的 canvas.sydney.edu.au 进行真实只读同步。",
        "Preloaded course material is currently in use. Install Canvas Connector to perform a read-only sync from a signed-in canvas.sydney.edu.au session.",
    )
st.markdown(
    f"<div class='demo-status'>{escape(connection_copy)}</div>",
    unsafe_allow_html=True,
)
sync_columns = st.columns([1, 4])
with sync_columns[0]:
    if st.button(tr(language, "检查最新同步", "Check latest sync"), key=f"refresh-sync-{selected_code}"):
        st.cache_data.clear()
        st.rerun()
with sync_columns[1]:
    if new_sync_detected:
        st.success(
            tr(
                language,
                f"检测到新的 Canvas 同步：新增 {sync_change_counts['added']} 项、更新 {sync_change_counts['changed']} 项、移除 {sync_change_counts['removed']} 项。受影响的 Weekly Brief 会要求重新生成。",
                f"New Canvas sync: {sync_change_counts['added']} added, {sync_change_counts['changed']} changed and {sync_change_counts['removed']} removed. Affected Weekly Briefs will require regeneration.",
            )
        )

semester_tab, weekly_tab, project_tab = st.tabs(
    [
        tr(language, "学期总览", "Semester Overview"),
        tr(language, "每周简报", "Weekly Brief"),
        tr(language, "项目计划", "Project Planner"),
    ]
)

with semester_tab:
    st.markdown(f"<div class='compact-title'>Course Overview</div>", unsafe_allow_html=True)
    if selected_code == "QBUS6600":
        summary = schedule["course_summary_zh"] if language == "中文" else schedule["course_summary_en"]
        learning_path = tr(
            language,
            "数据理解与清洗 → EDA 与特征工程 → 统计 / Machine Learning 建模 → 模型评估 → 商业建议",
            "Data understanding → EDA and feature engineering → statistical / ML modelling → model evaluation → business recommendations",
        )
    else:
        summary = selected_course_data["summary_zh"] if language == "中文" else selected_course_data["summary_en"]
        learning_path = selected_course_data["learning_path_zh"] if language == "中文" else selected_course_data["learning_path_en"]
    st.markdown(f"<div class='course-summary'>{summary}</div>", unsafe_allow_html=True)
    st.caption(f"{tr(language, '学习路径', 'Learning path')}：{learning_path}")

    st.markdown(f"<div class='compact-title'>{tr(language, '课程形式', 'Class Structure')}</div>", unsafe_allow_html=True)
    active_sessions = schedule["sessions"] if selected_code == "QBUS6600" else selected_course_data["sessions"]
    session_columns = st.columns(min(3, len(active_sessions)))
    for index, item in enumerate(active_sessions):
        duration = localized_duration(item, language)
        attendance = item["attendance_zh"] if language == "中文" else item["attendance_en"]
        with session_columns[index % len(session_columns)]:
            summary_card(
                item["type"],
                attendance,
                label=tr(language, "课程形式", "Session format"),
                items=[f"{tr(language, '时间', 'Time')}：{duration}"],
            )

    st.markdown("<div class='compact-title'>Assessment Map</div>", unsafe_allow_html=True)
    assessment_rows = []
    if selected_code == "QBUS6600":
        for item in gold["assessments"]:
            assessment_rows.append(
                {
                    tr(language, "Assessment", "Assessment"): localized(item, language),
                    tr(language, "类型", "Category"): category_for(item, language),
                    tr(language, "占比", "Weight"): f"{item['weight_percent']}%",
                    tr(language, "截止日期", "Due date"): format_due(item["due_at"], language),
                    tr(language, "提交内容", "Deliverables"): " · ".join(localized(deliverable, language) for deliverable in item["deliverables"]),
                }
            )
    else:
        for item in selected_course_data["assessments"]:
            due = format_due(item["due_at"], language) if item["due_at"] else item["due_text_zh" if language == "中文" else "due_text_en"]
            assessment_rows.append(
                {
                    tr(language, "Assessment", "Assessment"): item["title_zh"] if language == "中文" else item["title_en"],
                    tr(language, "类型", "Category"): item["category_zh"] if language == "中文" else item["category_en"],
                    tr(language, "占比", "Weight"): f"{item['weight']}%",
                    tr(language, "截止日期", "Due date"): due,
                    tr(language, "提交内容", "Deliverables"): item["deliverables_zh"] if language == "中文" else item["deliverables_en"],
                }
            )
    assessment_columns = st.columns(2)
    assessment_key = tr(language, "Assessment", "Assessment")
    category_key = tr(language, "类型", "Category")
    weight_key = tr(language, "占比", "Weight")
    due_key = tr(language, "截止日期", "Due date")
    deliverables_key = tr(language, "提交内容", "Deliverables")
    for index, item in enumerate(assessment_rows):
        with assessment_columns[index % 2]:
            st.markdown(
                "<div class='summary-card'>"
                f"<div class='summary-card-label'>Assessment {index + 1:02d}</div>"
                f"<div class='summary-card-title'>{escape(item[assessment_key])}</div>"
                "<div class='assessment-meta'>"
                f"<span class='assessment-tag'>{escape(item[category_key])}</span>"
                f"<span class='assessment-tag'>{escape(item[weight_key])}</span>"
                f"<span class='assessment-tag'>{escape(item[due_key])}</span>"
                "</div>"
                f"<div class='summary-card-copy'>{escape(item[deliverables_key])}</div>"
                "</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div class='compact-title'>Learning Overview · Week 1–13</div>", unsafe_allow_html=True)
    active_weeks = schedule["weeks"] if selected_code == "QBUS6600" else selected_course_data["weeks"]
    week_columns = st.columns(2)
    for index, item in enumerate(active_weeks):
        topic = item["title_zh"] if language == "中文" else item["title_en"]
        tutorial = localized_week_session(item, "tutorial", language)
        lecture = localized_week_session(item, "lecture", language)
        with week_columns[index % 2]:
            summary_card(
                topic,
                f"Lecture：{lecture}",
                label=f"Week {item['week']}",
                items=[
                    f"{tr(language, 'Tutorial / Workshop', 'Tutorial / Workshop')}：{tutorial}",
                    f"{tr(language, '学习成果（LO）', 'Learning Outcomes')}：{' · '.join(item['outcomes'])}",
                ],
            )
    if selected_code == "QBUS6600":
        source_note = tr(language, "来源：QBUS6600 Semester 2 2026 Unit Outline。Canvas Module 当前只发布到 Week 2，Week 3–13 的详细课前任务暂不推测。", "Source: QBUS6600 Semester 2 2026 Unit Outline. Canvas Modules are currently published through Week 2; detailed preparation for Weeks 3–13 is not inferred.")
        st.markdown(f"<div class='reference-note'>{source_note}</div>", unsafe_allow_html=True)
        evidence_block(language, gold["course"]["evidence_ids"], evidence_map)
    else:
        source_note = selected_course_data["source_note_zh"] if language == "中文" else selected_course_data["source_note_en"]
        st.markdown(f"<div class='reference-note'>{source_note}</div>", unsafe_allow_html=True)
        with st.expander(tr(language, "课程来源", "Course sources")):
            for source in selected_course_data["sources"]:
                st.markdown(f"- [{source['title']}]({source['url']})")

    st.markdown(f"<div class='compact-title'>{tr(language, '最新通知', 'Latest Announcements')}</div>", unsafe_allow_html=True)
    synced_announcements = (synced_course or {}).get("announcements", [])
    if synced_announcements:
        for announcement in sorted(synced_announcements, key=lambda item: item.get("posted_at") or "", reverse=True)[:5]:
            announcement_copy = plain_canvas_text(announcement.get("message", ""), limit=260)
            st.markdown(
                f"**{escape(announcement.get('title') or tr(language, '未命名通知', 'Untitled announcement'))}**  \n"
                f"{escape(announcement_copy or tr(language, '无正文摘要', 'No text summary'))}  \n"
                f"<span class='reference-note'>{escape(announcement.get('posted_at') or '—')}</span>",
                unsafe_allow_html=True,
            )
    else:
        st.info(
            tr(
                language,
                "当前资料中没有 Announcements。连接 Canvas 后，这里只显示新增或发生变化的课程通知。",
                "No announcements are available in the current material. After Canvas is connected, this area will show only new or changed course announcements.",
            )
        )

with weekly_tab:
    title_col, selector_col = st.columns([3.2, 1])
    with selector_col:
        selected_week_number = st.selectbox(
            tr(language, "周次", "Week"),
            list(range(1, 14)),
            index=1,
            format_func=lambda number: f"Week {number}",
            key="week_selector",
            label_visibility="collapsed",
        )
    active_weeks = schedule["weeks"] if selected_code == "QBUS6600" else selected_course_data["weeks"]
    schedule_week = next(item for item in active_weeks if item["week"] == selected_week_number)
    live_week = canvas_week_extract(synced_course, selected_week_number)
    weekly_title = schedule_week["title_zh"] if language == "中文" else schedule_week["title_en"]
    if live_week and live_week["module_names"]:
        live_title = re.sub(
            rf"^\s*week\s*0?{selected_week_number}\s*[-:–—]\s*",
            "",
            live_week["module_names"][0],
            flags=re.IGNORECASE,
        ).strip()
        scheduled_en = schedule_week["title_en"].strip().casefold()
        if live_title and (language == "English" or live_title.casefold() != scheduled_en):
            localized_live_title = live_title
            if language == "中文" and selected_code != "QBUS6600":
                for assessment in selected_course_data.get("assessments", []):
                    if assessment["title_en"].casefold() in live_title.casefold():
                        localized_live_title = assessment["title_zh"]
                        break
            weekly_title = localized_live_title
    with title_col:
        st.markdown(f"<div class='weekly-title'>Week {selected_week_number} · {weekly_title}</div>", unsafe_allow_html=True)

    if not synced_course:
        st.info(
            tr(
                language,
                "当前课程尚未同步或未在 Canvas Connector 结果中匹配。请先同步该课程后再查看 Weekly Brief。",
                "This course has not been synced or matched in the Canvas Connector result. Sync the course before opening its Weekly Brief.",
            )
        )
    elif not live_week:
        st.info(
            tr(
                language,
                "当前同步结果中没有该周已发布的 Canvas Module，因此暂不生成总结或讲解。",
                "No released Canvas Module for this week exists in the current sync, so no summary or explanation is generated.",
            )
        )
    else:
        module_signature = hashlib.sha256(
            json.dumps(
                {
                    "module_names": live_week["module_names"],
                    "module_items": live_week["module_items"],
                    "content_text": live_week["content_text"],
                    "announcements": live_week["announcements"],
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        module_cache_key = f"weekly-module-summaries-v6-{selected_code}"
        persistent_module_cache_key = f"user:{user_namespace}:{module_cache_key}"
        persisted_module_cache = load_json_state(APP_DB_PATH, persistent_module_cache_key, {})
        module_cache = dict(st.session_state.get(module_cache_key, persisted_module_cache))
        week_cache = dict(module_cache.get(str(selected_week_number), {}))
        source_changed = bool(week_cache and week_cache.get("source_signature") != module_signature)
        if week_cache.get("source_signature") != module_signature:
            week_cache = {"source_signature": module_signature, "result": None}
        module_analysis = week_cache.get("result")
        validation_kwargs = {
            "expected_items": live_week["module_items"],
            "readable_items": live_week["readable_module_items"],
            "announcement_titles": [item["title"] for item in live_week["announcements"]],
        }
        if module_analysis and not validate_module_summary_coverage(module_analysis, **validation_kwargs):
            week_cache["result"] = None
            module_cache[str(selected_week_number)] = week_cache
            st.session_state[module_cache_key] = module_cache
            save_json_state(APP_DB_PATH, persistent_module_cache_key, module_cache)
            module_analysis = None
        api_ready = configure_openai_api_key()

        coverage_items = live_week["module_items"] or live_week["module_names"]
        coverage_label = tr(
            language,
            f"本周已纳入 {len(coverage_items)} 项 Module 内容：",
            f"This week includes {len(coverage_items)} Module items: ",
        )
        st.markdown(
            f"<div class='module-coverage'><strong>{escape(coverage_label)}</strong>"
            f"{escape(' · '.join(coverage_items))}</div>",
            unsafe_allow_html=True,
        )
        unreadable_items = [item for item in live_week["module_items"] if item not in live_week["readable_module_items"]]
        if unreadable_items:
            st.info(
                tr(
                    language,
                    f"资料未同步：{'、'.join(unreadable_items)} 没有可读取正文，AI 不会推测其中内容。",
                    f"Material not synced: {', '.join(unreadable_items)} has no readable body. AI will not infer its content.",
                )
            )
        if source_changed:
            st.warning(
                tr(
                    language,
                    "Canvas 资料已发生变化，旧简报已失效。请重新生成本周简报。",
                    "Canvas material has changed, so the previous brief is outdated. Regenerate this week’s brief.",
                )
            )

        if not live_week["readable_module_items"]:
            st.info(
                tr(
                    language,
                    "本周 Module 目录已同步，但正文未成功读取，因此暂时不能生成知识图谱和内容讲解。",
                    "This week’s Module directory is synced, but no readable body was retrieved, so a Knowledge Map and walkthrough cannot be generated yet.",
                )
            )

        if not module_analysis and api_ready and live_week["readable_module_items"]:
            if st.button(
                tr(language, "生成本周 Module 知识简报", "Generate this week’s Module brief"),
                key=f"summarise-module-{selected_code}-{selected_week_number}",
                type="primary",
            ):
                try:
                    with st.spinner(tr(language, "正在总结本周 Module……", "Summarising this week’s Module…")):
                        generated_analysis = summarise_module(
                            course_title=selected_course,
                            week_number=selected_week_number,
                            module_names=live_week["module_names"],
                            module_items=live_week["module_items"],
                            module_text=live_week["content_text"],
                            announcements=live_week["announcements"],
                            language=language,
                        )
                    if not validate_module_summary_coverage(generated_analysis, **validation_kwargs):
                        raise RuntimeError("Weekly Brief result did not completely cover the synced Module items.")
                    module_analysis = generated_analysis
                    week_cache["result"] = module_analysis
                    module_cache[str(selected_week_number)] = week_cache
                    st.session_state[module_cache_key] = module_cache
                    save_json_state(APP_DB_PATH, persistent_module_cache_key, module_cache)
                except Exception as exc:
                    error_text = str(exc).lower()
                    if "insufficient_quota" in error_text:
                        message = tr(language, "Module 总结失败：当前 API 项目没有可用额度。", "Module summary failed: this API project has no available quota.")
                    elif "invalid_api_key" in error_text or "error code: 401" in error_text:
                        message = tr(language, "Module 总结失败：API Key 无效或已失效。", "Module summary failed: the API key is invalid or inactive.")
                    else:
                        message = tr(language, "Module 总结暂时失败，请稍后重试。", "Module summary temporarily failed. Try again later.")
                    st.error(message)
        elif not module_analysis and not api_ready and live_week["readable_module_items"]:
            st.warning(tr(language, "连接 AI API 后可生成完整 Module 总结与知识点讲解。", "Connect the AI API to generate a complete Module summary and concept explanations."))

        if module_analysis:
            st.markdown(
                f"<div class='compact-title'>{tr(language, '知识图谱', 'Knowledge Map')}</div>",
                unsafe_allow_html=True,
            )
            render_week_knowledge_map(module_analysis, language)

            st.markdown(
                f"<div class='compact-title'>{tr(language, '内容讲解', 'Module Walkthrough')}</div>",
                unsafe_allow_html=True,
            )
            walkthrough_html = []
            for item in module_analysis["walkthrough"]:
                overview = item["overview_zh"] if language == "中文" else item["overview_en"]
                sections_html = "".join(
                    "<div class='walkthrough-subsection'>"
                    f"<div class='walkthrough-subsection-title'>{escape(section['heading_zh'] if language == '中文' else section['heading_en'])}</div>"
                    f"<div class='walkthrough-subsection-copy'>{escape(section['content_zh'] if language == '中文' else section['content_en'])}</div>"
                    "</div>"
                    for section in item["sections"]
                )
                walkthrough_html.append(
                    "<section class='walkthrough-module'>"
                    f"<div class='walkthrough-module-title'>{escape(item['module_label'])}</div>"
                    f"<div class='walkthrough-module-overview'>{escape(overview)}</div>"
                    f"{sections_html}"
                    "</section>"
                )
            st.html(f"<div class='walkthrough-flow'>{''.join(walkthrough_html)}</div>")

            st.markdown(
                f"<div class='compact-title'>{tr(language, '通知与 Workshop 前准备', 'Notices & Workshop Preparation')}</div>",
                unsafe_allow_html=True,
            )
            notices = module_analysis.get("notices_and_preparation", [])
            notice_items = [item for item in notices if item["kind"] == "notice"]
            preparation_items = [item for item in notices if item["kind"] == "workshop_preparation"]

            def action_card(title: str, items: list[dict], empty_text: str) -> str:
                if items:
                    content = "".join(
                        "<div class='weekly-action-item'>"
                        f"<strong>{escape(item['title_zh'] if language == '中文' else item['title_en'])}</strong>"
                        f"<span class='weekly-action-detail'>{escape(item['detail_zh'] if language == '中文' else item['detail_en'])}</span>"
                        "</div>"
                        for item in items
                    )
                else:
                    content = f"<div class='weekly-action-empty'>{escape(empty_text)}</div>"
                return (
                    "<div class='weekly-action-card'>"
                    f"<div class='weekly-action-title'>{escape(title)}</div>{content}"
                    "</div>"
                )

            notice_card = action_card(
                tr(language, "课程通知", "Course Notices"),
                notice_items,
                tr(language, "本周没有课程通知。", "No course notices this week."),
            )
            preparation_card = action_card(
                tr(language, "Workshop 前准备", "Workshop Preparation"),
                preparation_items,
                tr(language, "本周没有 Workshop 前准备。", "No Workshop preparation this week."),
            )
            st.html(f"<div class='weekly-action-grid'>{notice_card}{preparation_card}</div>")

            one_view = module_analysis["one_view"]
            core_sentence = one_view["core_sentence_zh"] if language == "中文" else one_view["core_sentence_en"]
            takeaways_html = "".join(
                f"<li>{escape(item['text_zh'] if language == '中文' else item['text_en'])}</li>"
                for item in one_view["takeaways"]
            )
            chain_html = " → ".join(
                escape(item["title_zh"] if language == "中文" else item["title_en"])
                for item in one_view["logic_chain"]
            )
            st.markdown(
                "<div class='one-view'>"
                f"<div class='one-view-title'>{escape(tr(language, '本周总结', 'In One View'))}</div>"
                f"<div class='one-view-core'>{escape(core_sentence)}</div>"
                f"<ol>{takeaways_html}</ol>"
                f"<div class='one-view-chain'>{chain_html}</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            feedback_form(context=f"weekly-{selected_week_number}", course_code=selected_code, language=language, user_namespace=user_namespace)
        else:
            preview = live_week["source_preview"] or tr(language, "该 Module 只有标题，没有可读取的页面正文。", "This Module contains titles but no readable page text.")
            st.markdown(
                "<div class='week-summary'>"
                f"<div class='week-summary-title'>{tr(language, 'Canvas Module 原文整理', 'Canvas Module source preview')}</div>"
                f"<div class='week-summary-copy'>{escape(preview)}</div>"
                "</div>",
                unsafe_allow_html=True,
            )

        st.caption(
            tr(
                language,
                "分析范围仅限上方列出的已同步 Canvas Module 内容；不包含 Recording、Ed Lesson 或课堂内容。",
                "The analysis is limited to the synced Canvas Module items listed above; Recording, Ed Lesson and class content are excluded.",
            )
        )

with project_tab:
    project_candidates: list[dict] = []
    if selected_code == "QBUS6600":
        for item in gold["assessments"]:
            project_candidates.append(
                {
                    **item,
                    "project_key": item["id"],
                    "category_zh": category_for(item, "中文"),
                    "category_en": category_for(item, "English"),
                }
            )
    else:
        excluded_categories = {"exam", "supervised test", "online quiz", "participation"}
        for item in selected_course_data["assessments"]:
            if item["category_en"].lower() in excluded_categories:
                continue
            project_candidates.append(
                {
                    "project_key": f"{selected_code}-{item['title_en'].lower().replace(' ', '-')}",
                    "title_original": item["title_en"],
                    "title_localized": {"zh-CN": item["title_zh"]},
                    "weight_percent": item["weight"],
                    "due_at": item["due_at"],
                    "team_size": item.get("team_size"),
                    "mode": item["mode"],
                    "category_zh": item["category_zh"],
                    "category_en": item["category_en"],
                    "deliverables": [
                        {
                            "title_original": item["deliverables_en"],
                            "title_localized": {"zh-CN": item["deliverables_zh"]},
                        }
                    ],
                }
            )

    brief_cache_key = f"parsed-briefs-{selected_code}"
    analysis_cache_key = f"ai-analyses-v2-{selected_code}"
    persistent_analysis_cache_key = f"user:{user_namespace}:{analysis_cache_key}"
    active_analysis_key = f"active-assignment-analysis-{selected_code}"
    cached_briefs: list[dict] = list(st.session_state.get(brief_cache_key, []))
    synced_assignments = (synced_course or {}).get("assignments", [])
    canvas_matches = {
        item["project_key"]: match_canvas_assignment(item, synced_assignments)
        for item in project_candidates
    }

    current_analysis_project = st.session_state.get(active_analysis_key)
    if current_analysis_project:
        if st.button(
            tr(language, "← 返回作业列表", "← Back to assignments"),
            key=f"back-to-assignments-{selected_code}",
        ):
            st.session_state.pop(active_analysis_key, None)
            st.rerun()
    else:
        st.markdown(f"<div class='compact-title'>{tr(language, '可规划作业', 'Plannable assignments')}</div>", unsafe_allow_html=True)
        if synced_assignments:
            st.caption(
                tr(
                    language,
                    "Canvas 已同步作业列表。选择一项作业即可进入独立分析页面。",
                    "Canvas assignments are synced. Choose an assignment to open its dedicated analysis view.",
                )
            )
    assignment_columns = st.columns(2) if not current_analysis_project else []
    for index, item in enumerate(project_candidates if not current_analysis_project else []):
        canvas_assignment = canvas_matches[item["project_key"]]
        canvas_material = canvas_assignment_material(canvas_assignment) if canvas_assignment else ""
        canvas_hash = hashlib.sha256(canvas_material.encode("utf-8")).hexdigest() if canvas_material else ""
        existing_canvas_source = next(
            (
                source
                for source in cached_briefs
                if source.get("input_kind") == "canvas" and source.get("project_key") == item["project_key"]
            ),
            None,
        )
        is_current = bool(existing_canvas_source and existing_canvas_source.get("sha256") == canvas_hash)
        is_update = bool(existing_canvas_source and not is_current and canvas_assignment)
        if canvas_assignment:
            source_status = tr(
                language,
                "Canvas 资料已载入" if is_current else "Canvas 内容有更新，可重新载入" if is_update else "已匹配 Canvas 作业说明与 Rubric",
                "Canvas material loaded" if is_current else "Canvas content changed; load the update" if is_update else "Matched to the Canvas brief and rubric",
            )
        else:
            source_status = tr(
                language,
                "当前同步结果中没有匹配的 Canvas 作业说明",
                "No matching Canvas assignment brief was found in the current sync",
            )
        with assignment_columns[index % 2]:
            tags = "".join(
                f"<span class='assessment-tag'>{escape(value)}</span>"
                for value in [
                    item["category_zh"] if language == "中文" else item["category_en"],
                    f"{item['weight_percent']}%",
                    format_due(item["due_at"], language),
                ]
            )
            st.markdown(
                "<div class='canvas-assignment-card'>"
                f"<div class='canvas-assignment-source'>{escape(tr(language, 'Canvas 作业', 'Canvas assignment') if canvas_assignment else tr(language, '课程作业', 'Course assignment'))}</div>"
                f"<div class='canvas-assignment-title'>{escape(localized(item, language))}</div>"
                f"<div class='assessment-meta'>{tags}</div>"
                f"<div class='canvas-assignment-status'>{escape(source_status)}</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            if canvas_assignment:
                button_label = tr(language, "打开作业分析", "Open assignment analysis")
                if st.button(
                    button_label,
                    key=f"load-canvas-assignment-{selected_code}-{item['project_key']}",
                    type="primary",
                    width="stretch",
                ):
                    if not is_current:
                        cached_briefs = [
                            source
                            for source in cached_briefs
                            if not (source.get("input_kind") == "canvas" and source.get("project_key") == item["project_key"])
                        ]
                        cached_briefs.append(
                            {
                                "filename": canvas_assignment.get("name") or localized(item, language),
                                "input_kind": "canvas",
                                "source_type": "canvas_assignment",
                                "chunk_count": 1 + len(canvas_assignment.get("rubric") or []),
                                "sha256": canvas_hash,
                                "text": canvas_material,
                                "project_key": item["project_key"],
                                "source_url": canvas_assignment.get("html_url"),
                            }
                        )
                    st.session_state[brief_cache_key] = cached_briefs
                    st.session_state[active_analysis_key] = item["project_key"]
                    st.rerun()
            else:
                st.button(
                    tr(language, "请先同步该课程", "Sync this course first"),
                    key=f"missing-canvas-assignment-{selected_code}-{item['project_key']}",
                    disabled=True,
                    width="stretch",
                )

    api_ready = configure_openai_api_key()
    cached_briefs = list(st.session_state.get(brief_cache_key, []))
    st.session_state[brief_cache_key] = cached_briefs
    active_project_key = st.session_state.get(active_analysis_key)
    detected_project_keys = [
        active_project_key
    ] if active_project_key and any(item.get("project_key") == active_project_key for item in cached_briefs) else []
    analysis_requested = False
    if detected_project_keys:
        active_item = next(item for item in project_candidates if item["project_key"] == active_project_key)
        st.markdown(
            f"<div class='compact-title'>{tr(language, 'Assignment Analysis', 'Assignment Analysis')} · {escape(localized(active_item, language))}</div>",
            unsafe_allow_html=True,
        )
        source_names = [item["filename"] for item in cached_briefs if item.get("project_key") == active_project_key]
        st.caption(
            tr(language, "分析资料来自 Canvas：", "Analysis material from Canvas: ")
            + " · ".join(source_names)
        )
        existing_analysis_entry = st.session_state.get(analysis_cache_key, {}).get(active_project_key, {})
        existing_language_results = existing_analysis_entry.get("results_by_language", {})
        has_current_analysis = language in existing_language_results
        if has_current_analysis:
            st.success(tr(language, "AI 分析已生成，结果显示在下方。", "AI analysis is ready and displayed below."))
        elif api_ready:
            analysis_requested = st.button(
                tr(language, "AI 分析此作业", "Analyse this assignment with AI"),
                key=f"analyse-canvas-assignment-{selected_code}-{active_project_key}-{language}",
                type="primary",
                width="stretch",
            )
            st.caption(
                tr(
                    language,
                    "点击后，当前 Canvas 作业说明与可见 Rubric 会发送到已配置的 AI 服务并立即生成分析。",
                    "Clicking sends this Canvas assignment description and visible rubric to the configured AI service and generates the analysis immediately.",
                )
            )
        else:
            st.button(
                tr(language, "AI API 未连接", "AI API is not connected"),
                key=f"analyse-canvas-assignment-disabled-{selected_code}-{active_project_key}",
                disabled=True,
                width="stretch",
            )
            st.warning(
                tr(
                    language,
                    "Canvas 作业资料已准备好，但当前 OpenAI API 没有连接或可用额度，因此暂时不能生成 AI 结果。",
                    "The Canvas material is ready, but the OpenAI API is not connected or has no available quota, so an AI result cannot be generated yet.",
                )
            )
    persisted_ai_analyses = load_json_state(APP_DB_PATH, persistent_analysis_cache_key, {})
    ai_analyses: dict[str, dict] = dict(st.session_state.get(analysis_cache_key, persisted_ai_analyses))
    if analysis_requested and api_ready:
        for project_key in detected_project_keys:
            project_assignment = next(item for item in project_candidates if item["project_key"] == project_key)
            project_sources = [
                {"title": item["filename"], "text": item.get("text", "")}
                for item in cached_briefs
                if item["project_key"] == project_key and item.get("text")
            ]
            source_signature = hashlib.sha256("|".join(sorted(item["sha256"] for item in cached_briefs if item["project_key"] == project_key)).encode("utf-8")).hexdigest()
            cached_analysis = ai_analyses.get(project_key, {})
            results_by_language = dict(cached_analysis.get("results_by_language", {}))
            legacy_language = cached_analysis.get("analysis_language")
            if legacy_language and cached_analysis.get("result"):
                results_by_language.setdefault(legacy_language, cached_analysis["result"])
            if (
                cached_analysis.get("source_signature") != source_signature
                or cached_analysis.get("schema_version") != ANALYSIS_SCHEMA_VERSION
            ):
                results_by_language = {}
            if project_sources and (
                language not in results_by_language
            ):
                try:
                    with st.spinner(tr(language, f"正在解析 {localized(project_assignment, language)}……", f"Analysing {localized(project_assignment, language)}…")):
                        results_by_language[language] = analyse_assignment_materials(
                            assignment=project_assignment,
                            materials=project_sources,
                            language=language,
                        )
                        ai_analyses[project_key] = {
                            "source_signature": source_signature,
                            "schema_version": ANALYSIS_SCHEMA_VERSION,
                            "results_by_language": results_by_language,
                        }
                except Exception as exc:
                    error_text = str(exc).lower()
                    if "invalid_api_key" in error_text or "error code: 401" in error_text:
                        message = tr(
                            language,
                            "AI 连接失败：API Key 无效或已失效，请重新配置后再试。",
                            "AI connection failed: the API key is invalid or inactive. Reconfigure it and try again.",
                        )
                    elif "insufficient_quota" in error_text:
                        message = tr(
                            language,
                            "AI 连接失败：当前 API 项目没有可用额度，请检查 Billing。",
                            "AI connection failed: this API project has no available quota. Check Billing.",
                        )
                    else:
                        message = tr(
                            language,
                            f"AI 解析暂时失败，请稍后重试（{type(exc).__name__}）。",
                            f"AI analysis temporarily failed. Try again later ({type(exc).__name__}).",
                        )
                    st.error(message)
        st.session_state[analysis_cache_key] = ai_analyses
        save_json_state(APP_DB_PATH, persistent_analysis_cache_key, ai_analyses)

    if not detected_project_keys:
        st.info(tr(language, "从上方选择一项 Canvas 作业，进入独立的 Assignment Analysis 页面。", "Choose a Canvas assignment above to open its dedicated Assignment Analysis view."))
    else:
        project_assignment = next(item for item in project_candidates if item["project_key"] == active_project_key)
        project_team_range = project_assignment.get("team_size")
        st.markdown(f"<div class='compact-title'>{tr(language, '作业资料', 'Assignment material')}</div>", unsafe_allow_html=True)
        analysis_cols = st.columns(4)
        analysis_cols[0].metric(tr(language, "类型", "Type"), localized(project_assignment, language))
        analysis_cols[1].metric(tr(language, "占比", "Weight"), f"{project_assignment['weight_percent']}%")
        analysis_cols[2].metric(tr(language, "截止日期", "Due date"), format_due(project_assignment["due_at"], language))
        is_group_project = project_assignment["mode"] == "group"
        team_label = (
            f"{project_team_range['min']}–{project_team_range['max']}"
            if project_team_range
            else tr(language, "Brief 待确认", "Confirm from brief")
        ) if is_group_project else tr(language, "个人", "Individual")
        analysis_cols[3].metric(tr(language, "小组人数", "Team size"), team_label)
        st.markdown(f"<div class='analysis-label'>{tr(language, '正式交付物', 'Formal deliverables')}</div>", unsafe_allow_html=True)
        analysis_list([localized(item, language) for item in project_assignment["deliverables"]])
        if selected_code == "QBUS6600":
            evidence_block(language, assignment_2["evidence_ids"], evidence_map)
        else:
            with st.expander(tr(language, "课程来源", "Course sources")):
                for source in selected_course_data["sources"]:
                    st.markdown(f"- [{source['title']}]({source['url']})")
    
        analysis_entry = ai_analyses.get(active_project_key, {})
        results_by_language = dict(analysis_entry.get("results_by_language", {}))
        legacy_language = analysis_entry.get("analysis_language")
        if legacy_language and analysis_entry.get("result"):
            results_by_language.setdefault(legacy_language, analysis_entry["result"])
        project_analysis = results_by_language.get(language)
        if not project_analysis:
            other_language_exists = bool(results_by_language)
            st.info(
                tr(
                    language,
                    "该作业的中文 AI 版本尚未生成；其他语言结果仍已保存。点击上方“AI 分析此作业”即可生成中文版本。" if other_language_exists else "尚未生成 AI 分析。API 可用时，点击上方“AI 分析此作业”即可立即生成结果。",
                    "The English AI version has not been generated; its other-language result remains saved. Click 'Analyse this assignment with AI' above to create the English version." if other_language_exists else "No AI analysis has been generated. When the API is available, click 'Analyse this assignment with AI' above to generate it immediately.",
                )
            )
            st.stop()
        required_analysis_fields = {"objective", "final_deliverables", "key_requirements", "content_framework", "required_documents"}
        if not required_analysis_fields.issubset(project_analysis):
            st.warning(
                tr(
                    language,
                    "AI 解析结构已升级。请点击上方“AI 分析此作业”重新生成；Canvas 原始资料不会删除。",
                    "The AI analysis structure has been upgraded. Click 'Analyse this assignment with AI' above to regenerate it; the Canvas source material will not be deleted.",
                )
            )
            st.stop()

        st.markdown(
            "<div class='analysis-hero'>"
            f"<div class='analysis-kicker'>{tr(language, '作业解析摘要', 'Assignment brief')}</div>"
            f"<div class='analysis-objective'>{escape(project_analysis['objective'])}</div>"
            f"<p class='analysis-summary'>{escape(project_analysis['summary'])}</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        summary_left, summary_right = st.columns([1, 1])
        with summary_left:
            st.markdown(f"<div class='analysis-label'>{tr(language, '最终交付物', 'Final deliverables')}</div>", unsafe_allow_html=True)
            analysis_list(project_analysis["final_deliverables"])
        with summary_right:
            st.markdown(f"<div class='analysis-label'>{tr(language, '关键要求', 'Key requirements')}</div>", unsafe_allow_html=True)
            for requirement in project_analysis["key_requirements"]:
                st.markdown(f"- {escape(requirement['text'])}", unsafe_allow_html=True)

        members: list[str] = []
        if is_group_project:
            team_size_options = list(range(project_team_range["min"], project_team_range["max"] + 1)) if project_team_range else [3, 4]
            team_size_store_key = f"team-size-value-{selected_code}-{active_project_key}"
            saved_team_size = st.session_state.get(team_size_store_key, team_size_options[0])
            team_size = st.selectbox(
                tr(language, "小组人数", "Number of members"),
                team_size_options,
                index=team_size_options.index(saved_team_size) if saved_team_size in team_size_options else 0,
                key=f"team_size-{selected_code}-{active_project_key}",
            )
            st.session_state[team_size_store_key] = team_size
            member_store_key = f"member-values-{selected_code}-{active_project_key}-{team_size}"
            saved_members = dict(st.session_state.get(member_store_key, {}))
            member_columns = st.columns(team_size)
            for index, column in enumerate(member_columns, start=1):
                # Neutral defaults survive language switching; real names are
                # always preserved verbatim.
                default = saved_members.get(str(index), chr(64 + index))
                with column:
                    member_name = st.text_input(tr(language, f"成员 {index}", f"Member {index}"), value=default, key=f"member-{selected_code}-{active_project_key}-{team_size}-{index}").strip()
                    members.append(member_name)
                    saved_members[str(index)] = member_name
            st.session_state[member_store_key] = saved_members

        st.markdown(
            "<div class='analysis-section'><span class='analysis-section-number'>01</span><span class='analysis-section-title'>Assignment Structure</span></div>",
            unsafe_allow_html=True,
        )
        if project_analysis["final_deliverables"]:
            deliverable_copy = "；".join(project_analysis["final_deliverables"])
            st.markdown(
                f"<div class='structure-deliverable'>{escape(deliverable_copy)}</div>",
                unsafe_allow_html=True,
            )
        st.caption(
            tr(
                language,
                "这棵树同时说明最终交付物按照什么结构组织，以及每个部分需要写什么。",
                "This tree shows both how the final deliverable is organised and what should be written in each section.",
            )
        )
        structure_root = localized(project_assignment, language)
        st.markdown(structure_tree_html(structure_root, project_analysis["content_framework"]), unsafe_allow_html=True)

        edited_rows: list[dict] = []
        member_options = ["", *[member for member in members if member]]
        responsibility_store_key = f"responsibility-values-{selected_code}-{active_project_key}"
        saved_responsibilities = dict(st.session_state.get(responsibility_store_key, {}))
        content_framework: list[dict[str, str]] = []
        for section_index, item in enumerate(project_analysis["content_framework"], start=1):
            with st.container(border=True):
                word_tag = ""
                if item.get("word_share"):
                    word_level = item.get("word_share_level")
                    word_label = (
                        tr(language, "规定字数", "Required length")
                        if word_level == "required"
                        else tr(language, "作业建议字数", "Assignment-suggested length")
                        if word_level == "source_recommended"
                        else tr(language, "AI 建议字数", "AI-suggested length")
                    )
                    word_tag = f"<span class='word-share-tag'>{escape(word_label)} · {escape(item['word_share'])}</span>"
                st.markdown(
                    f"<div class='analysis-card-title'>{section_index:02d} · {escape(item['section'])}{word_tag}</div>",
                    unsafe_allow_html=True,
                )
                source_items = list(item["required_content"])
                annotated_content(item["level"], item["purpose"], language, source_items)

                ai_items: list[str] = []
                if item["evidence_suggestions"]:
                    ai_items.append(
                        f"{tr(language, '证据与论证', 'Evidence and reasoning')}："
                        + "；".join(item["evidence_suggestions"])
                    )
                for child in item["subsections"]:
                    child_detail = f"{child['title']}：{child['guidance']}"
                    if child["writing_points"]:
                        child_detail += " — " + "；".join(child["writing_points"])
                    ai_items.append(child_detail)
                if ai_items:
                    ai_level = "ai_suggestion" if item["level"] == "ai_suggestion" else (
                        "ai_plus_recommended" if item["level"] == "source_recommended" else "ai_plus_required"
                    )
                    annotated_content(
                        ai_level,
                        tr(language, "本部分的重点内容", "What to cover in this section"),
                        language,
                        ai_items,
                    )

                owner = tr(language, "本人", "You")
                reviewer = ""
                if is_group_project:
                    saved_section = dict(saved_responsibilities.get(str(section_index), {}))
                    saved_owner = saved_section.get("owner", "")
                    saved_reviewer = saved_section.get("reviewer", "")
                    owner_column, reviewer_column = st.columns([1, 1])
                    with owner_column:
                        owner = st.selectbox(
                            tr(language, "本部分负责人", "Section owner"),
                            member_options,
                            index=member_options.index(saved_owner) if saved_owner in member_options else 0,
                            key=f"section-owner-{selected_code}-{active_project_key}-{section_index}",
                        )
                    with reviewer_column:
                        reviewer = st.selectbox(
                            tr(language, "复核人（可选）", "Reviewer (optional)"),
                            member_options,
                            index=member_options.index(saved_reviewer) if saved_reviewer in member_options else 0,
                            key=f"section-reviewer-{selected_code}-{active_project_key}-{section_index}",
                        )
                    saved_responsibilities[str(section_index)] = {"owner": owner, "reviewer": reviewer}

                framework_summary = "; ".join(item["required_content"])
                content_framework.append(
                    {
                        tr(language, "内容部分", "Section"): item["section"],
                        tr(language, "框架建议", "Framework suggestion"): framework_summary,
                        tr(language, "来源依据", "Source evidence"): item["evidence"],
                    }
                )
                edited_rows.append(
                    {
                        "Part": item["section"],
                        tr(language, "工作内容", "Scope"): framework_summary or item["purpose"],
                        tr(language, "主要产出", "Output"): item["section"],
                        tr(language, "负责人", "Owner"): owner,
                        tr(language, "审核人", "Reviewer"): reviewer,
                    }
                )
        if is_group_project:
            st.session_state[responsibility_store_key] = saved_responsibilities

        st.markdown(
            f"<div class='analysis-section'><span class='analysis-section-number'>02</span><span class='analysis-section-title'>{tr(language, '作业要求或建议使用的文档', 'Documents required or recommended by the assignment')}</span></div>",
            unsafe_allow_html=True,
        )
        project_files: list[dict[str, str]] = []
        if project_analysis["required_documents"]:
            for item in project_analysis["required_documents"]:
                level = "required" if item["requirement"] == "required" else "recommended"
                with st.container(border=True):
                    st.markdown(
                        f"<div class='analysis-card-title'>{escape(item['name'])} &nbsp; {analysis_badge(level, language)}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"<div class='analysis-card-copy'>{escape(item['usage'])}</div>", unsafe_allow_html=True)
                    if item.get("location"):
                        st.markdown(
                            f"<span class='document-location'>{tr(language, '位置', 'Location')} · {escape(item['location'])}</span>",
                            unsafe_allow_html=True,
                        )
                    project_files.append(
                        {
                            tr(language, "文档", "Document"): item["name"],
                            tr(language, "级别", "Level"): tr(language, "必须", "Required") if item["requirement"] == "required" else tr(language, "建议", "Recommended"),
                            tr(language, "用途", "Purpose"): item["usage"],
                            tr(language, "位置", "Location"): item.get("location") or "—",
                        }
                    )
        else:
            st.info(tr(language, "已上传资料中未明确要求或建议使用其他资料。", "The supplied material does not explicitly require or recommend any other material."))
    
        export_rows = [
            {
                tr(language, "任务", "Task"): f"{row['Part']} · {row[tr(language, '工作内容', 'Scope')]}",
                tr(language, "负责人", "Owner"): row.get(tr(language, "负责人", "Owner"), ""),
                tr(language, "审核人", "Reviewer"): row.get(tr(language, "审核人", "Reviewer"), ""),
            }
            for row in edited_rows
        ]
        export_markdown = build_project_markdown(
            project_assignment,
            export_rows,
            language=language,
            content_framework=content_framework,
            project_files=project_files,
        )
        owner_key = tr(language, "负责人", "Owner")
        owners_complete = all(bool(row.get(owner_key)) for row in edited_rows)
        if is_group_project:
            # Confirmation represents the actual assignment, not the current UI
            # language. Keep the signature independent of translated column names.
            canonical_responsibilities = [
                {
                    "section_index": section_index,
                    "owner": row.get(tr(language, "负责人", "Owner"), ""),
                    "reviewer": row.get(tr(language, "审核人", "Reviewer"), ""),
                }
                for section_index, row in enumerate(edited_rows, start=1)
            ]
            responsibility_signature = hashlib.sha256(
                json.dumps(canonical_responsibilities, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()
            confirmation_key = f"responsibilities-confirmed-{selected_code}-{active_project_key}"
            responsibilities_confirmed = (
                owners_complete and st.session_state.get(confirmation_key) == responsibility_signature
            )
            action_left, action_right = st.columns([1, 1])
            with action_left:
                if st.button(tr(language, "确认小组分工", "Confirm responsibilities"), type="primary", width="stretch"):
                    if not owners_complete:
                        st.error(tr(language, "请先为每个作业部分选择负责人。", "Choose an owner for every assignment section first."))
                    else:
                        st.session_state[confirmation_key] = responsibility_signature
                        responsibilities_confirmed = True
                        st.success(tr(language, "小组分工已确认。", "Responsibilities confirmed."))
            with action_right:
                st.download_button(
                    tr(language, "导出完整小组计划", "Export complete group plan"),
                    export_markdown,
                    file_name=f"{selected_code.lower()}-complete-group-plan.md",
                    mime="text/markdown",
                    disabled=not responsibilities_confirmed,
                    help=tr(language, "选择负责人并确认小组分工后即可导出。", "Choose section owners and confirm the responsibilities before exporting."),
                    width="stretch",
                )
        else:
            st.download_button(
                tr(language, "导出个人作业计划", "Export individual assignment plan"),
                export_markdown,
                file_name=f"{selected_code.lower()}-individual-assignment-plan.md",
                mime="text/markdown",
                width="stretch",
            )
        feedback_form(context=f"assignment-{active_project_key}", course_code=selected_code, language=language, user_namespace=user_namespace)
