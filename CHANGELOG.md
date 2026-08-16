# Changelog

## v0.12.0 — Real local Canvas Connector

- Added a read-only Chrome Manifest V3 Connector scoped to `canvas.sydney.edu.au`.
- Used the existing signed-in Canvas browser session without asking for a password or personal API token.
- Synced selected Courses, syllabus content, Modules, Canvas Pages, Assignments, visible Rubrics and Announcements to a localhost-only bridge.
- Added snapshot validation, a 12 MB request limit, extension-origin checks and Git-ignored local storage.
- Made matched Weekly Briefs prioritise real synced Module Items and made Semester Announcements use synced Canvas content.
- Replaced Weekly Brief content cards with a continuous text brief separated by lightweight rules.
- Kept Canvas read access and optional OpenAI sending as separate consent decisions.

## v0.11.0 — Semester and weekly workspace redesign

- Replaced Semester Overview and Weekly Brief data tables with the same card-based visual language used by the Project Planner.
- Added a weekly course summary and separate Module, Lecture / Recording, and Tutorial / Workshop source cards.
- Kept Recording summaries empty unless transcript content is actually imported, and separated after-class consolidation from Module content.
- Added a global local-Demo status and an Announcements empty state without implying a live Canvas connection.
- Preserved AI analysis, member names and section ownership when switching interface language.
- Required explicit responsibility confirmation before group-plan export and preserved document locations in Markdown exports.
- Moved uploaded files to system-temporary storage and localized student-facing upload errors.
- Corrected privacy documentation to distinguish temporary files, in-session extracted text, Canvas read access and optional AI sending consent.
- Passed 67 automated tests in Chinese and English.

## v0.10.0 — Unified assignment structure

- Merged `Task Breakdown` and `Suggested Structure` into one `Assignment Structure`.
- Made the tree mirror the actual final deliverable: deliverable → required sections → AI-supported subsections.
- Moved the full deliverable/word-count sentence beneath the section title so the tree contains structure nodes only.
- Reduced every section detail to the two student decisions that matter: where the content belongs and what to cover there.
- Consolidated all source content in a section under one assignment-origin label and all AI expansion under one AI label.
- Moved group ownership from artificial task Parts to the actual assignment sections.
- Displayed each section's word allocation as a compact required/source/AI-labelled tag instead of body text.
- Removed source-evidence expanders from the required/recommended document list.
- Removed the separate AI work-module output from the analysis schema, reducing duplication and API output size.
- Passed 64 automated Chinese/English tests.

## v0.9.0 — Tree breakdown and deeper AI guidance

- Replaced the flat Part overview with a true three-level `Assignment → Module → Part` tree.
- Kept group ownership controls attached only to substantive content Parts.
- Renamed the two analysis sections to `Task Breakdown` and `Suggested Structure` in both language modes.
- Removed visible evidence/source expanders from Key Requirements.
- Replaced ambiguous `AI + Requirement` presentation with content-level `作业要求 / 作业建议 / AI 拆解建议 / AI 建议` annotations.
- Deepened AI guidance with assignment-specific analytical questions, theory use, evidence plans and critical-judgement prompts while preventing generic filler.
- Upgraded cached analysis to schema version 3 and guarded older results from rendering errors.
- Passed 64 automated tests in Chinese and English.

## v0.8.0 — Assignment guide analysis

- Replaced every AI-result table with a designed vertical assignment-guide layout.
- Added one-screen objective, deliverables and key-requirement summary with explicit source labels.
- Rendered task breakdowns as readable cards with outputs, requirements, risks and collapsed evidence.
- Restricted group Parts to substantive assignment content and formal deliverables; administrative chores can no longer be generated as responsibilities.
- Preserved required or recommended source frameworks and limited AI expansion to one labelled subsection level.
- Added five provenance labels: required, source recommendation, AI + requirement, AI + recommendation and AI suggestion.
- Replaced group ownership tables with per-Part member selection inside the relevant content card.
- Rendered required documents as cards with stated Canvas locations and source evidence.
- Versioned the AI cache so older table-shaped results cannot leak into the new interface.
- Passed 64 automated tests in Chinese and English.

## v0.7.0 — AI-gated unified analysis

- Combined pasted Canvas text and multi-file upload into one form with one bottom `Analyse all material` action.
- Kept each text or file source independent so one submission can create multiple Assignment Projects.
- Added an OpenAI Responses API adapter using Pydantic Structured Outputs.
- Added explicit user consent before any private assignment material is sent to the model service.
- Removed the dated execution plan.
- Limited the document section to items explicitly required or recommended in the supplied assignment material, with source evidence.
- When no API key is configured, the UI performs local reading and grouping only and does not fabricate AI output.
- Passed 64 automated tests.

## v0.6.0 — Unified assignment material input

- Replaced the document-only Project Planner input with Canvas text paste plus multi-document and screenshot upload.
- Added local macOS OCR for PNG, JPG and JPEG screenshots.
- Preserved course-scoped state and automatic Assignment grouping for both pasted and uploaded sources.
- Structured parsed results into responsibility / task planning, content-framework suggestions and required documents with suggested locations.
- Removed individual template and ZIP downloads while retaining complete-plan export.
- Expanded automated coverage to 67 tests in Chinese and English.

## v0.5.0 — Release acceptance and documentation

