"""Pure helpers used by the final local demo."""

from __future__ import annotations

from datetime import datetime, timedelta
import re
from typing import Any


MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


WEEK_COPY_ZH: dict[str, dict[str, Any]] = {
    "qbus6600-w1": {
        "learning_objectives": ["了解课程结构以及可选择的行业项目。"],
        "must_do": ["在选择项目之前，查看所有可选的行业项目。"],
        "before": ["查看课程介绍和行业项目资料。"],
        "during": ["理解课程要求以及行业项目之间的区别。"],
        "after": ["完成 Engage 部分。"],
    },
    "qbus6600-w2": {
        "learning_objectives": ["理解数据分析工作流，以及统计和 Machine Learning 的基础概念。"],
        "must_do": ["完成 Week 2 的 Explore、Reflect 和 Engage 内容。"],
        "before": ["查看 Week 2 Overview。"],
        "during": ["完成 Explore 和 Reflect 部分。"],
        "after": ["完成 Engage 部分，并整理与 Assignment 1 相关的问题。"],
    },
}


def localized(item: dict[str, Any], language: str) -> str:
    if language == "中文":
        return item.get("title_localized", {}).get("zh-CN", item.get("title_original", ""))
    return item.get("title_original", "")


def format_due(due_at: str | None, language: str) -> str:
    if due_at is None:
        return "待确认" if language == "中文" else "TBA"
    value = datetime.fromisoformat(due_at)
    if language == "中文":
        return f"{value.year}年{value.month}月{value.day}日"
    return value.strftime("%-d %b %Y")


def analyze_date_change(text: str, current_due_at: str) -> dict[str, str] | None:
    pattern = re.compile(
        r"\b(\d{1,2})\s+"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+(20\d{2})\b",
        re.IGNORECASE,
    )
    matches = pattern.findall(text)
    if not matches:
        return None
    day, month_name, year = matches[-1]
    new_date = datetime(int(year), MONTHS[month_name.lower()], int(day))
    current = datetime.fromisoformat(current_due_at)
    if new_date.date() == current.date():
        return None
    return {
        "field": "Assignment 2 due date",
        "before": current.date().isoformat(),
        "after": new_date.date().isoformat(),
        "evidence": text.strip(),
    }


def build_project_markdown(
    assignment: dict[str, Any],
    task_rows: list[dict[str, Any]],
    *,
    language: str,
    detailed_plan: list[dict[str, str]] | None = None,
    content_framework: list[dict[str, str]] | None = None,
    project_files: list[dict[str, str]] | None = None,
) -> str:
    title = localized(assignment, language)
    weight_label = "占比" if language == "中文" else "Weight"
    due_label = "截止日期" if language == "中文" else "Due"
    lines = [f"# {title}", "", f"- {weight_label}: {assignment['weight_percent']}%", f"- {due_label}: {format_due(assignment['due_at'], language)}", ""]
    lines.append("## Assignment Structure" if language == "English" else "## 作业结构")
    for row in task_rows:
        task = row.get("任务") or row.get("Task") or ""
        owner = row.get("负责人") or row.get("Owner") or "—"
        reviewer = row.get("审核人") or row.get("Reviewer") or "—"
        if language == "English":
            lines.append(f"- [ ] {task} · Owner: {owner} · Reviewer: {reviewer}")
        else:
            lines.append(f"- [ ] {task} · 负责人：{owner} · 复核人：{reviewer}")
    if content_framework:
        lines.extend(["", "## Section guidance" if language == "English" else "## 各部分内容说明"])
        for row in content_framework:
            values = list(row.values())
            lines.append(f"- **{values[0]}** — {values[1]} · {values[2]}")
    if detailed_plan:
        lines.extend(["", "## Detailed plan" if language == "English" else "## 详细执行计划"])
        for row in detailed_plan:
            values = list(row.values())
            lines.append(f"- **{values[0]} · {values[1]}** — {values[2]} → {values[3]}")
    if project_files:
        lines.extend(["", "## Required documents and locations" if language == "English" else "## 所需文档与建议位置"])
        for row in project_files:
            values = list(row.values())
            location = values[3] if len(values) > 3 else "—"
            location_label = "Location" if language == "English" else "位置"
            lines.append(f"- [ ] **{values[0]}** — {values[1]} · {values[2]} · {location_label}: {location}")
    return "\n".join(lines) + "\n"


