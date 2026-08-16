# Product Feedback Log

## FB-001 — Student-facing information architecture simplification

- Date: 2026-08-14
- Source: Product owner / University of Sydney student
- Version raised against: Demo v0.1
- Priority: P0
- Status: Completed

### Problems observed

1. Blue visual system does not feel connected to the University of Sydney context.
2. The interface exposes product explanations and engineering concepts that students do not need.
3. Semester Overview metrics do not communicate a clear classification system.
4. Assessment should be classified by actual academic type: exam, individual assignment and group project.
5. Chinese mode leaves too much ordinary learning content in English.
6. Weekly Brief lacks a student-editable to-do list.
7. Project Planner shows an internal processing pipeline instead of focusing on assignment analysis and team coordination.
8. Group work should be divided into selectable work parts after confirming team size; AI should propose work packages rather than assign people.
9. Updates and Eval are not clear student-facing functions and should not occupy primary navigation.

### Decisions

- Adopt USYD ochre/orange `#E64626` with charcoal and warm neutral surfaces.
- Remove promotional hero copy, section introductions and visible local/privacy engineering status.
- Keep course selection as a direct dropdown.
- Group assessments by exam, individual assignment and group project.
- Translate normal learning instructions into Chinese while preserving source-specific terms such as Overview, Reflect and Engage.
- Add an editable Weekly To-do List.
- Replace the Project Planner stepper with upload, parse, team-size confirmation, proposed work parts and member self-selection.
- Remove Updates and Eval from student navigation; retain Eval internally in automated tests.

### Acceptance criteria

- Main navigation contains only Semester Overview, Weekly Brief and Project Planner.
- No technical mode, Eval or agent pipeline status appears in the student interface.
- Group Project planning supports 3–4 members and Part A/B/C/D ownership selection.
- Chinese mode shows Chinese learning goals and required actions.
- All existing privacy and internal evaluation protections remain active in code and tests.

## FB-002 — Course navigation, full schedule and actionable group plan

- Date: 2026-08-14
- Source: Product owner / University of Sydney student
- Version raised against: Demo v0.2
- Priority: P0
- Status: Completed

### Problems observed

1. Course and language controls still look like form inputs rather than navigation.
2. Course Overview contains too much English and inconsistent heading scale.
3. Assessment categories are unnecessarily separated instead of being one comparable list.
4. Learning Overview hides weeks in expanders and only shows released Canvas Modules.
5. Weekly selection is visually disconnected from the selected week's title.
6. The editable To-do List adds space but little value.
7. Project Planner explains AI behaviour but does not provide a sufficiently detailed execution plan or file checklist.

### Decisions

- Use two-level Semester → Course navigation with all four current courses visible.
- Move the compact 中 / EN language switch to the sidebar bottom.
- Use smaller heading levels and remove explanatory UI copy.
- Show all assessments in one table with a Category column.
- Read the official QBUS6600 Unit Outline and display Week 1–13 as one continuous Learning Overview.
- Align the week selector with the Weekly Brief title and remove the To-do List.
- Add a seven-stage suggested group execution plan and a complete project file checklist.
- Keep unpublished Week 3–13 Canvas preparation tasks explicitly unknown.

### Acceptance criteria

- Week 1–13 appear in sequence and are backed by the Unit Outline.
- Assessment appears in one table with category, weight, due date and deliverables.
- Weekly selection sits on the same visual row as the week title.
- Project Planner includes Part selection, detailed stages and required files.
- No unpublished Canvas preparation task is invented.

## FB-003 — Clickable course catalogue and visual hierarchy

- Date: 2026-08-14
- Source: Product owner / University of Sydney student
- Version raised against: Demo v0.3
- Priority: P0
- Status: Completed

### Problems observed

1. Semester and course navigation still look like empty form fields.
2. Chinese due dates use an English date order.
3. Metric values are oversized relative to surrounding content.
4. The selected course and Weekly Brief titles are too small.

### Decisions

- Replace dropdown navigation with a visible, clickable course catalogue; keep the current semester as a fixed navigation label.
- Format Chinese dates as `YYYY年M月D日` while preserving `D Mon YYYY` in English mode.
- Reduce metric value typography and strengthen the page, section and weekly-title hierarchy.