- Completed 64 automated tests plus Gold data, compilation, dependency and real-browser checks.
- Added complete product specification and test / product-reasonableness report.
- Replaced fixed Week milestones with dates calculated backwards from each assignment due date.
- Reworked project parts and templates into cross-disciplinary structures suitable for all four courses.
- Added manual assignment confirmation when an uploaded file cannot be matched reliably.
- Corrected UI copy so deterministic planning is not presented as live LLM generation.

## v0.4.7 — Mock Brief grouping test

- Added four short QBUS mock documents covering Assignment 1, two Assignment 2 files and Assignment 3.
- Verified that four files create three Projects and that the two Assignment 2 documents merge correctly.
- Verified that opening the detected Assignment 2 Project exposes group-responsibility planning.
- Repeated the complete multi-file grouping and Project-control scenario in English mode.

## v0.4.6 — Multi-file Project workspace

- Enabled multiple Assignment Brief uploads in one course workspace.
- Replaced the separate delete-project action with per-file removal inside the upload area.
- Added assignment detection from file names and parsed document text.
- Grouped files that belong to the same assignment and created separate Projects for different assignments.
- Added a Created Projects overview and a selector for opening each detected Project's detailed plan.

## v0.4.5 — Persistent isolated Brief state

- Persisted parsed Brief metadata independently from Streamlit's temporary uploader widget.
- Preserved the original parsed state when returning to the same course and assignment.
- Kept saved results isolated from every other course and assignment.
- Added a scoped Delete project file action that removes the file and all derived content.

## v0.4.4 — Course-scoped project state

- Scoped uploaded Briefs to the selected course and assignment.
- Scoped member names and Part ownership tables to the same course-assignment pair.
- Prevented QBUS6600 parsing results and planning state from appearing in Marketing or other courses.

## v0.4.3 — Upload-gated Project Planner

- Separated known Assessment Map facts from AI-generated brief analysis.
- Added a course-specific list of plannable individual and group assignments while excluding exams, tests, quizzes and participation.
- Added an explicit assignment selector before Brief upload.
- Hidden analysis, task breakdown, detailed plan, templates and export until a Brief parses successfully.
- Added distinct individual-assignment and group-assignment planning paths.
- Renamed the shared files area to `作业文件清单 / Assignment file checklist`.

## v0.4.2 — Four-course feature parity

- Added QBUS6600 Class Structure with explicit unknown timing and attendance states.
- Unified Project Planner capabilities across QBUS6600, MKTG6018, MKTG6104 and SIEN6006.
- Made assignment analysis, team-size choices, Part ownership, detailed plan, templates and export course-aware.
- Added support for known 4–6 person teams while preserving `Brief 待确认` for unknown team sizes.
- Rebuilt English assignment templates without Chinese labels, content or file names.
- Added Chinese/English parity tests for every course.

## v0.4.1 — Full UI acceptance

- Added automated acceptance coverage for four courses across all 13 weeks, both languages, uploads, downloads and guarded project actions.
- Prevented incomplete responsibility plans from being exported.
- Added file-specific download help and clearer `下载模板 / Download template` actions.
- Removed Streamlit deployment and main-menu controls from the student interface.
- Deleted temporary private upload files immediately after parsing.

## v0.4.0 — Four-course content test

- Added MKTG6018, MKTG6104 and SIEN6006 from official Unit Outlines and authenticated Canvas content.
- Added course-specific summaries, class structures, complete Assessment Maps and Week 1–13 schedules.
- Added evidence-backed Week 1–2 preparation for each new course without inventing unpublished tasks.
- Added a guarded group-project preview for courses whose full Assignment Brief has not been imported.
- Added data-completeness, assessment-weight, unknown-preservation and multi-course rendering tests.

## v0.3.2 — Downloadable assignment workspace

- Removed redundant `SKILL HUB`, course-menu and semester labels from the sidebar.
- Fixed course-button selection timing with callback-based state updates.
- Replaced the static file checklist with nine downloadable assignment templates.
- Added a one-click ZIP download containing the complete template set.

## v0.3.1 — Navigation and typography refinement

- Replaced Semester/Course dropdowns with a fixed semester label and clickable course catalogue.
- Changed Chinese due dates to year-month-day formatting.
- Enlarged course and Weekly Brief titles while reducing oversized metric values.
- Added a clear active-course state in the sidebar.

## v0.3.0 — Course-first layout and detailed planning

- Added two-level Semester and Course navigation plus a bottom language switch.
- Reduced heading size and removed unnecessary explanatory text.
- Combined assessments into one category-aware table.
- Added the official QBUS6600 Week 1–13 Learning Overview from the Unit Outline.
- Moved week selection into the Weekly Brief title row and removed the To-do List.
- Added a seven-stage group execution plan and required-file checklist.
- Extended exported plans to include responsibilities, milestones and files.

## v0.2.0 — Student workflow redesign

- Switched the interface to the University of Sydney ochre/orange visual direction.
- Simplified the top area to the selected course title.
- Removed student-facing development, privacy mode, update and Eval UI.
- Reorganised Assessment Map into exam, individual assignment and group project categories.
- Added Chinese Weekly Brief content and an editable student to-do list.
- Redesigned Group Project planning around team size, proposed work parts and member self-selection.
- Kept Evidence, privacy blocking and automated Eval as internal quality controls.

## v0.1.0 — Final workflow prototype

- Added Semester Brief, Weekly Brief, Project Planner, Updates and Eval panels.
- Added local file ingestion and evidence-backed QBUS6600 demo data.