def eval_snapshot(bundle: dict[str, Any], automated_tests: int) -> dict[str, str]:
    group = next(item for item in bundle["assessments"] if item["mode"] == "group")
    required = len(group["deliverables"]) + len(group["intermediate_deliverables"])
    tba_items = [item for item in group["intermediate_deliverables"] if item["due_at"] is None]
    critical_objects = [*bundle["assessments"], *bundle["weeks"]]
    evidence_covered = sum(bool(item["evidence_ids"]) for item in critical_objects)
    return {
        "tests": str(automated_tests),
        "deliverables": f"{required}/{required}",
        "tba_preserved": f"{len(tba_items)}/{len(tba_items)}",
        "evidence_coverage": f"{evidence_covered}/{len(critical_objects)}",
    }


def weekly_copy(week: dict[str, Any], field: str, language: str) -> list[str]:
    if language == "中文":
        return list(WEEK_COPY_ZH.get(week["id"], {}).get(field, []))
    if field in {"before", "during", "after"}:
        return list(week["sessions"][0][field])
    return list(week[field])


def propose_work_parts(team_size: int, language: str) -> list[dict[str, str]]:
    if team_size not in {3, 4, 5, 6}:
        raise ValueError("team_size must be between 3 and 6")
    if language == "中文":
        parts = [
            {"part": "Part A", "scope": "研究问题、案例范围与核心分析角度", "output": "研究问题与分析范围"},
            {"part": "Part B", "scope": "资料、证据或数据整理与核心分析", "output": "证据记录与分析结果"},
            {"part": "Part C", "scope": "核心发现、论证与解释", "output": "主要发现与论证内容"},
            {"part": "Part D", "scope": "建议、方案或实践含义", "output": "建议或方案内容"},
            {"part": "Part E", "scope": "批判性评价、局限与替代解释", "output": "批判性评价内容"},
            {"part": "Part F", "scope": "结论、反思与整体意义", "output": "结论与反思内容"},
        ]
    else:
        parts = [
            {"part": "Part A", "scope": "Research question, case scope and core analytical angles", "output": "Research question and analytical scope"},
            {"part": "Part B", "scope": "Source, evidence or data preparation and core analysis", "output": "Evidence log and analysis"},
            {"part": "Part C", "scope": "Core findings, argument and interpretation", "output": "Findings and argument content"},
            {"part": "Part D", "scope": "Recommendations, solution or practical implications", "output": "Recommendation or solution content"},
            {"part": "Part E", "scope": "Critical evaluation, limitations and alternative explanations", "output": "Critical evaluation content"},
            {"part": "Part F", "scope": "Conclusion, reflection and overall significance", "output": "Conclusion and reflection content"},
        ]
    return parts[:team_size]