### Acceptance criteria

- All four courses are visible and clickable without opening a dropdown.
- The active course is visually distinguishable from other courses.
- Every known due date uses Chinese year-month-day formatting in Chinese mode.
- Course and weekly titles are more prominent than metric values.

## FB-004 — Lean sidebar and downloadable assignment files

- Date: 2026-08-14
- Source: Product owner / University of Sydney student
- Version raised against: Demo v0.3.1
- Priority: P0
- Status: Completed

### Problems observed

1. `SKILL HUB`, `课程菜单` and `学期` repeat context without helping course selection.
2. The clicked course and highlighted course can temporarily disagree.
3. The group file checklist describes files but does not let students obtain working copies.

### Decisions

- Keep only the product name, current semester value and four course buttons in the sidebar.
- Update course state in button callbacks so selection is applied before the interface renders.
- Replace the static checklist table with nine editable starter files, individual downloads and one ZIP bundle.

### Acceptance criteria

- Redundant sidebar labels are absent.
- Clicking a course immediately updates its active visual state and selected course content.
- Every listed assignment file has a download action, and all templates can be downloaded together.

## FB-005 — Validate the product with all enrolled courses

- Date: 2026-08-14
- Source: Product owner / University of Sydney student
- Version raised against: Demo v0.3.2
- Priority: P0
- Status: Completed

### Decision

- Import MKTG6018, MKTG6104 and SIEN6006 using the same evidence boundary as QBUS6600.
- Prefer the 2026 Unit Outline for stable semester structure and Canvas for currently released weekly preparation.
- Preserve unknown team sizes and unpublished preparation rather than generating plausible values.

### Acceptance criteria

- Every sidebar course opens a real Course Overview, Assessment Map and Week 1–13 Learning Overview.
- Week 1–2 Weekly Briefs use observed Canvas tasks.
- Assessment weights total 100% for every imported course.
- MKTG6104 explicitly records that its public 2026 Unit Outline is unavailable.

## FB-006 — Full function and copy acceptance

- Date: 2026-08-14
- Source: Product owner request for autonomous testing
- Version raised against: Demo v0.4.0
- Priority: P0
- Status: Completed

### Findings and decisions

- Course selection, language switching, the three main tabs and all 13 week values render correctly.
- Uploaded TXT content parses successfully; temporary private files are deleted after parsing.
- All nine individual templates and the ZIP bundle expose distinct downloadable payloads.
- An incomplete responsibility table previously still exposed an export action. Export is now disabled until every Part has an owner, and confirmation explains what is missing.
- Repeated `下载` labels were ambiguous. They now read `下载模板 / Download template` and retain file-specific help text.
- Streamlit's `Deploy` and `Main menu` controls are irrelevant to students and are now hidden.
- Platform-native table tools remain secondary icon controls because search, CSV download and fullscreen are useful on long course tables; core product actions remain bilingual.

### Acceptance result

- Automated suite: 52 passed.
- Real-browser checks: course switching, Chinese/English mode, Week 13 selection, project-tab rendering, incomplete-owner validation and post-fix button visibility all passed.

## FB-007 — Four-course and bilingual feature parity

- Date: 2026-08-14
- Source: Product owner review
- Version raised against: Demo v0.4.1
- Priority: P0
- Status: Completed

### Problems observed

1. QBUS6600 did not show Class Structure while the other three courses did.
2. Only QBUS6600 exposed the full Project Planner; the other courses stopped at a detected-assignment preview.
3. English Group file checklist rows were generated by relabelling Chinese templates and therefore retained Chinese content.

### Decisions

- Show the same Class Structure section for every course. When QBUS timing or attendance is absent, display an explicit unknown state instead of omitting the section or inventing details.
- Use one Project Planner flow for all four courses: upload and parse, assignment analysis, team size, Part selection, detailed plan, downloadable files, confirmation and export.
- Populate the shared flow with the selected course's actual group-assignment title, weight, due date, deliverables and known team-size range.
- Support 3–6 member planning so MKTG6104 can preserve its observed 4–6 person range.
- Maintain independent Chinese and English template content rather than translating field names over Chinese files.