def build_detailed_project_plan(language: str, due_at: str | None = None) -> list[dict[str, str]]:
    offsets = [56, 42, 28, 21, 14, 7, 2]
    if due_at:
        due = datetime.fromisoformat(due_at)
        timings = [format_due((due - timedelta(days=days)).isoformat(), language) for days in offsets]
    else:
        timings = [f"截止前 {days} 天" if language == "中文" else f"{days} days before due" for days in offsets]
    if language == "中文":
        return [
            {"阶段": "1. 要求与范围确认", "建议时间": timings[0], "详细任务": "核对 Brief、Rubric、截止日期、提交格式和所有交付物；小组作业同时确认成员与协作方式。", "阶段产出": "要求清单、范围与责任框架"},
            {"阶段": "2. 资料与证据准备", "建议时间": timings[1], "详细任务": "收集课程材料、研究来源、数据或案例，记录来源与使用限制，并列出待确认问题。", "阶段产出": "资料清单、证据记录、待确认问题"},
            {"阶段": "3. 分析与方案设计", "建议时间": timings[2], "详细任务": "选择适合作业要求的分析、论证或设计方法，明确质量标准和各部分之间的依赖。", "阶段产出": "分析框架、方法与任务依赖"},
            {"阶段": "4. 核心内容初稿", "建议时间": timings[3], "详细任务": "完成主要交付内容、图表或展示材料初稿，并逐项对应 Rubric。", "阶段产出": "完整初稿与 Rubric 对照"},
            {"阶段": "5. 审核与修改", "建议时间": timings[4], "详细任务": "检查论据、结构、引用与限制；小组作业进行跨 Part review 并记录修改项。", "阶段产出": "Review 记录与修改稿"},
            {"阶段": "6. 整合与演练", "建议时间": timings[5], "详细任务": "统一格式、术语和叙事；如有展示或视频，完成脚本、演练和技术检查。", "阶段产出": "整合版本、展示材料与演练记录"},
            {"阶段": "7. 最终 QA 与提交", "建议时间": timings[6], "详细任务": "逐项核对 Rubric、文件命名、引用、可打开性和上传要求；保留提交确认。", "阶段产出": "最终交付物、Peer review、提交确认"},
        ]
    return [
        {"Stage": "1. Requirements and scope", "Suggested timing": timings[0], "Detailed tasks": "Check the brief, rubric, due date, submission format and every deliverable; for group work, confirm members and collaboration rules.", "Output": "Requirements, scope and responsibilities"},
        {"Stage": "2. Sources and evidence", "Suggested timing": timings[1], "Detailed tasks": "Collect course material, research, data or cases; record sources, usage limits and open questions.", "Output": "Source list, evidence log and open questions"},
        {"Stage": "3. Analysis and approach", "Suggested timing": timings[2], "Detailed tasks": "Choose an analysis, argument or design approach suited to the brief and define dependencies and quality criteria.", "Output": "Analysis framework, method and dependencies"},
        {"Stage": "4. Core draft", "Suggested timing": timings[3], "Detailed tasks": "Draft the main deliverables, figures or presentation material and map each section to the rubric.", "Output": "Complete draft and rubric map"},
        {"Stage": "5. Review and revision", "Suggested timing": timings[4], "Detailed tasks": "Check evidence, structure, references and limitations; for group work, cross-review Parts and record revisions.", "Output": "Review log and revised draft"},
        {"Stage": "6. Integration and rehearsal", "Suggested timing": timings[5], "Detailed tasks": "Standardise format, terminology and narrative; rehearse and technically check any presentation or video.", "Output": "Integrated version, presentation and rehearsal record"},
        {"Stage": "7. Final QA and submission", "Suggested timing": timings[6], "Detailed tasks": "Check the rubric, file names, references, file access and upload requirements; retain submission confirmation.", "Output": "Final deliverables, Peer review and submission record"},
    ]


def build_content_framework(language: str) -> list[dict[str, str]]:
    """Return a course-agnostic assignment structure that can be refined from a brief."""
    if language == "中文":
        return [
            {"内容部分": "1. 要求与 Rubric 对照", "框架建议": "列出作业目标、提交项、字数或时长、评分标准与限制条件。", "检查点": "每个 Rubric 项都有对应内容"},
            {"内容部分": "2. 背景与问题", "框架建议": "界定研究、商业或反思问题，说明范围与重要性。", "检查点": "问题明确且与课程目标相关"},
            {"内容部分": "3. 证据与方法", "框架建议": "说明课程材料、数据、文献或案例及分析方法。", "检查点": "来源可追溯，方法能回答问题"},
            {"内容部分": "4. 核心分析或论证", "框架建议": "按主题或子问题组织发现，将证据、解释与判断连接起来。", "检查点": "结论由证据支持"},
            {"内容部分": "5. 结论与建议", "框架建议": "回答核心问题，提出建议、启示或 Reflection。", "检查点": "不引入未论证的新结论"},
            {"内容部分": "6. 限制、引用与附件", "框架建议": "说明限制、伦理或 AI 使用，整理引用、附录与辅助材料。", "检查点": "格式与学术诚信要求合规"},
        ]
    return [
        {"Section": "1. Requirements and rubric map", "Framework suggestion": "List the objective, deliverables, length or duration, criteria and constraints.", "Check": "Every rubric criterion maps to content"},
        {"Section": "2. Context and question", "Framework suggestion": "Define the research, business or reflection question, scope and significance.", "Check": "The question is clear and relevant to the unit outcomes"},
        {"Section": "3. Evidence and method", "Framework suggestion": "Explain the course material, data, literature or cases and the analysis method.", "Check": "Sources are traceable and the method answers the question"},
        {"Section": "4. Core analysis or argument", "Framework suggestion": "Organise findings by theme or sub-question and connect evidence, interpretation and judgement.", "Check": "Claims are supported by evidence"},
        {"Section": "5. Conclusions and recommendations", "Framework suggestion": "Answer the main question and provide recommendations, implications or reflection.", "Check": "No unsupported new claims are introduced"},
        {"Section": "6. Limitations, references and appendices", "Framework suggestion": "Cover limitations, ethics or AI use, then organise references and supporting material.", "Check": "Format and academic-integrity requirements are met"},
    ]


def required_project_files(language: str, mode: str = "group") -> list[dict[str, str]]:
    if language == "中文":
        rows = [
            {"文档": "Assignment Brief 与 Rubric", "用途": "保留作业要求与评分标准", "建议位置": "01_Admin/Assignment_Brief_Rubric"},
            {"文档": "Task / team plan", "用途": "记录任务、Owner、Reviewer 与时间", "建议位置": "01_Admin/Task_or_Team_Plan"},
            {"文档": "Research / evidence log", "用途": "记录资料、证据、数据与使用限制", "建议位置": "02_Research/Evidence_Log"},
            {"文档": "Source register", "用途": "统一引用来源与参考文献", "建议位置": "02_Research/Source_Register"},
            {"文档": "Analysis working notes", "用途": "保存分析、判断、图表或草稿", "建议位置": "03_Working/Analysis_Notes"},
            {"文档": "Main submission", "用途": "组织最终交付内容并对应 Rubric", "建议位置": "04_Deliverables/Main_Submission"},
            {"文档": "Presentation / supporting material", "用途": "存放 Brief 要求的展示、视频或附件", "建议位置": "04_Deliverables/Supporting_Material"},
            {"文档": "Review log", "用途": "记录修改、反馈与成员贡献", "建议位置": "05_Review/Review_Log"},
            {"文档": "Submission checklist", "用途": "核对版本、文件名与提交结果", "建议位置": "05_Review/Submission_Checklist"},
        ]
    else:
        rows = [
            {"Document": "Assignment Brief and rubric", "Purpose": "Retain the requirements and marking criteria", "Suggested location": "01_Admin/Assignment_Brief_Rubric"},
            {"Document": "Task / team plan", "Purpose": "Record tasks, Owners, Reviewers and timing", "Suggested location": "01_Admin/Task_or_Team_Plan"},
            {"Document": "Research / evidence log", "Purpose": "Record sources, evidence, data and usage limits", "Suggested location": "02_Research/Evidence_Log"},
            {"Document": "Source register", "Purpose": "Align citations and references", "Suggested location": "02_Research/Source_Register"},
            {"Document": "Analysis working notes", "Purpose": "Keep analysis, decisions, figures or draft material", "Suggested location": "03_Working/Analysis_Notes"},
            {"Document": "Main submission", "Purpose": "Organise the final deliverable and map it to the rubric", "Suggested location": "04_Deliverables/Main_Submission"},
            {"Document": "Presentation / supporting material", "Purpose": "Store presentation, video or attachments required by the brief", "Suggested location": "04_Deliverables/Supporting_Material"},
            {"Document": "Review log", "Purpose": "Record revisions, feedback and contribution", "Suggested location": "05_Review/Review_Log"},
            {"Document": "Submission checklist", "Purpose": "Check versions, file names and submission confirmation", "Suggested location": "05_Review/Submission_Checklist"},
        ]
    if mode == "individual":
        return [row for row in rows if "team plan" not in next(iter(row.values())).lower() and "Review log" not in next(iter(row.values())) and "Review log" not in str(row)]
    return rows