### Acceptance result

- Automated suite: 55 passed, including Chinese and English parity for all four courses.
- Real browser: all seven Project Planner capability checkpoints passed for all four courses.
- English Group file checklist contains no Chinese characters.
- QBUS6600 Class Structure visibly includes Lecture and Tutorial rows with explicit unknown timing and attendance information.

## FB-008 — Separate known assignments from generated project results

- Date: 2026-08-14
- Source: Product owner review
- Version raised against: Demo v0.4.2
- Priority: P0
- Status: Completed

### Problem observed

Project Planner displayed an assignment analysis, team breakdown, plan and files before the student uploaded an Assignment Brief. This made official course metadata look like an AI parsing result and implied work had already been performed.

### Decision

- Start Project Planner with a read-only list of plannable assessments taken from the selected course's Assessment Map.
- Include individual and group assignments; exclude exams, supervised tests, quizzes and participation items.
- Ask the student to select the assignment they intend to analyse, then upload its Brief.
- Before a successful upload, show only the assignment list, selector, uploader and a short explanation of what upload unlocks.
- After successful parsing, reveal analysis, task breakdown, detailed plan, file templates and export actions.
- Use team ownership for group assignments and a personal task breakdown for individual assignments.

### Acceptance result

- Automated suite: 58 passed.
- Before upload: no analysis result, detailed plan or download action is rendered.
- After a real TXT/Markdown parse in automated acceptance: all downstream planning sections render.
- The real browser can open Project Planner and shows the assignment list, selector and uploader without premature results.

## FB-009 — Prevent project state from leaking across courses

- Date: 2026-08-14
- Source: Product owner review
- Version raised against: Demo v0.4.3
- Priority: P0
- Status: Completed

### Problem observed

A Brief uploaded and parsed under QBUS6600 could remain attached to the shared uploader when the student switched to a Marketing or another course, causing the new course to display unrelated analysis.

### Decision

- Give every uploader an identity composed of course code and assignment identity.
- Apply the same identity boundary to member names and editable Part ownership.
- Treat switching courses or assignments as entering an independent Project Planner workspace.

### Acceptance result

- Automated suite: 59 passed.
- After parsing a QBUS6600 Brief, switching to MKTG6018 shows an empty uploader and no analysis, plan or downloads.

## FB-010 — Preserve isolated analysis when returning to a course

- Date: 2026-08-14
- Source: Product owner review
- Version raised against: Demo v0.4.4
- Priority: P0
- Status: Completed

### Problem observed

Course isolation correctly removed a QBUS Brief from other courses, but Streamlit also discarded the uploader widget state when the student left the course. Returning to QBUS therefore lost the visible analysis.

### Decision

- Keep the uploader temporary and store only the parsed result metadata in a separate course-assignment cache.
- Keep the analysis, plan and files in their original completed state when the student returns to the same course and assignment.
- Continue showing the normal `解析完成 / Parsed` file status without a restoration message.
- Add a scoped `删除项目文件 / Delete project file` action that removes the current file and all derived content.

### Acceptance result

- Automated suite: 60 passed.
- QBUS analysis remains absent in MKTG6018 and reappears when returning to QBUS6600.
- Deleting the QBUS project file returns that assignment to the pre-upload state without affecting another course.

## FB-011 — Multi-file upload and automatic Project grouping

- Date: 2026-08-14
- Source: Product owner review
- Version raised against: Demo v0.4.5
- Priority: P0
- Status: Completed

### Decisions

- Allow several PDF, DOCX, PPTX, TXT or Markdown Briefs to be uploaded together.
- Keep file removal inside the upload workspace using a compact per-file `×` action; remove the separate delete-project button.
- Detect the matching assignment from file names and parsed text while keeping detection limited to the current course's plannable assignments.
- Combine multiple files detected as the same assignment into one Project.
- Create separate Project entries when files belong to different assignments, then let the student open each detailed plan independently.
- Preserve multi-file state when leaving and returning to the course, while retaining course isolation.

### Acceptance result

- Automated suite: 63 passed, including the complete multi-file scenario in Chinese and English.
- Two QBUS files identifying Assignment 1 and Assignment 2 create two separate Project entries.
- Removing one file from the upload area clears its derived Project content when no other file belongs to it.
## FB-012 — Replace AI tables with a source-aware assignment guide

- Date: 2026-08-15
- Source: Product owner review
- Version raised against: Demo v0.7.0
- Priority: P0
- Status: Completed

### Problem observed

Long AI-generated task and framework text was rendered in wide tables. The layout clipped content, weakened hierarchy and made source requirements difficult to distinguish from AI advice. Generic group planning could also turn submission chores into artificial member responsibilities.

### Decisions

- Use a designed vertical assignment-guide layout with no tables inside the AI analysis result.
- Keep the analysis summary, task cards, content framework, group ownership and required documents readable in one column.
- Show required, source-recommended and AI-created material with persistent provenance labels and collapsed source evidence.
- Preserve any required or recommended source framework at the top level; AI may only add one labelled subsection level beneath it.
- Restrict group Parts to substantive content and formal deliverables. Exclude upload, formatting, merging, file naming, meeting, reminder, scheduling, progress-tracking and generic QA chores.
- Allow students to select owners and optional reviewers inside each substantive Part card.
- Include only explicitly required or recommended documents and display the stated Canvas/module location when available.

### Acceptance result

- Automated suite: 64 passed.
- Chinese and English seeded AI results render without analysis tables.
- Prompt tests enforce content-only responsibility rules and source-framework preservation.
- Old AI caches are isolated by a new schema-versioned key.

## FB-013 — True task tree and content-level AI attribution

- Date: 2026-08-15
- Source: Product owner review
- Version raised against: Demo v0.8.0
- Priority: P0
- Status: Completed

### Problem observed

The initial Task Breakdown placed flat cards beneath a root and did not read as a genuine tree. The combined `AI + Requirement` badge also failed to show where the assignment requirement ended and AI guidance began. AI guidance needed more analytical depth without becoming generic or inventing new requirements.

### Decisions

- Render Task Breakdown as a three-level `Assignment → content module → content Part` tree.
- Keep detailed scopes, outputs, content focus, risks and group ownership below the overview tree.
- Use the English titles `Task Breakdown` and `Suggested Structure` in both language modes.
- Remove visible source citations from Key Requirements while retaining provenance internally.
- Show assignment requirements and AI expansion as separate content rows rather than a combined provenance badge.
- Require brief-specific AI suggestions to cover analytical questions, theory application, evidence use and critical judgement.
- Continue excluding upload, formatting, meetings and other administrative chores from task allocation.

### Acceptance result

- Automated suite: 64 passed.
- Tree fixtures contain distinct root, module and Part nodes.
- Chinese and English use the same analysis structure and controls.
- UI tests confirm the ambiguous `AI＋要求` label is absent and Key Requirement evidence is not rendered.

## FB-014 — Merge task breakdown into the final-deliverable structure

- Date: 2026-08-15
- Source: Product owner review
- Version raised against: Demo v0.9.0
- Priority: P0
- Status: Completed

### Problem observed

Task Breakdown and Suggested Structure independently decomposed the same assignment. Students could not see which task belonged in which final report or presentation section, and the first breakdown contained more operational detail than needed.

### Decisions

- Use a single `Assignment Structure` as both the writing framework and substantive work breakdown.
- Make every tree node correspond to a real section or segment of the final deliverable.
- For each section, explain only where it belongs and the key content to cover.
- Display the assignment-origin content once and the consolidated AI breakdown once per section.
- Assign group owners and optional reviewers directly to final-deliverable sections.
- Do not create a separate work-module response in the AI schema.

### Acceptance result

- Automated suite: 64 passed.
- UI tests confirm the separate Task Breakdown and Suggested Structure titles are absent.
- The structure tree contains the final deliverable, section and subsection levels.
- Each seeded section renders exactly one assignment-origin annotation and one AI annotation.