def build_project_templates(language: str, course_code: str = "QBUS6600", due_at: str | None = "2026-10-19T23:59:00+11:00") -> list[dict[str, str]]:
    """Return editable starter files that are safe to download from the demo."""
    if language == "中文":
        return [
            {
                "文件": "作业要求与 Rubric 核对表",
                "用途": "逐项确认要求、评分标准和提交格式",
                "文件名": "01_作业要求与Rubric核对表.md",
                "内容": f"# {course_code} 作业要求与 Rubric 核对表\n\n- [ ] 截止日期：{format_due(due_at, language)}\n- [ ] 所有提交项已确认\n- [ ] 页数、引用格式与文件命名已核对\n- [ ] 每项 Rubric 均有对应内容\n",
            },
            {
                "文件": "Team responsibilities outline",
                "用途": "记录每个 Part 的 Owner、Reviewer 和交付时间",
                "文件名": "02_team_responsibilities.md",
                "内容": "# Team Responsibilities\n\n| Part | Scope | Owner | Reviewer | Due | Status |\n|---|---|---|---|---|---|\n| Part A | | | | | 未开始 |\n| Part B | | | | | 未开始 |\n| Part C | | | | | 未开始 |\n",
            },
            {
                "文件": "Research / evidence log",
                "用途": "记录资料、证据、数据来源和待确认问题",
                "文件名": "03_research_evidence_log.csv",
                "内容": "owner,source_or_item,key_finding,evidence,usage_limit,open_question\n成员A,,,,,\n成员B,,,,,\n成员C,,,,,\n",
            },
            {
                "文件": "Source register",
                "用途": "统一来源、引用方式、可信度和使用限制",
                "文件名": "04_source_register.csv",
                "内容": "source,description,reference_format,confidence,allowed_use,notes\n,,,,,\n",
            },
            {
                "文件": "Analysis working notes",
                "用途": "记录分析问题、方法、发现、限制和后续行动",
                "文件名": "05_analysis_working_notes.md",
                "内容": f"# {course_code} Analysis Working Notes\n\n## Question\n\n## Sources / Data\n\n## Method\n\n## Findings\n\n## Limitations\n\n## Next Actions\n",
            },
            {
                "文件": "Main submission 模板",
                "用途": "组织主要交付内容并逐项对应 Rubric",
                "文件名": "06_main_submission_template.md",
                "内容": "# Main Submission\n\n## Purpose\n\n## Evidence and Approach\n\n## Main Analysis / Argument\n\n## Conclusions / Recommendations\n\n## Risks and Limitations\n\n## Rubric Mapping\n\n## References\n",
            },
            {
                "文件": "Presentation / supporting material",
                "用途": "在 Brief 要求时规划展示、海报、视频或附件",
                "文件名": "07_presentation_script.md",
                "内容": "# Presentation / Supporting Material\n\n| Section | Owner | Duration / Size | Key message | Visual / File |\n|---|---|---:|---|---|\n| Opening | | | | |\n| Evidence and approach | | | | |\n| Findings | | | | |\n| Conclusions | | | | |\n| Closing | | | | |\n",
            },
            {
                "文件": "Progress report / Peer review",
                "用途": "记录进度、成员贡献、阻塞项和互评",
                "文件名": "08_progress_peer_review.md",
                "内容": "# Progress & Peer Review\n\n| Member | Completed work | Evidence | Next task | Blocker | Peer feedback |\n|---|---|---|---|---|---|\n| | | | | | |\n",
            },
            {
                "文件": "Submission checklist",
                "用途": "核对文件名、版本、可运行性和最终提交",
                "文件名": "09_submission_checklist.md",
                "内容": "# Submission Checklist\n\n- [ ] 所有 Brief 要求的交付物均为最终版本\n- [ ] 文件均可正常打开或运行\n- [ ] 图表、证据与正文结论一致\n- [ ] 引用和文件命名符合要求\n- [ ] 如适用，Peer review 已完成\n- [ ] 已复核最终上传结果\n",
            },
        ]

    return [
        {"File": "Assignment Brief and rubric checklist", "Purpose": "Check requirements, criteria and submission format", "Filename": "01_assignment_brief_rubric_checklist.md", "Content": f"# {course_code} Assignment Brief and Rubric Checklist\n\n- [ ] Due date: {format_due(due_at, language)}\n- [ ] All deliverables confirmed\n- [ ] Length, references and file names checked\n- [ ] Every rubric criterion has corresponding content\n"},
        {"File": "Team responsibilities outline", "Purpose": "Record each Part's Owner, Reviewer and due date", "Filename": "02_team_responsibilities.md", "Content": "# Team Responsibilities\n\n| Part | Scope | Owner | Reviewer | Due | Status |\n|---|---|---|---|---|---|\n| Part A | | | | | Not started |\n| Part B | | | | | Not started |\n| Part C | | | | | Not started |\n"},
        {"File": "Research / evidence log", "Purpose": "Record sources, evidence, data, usage limits and open questions", "Filename": "03_research_evidence_log.csv", "Content": "owner,source_or_item,key_finding,evidence,usage_limit,open_question\nMember A,,,,,\nMember B,,,,,\nMember C,,,,,\n"},
        {"File": "Source register", "Purpose": "Align sources, references, confidence and permitted use", "Filename": "04_source_register.csv", "Content": "source,description,reference_format,confidence,allowed_use,notes\n,,,,,\n"},
        {"File": "Analysis working notes", "Purpose": "Record the question, approach, findings, limitations and next actions", "Filename": "05_analysis_working_notes.md", "Content": f"# {course_code} Analysis Working Notes\n\n## Question\n\n## Sources / Data\n\n## Method\n\n## Findings\n\n## Limitations\n\n## Next Actions\n"},
        {"File": "Main submission template", "Purpose": "Organise the main deliverable and map it to the rubric", "Filename": "06_main_submission_template.md", "Content": "# Main Submission\n\n## Purpose\n\n## Evidence and Approach\n\n## Main Analysis / Argument\n\n## Conclusions / Recommendations\n\n## Risks and Limitations\n\n## Rubric Mapping\n\n## References\n"},
        {"File": "Presentation / supporting material", "Purpose": "Plan slides, poster, video or attachments when required by the brief", "Filename": "07_presentation_script.md", "Content": "# Presentation / Supporting Material\n\n| Section | Owner | Duration / Size | Key message | Visual / File |\n|---|---|---:|---|---|\n| Opening | | | | |\n| Evidence and approach | | | | |\n| Findings | | | | |\n| Conclusions | | | | |\n| Closing | | | | |\n"},
        {"File": "Progress report and peer review", "Purpose": "Record progress, contribution, blockers and peer feedback", "Filename": "08_progress_peer_review.md", "Content": "# Progress and Peer Review\n\n| Member | Completed work | Evidence | Next task | Blocker | Peer feedback |\n|---|---|---|---|---|---|\n| | | | | | |\n"},
        {"File": "Submission checklist", "Purpose": "Check versions, file names, quality and final submission", "Filename": "09_submission_checklist.md", "Content": "# Submission Checklist\n\n- [ ] All required files are final\n- [ ] Figures and claims are consistent\n- [ ] References and file names meet the brief\n- [ ] Peer review is complete\n- [ ] A second member verified the uploaded submission\n"},
    ]
