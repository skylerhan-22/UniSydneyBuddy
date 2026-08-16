# UniSydneyBuddy UI Acceptance Report

Date: 2026-08-14  
Scope: Demo v0.4.1

## Result

The current demo passes the functional and copy acceptance baseline. The automated suite contains 52 passing tests, supplemented by real-browser interaction checks.

| Area | Coverage | Result |
|---|---|---|
| Course catalogue | All 4 course buttons, active state and course-specific content | Pass |
| Semester Overview | Summary, class format, Assessment Map and Week 1–13 schedule | Pass |
| Weekly Brief | All 4 courses × all 13 week values; published and unpublished states | Pass |
| Language | Chinese and English navigation and core actions | Pass |
| Assignment upload | TXT live parse plus PDF/DOCX/PPTX/MD/TXT type declaration | Pass |
| Team planning | 3–4 member options, incomplete-owner validation | Pass |
| Assignment files | 9 distinct templates, one ZIP bundle, distinct download payloads | Pass |
| Plan export | Disabled before all owners are selected; generated plan content unit-tested | Pass |
| Student-facing chrome | Irrelevant Deploy and Main menu controls removed | Pass |
| Four-course parity | Identical Project Planner stages and controls in Chinese and English | Pass |
| Upload gating | Results and planning controls appear only after successful Brief parsing | Pass |
| Course isolation | Brief, member and Part state are isolated by course and assignment | Pass |
| State persistence | Returning to the same course-assignment preserves its parsed state unchanged | Pass |
| Multi-file grouping | Multiple Briefs are grouped into separate detected Projects by assignment | Pass |
| Mock document scenario | 4 short QBUS files grouped into 3 correct Projects in Chinese and English | Pass |

## Copy decisions

- Keep course names, Assessment, Lecture, Tutorial and established academic terms in English where they match Canvas.
- Translate workflow instructions and decisions in Chinese mode.
- Use `下载模板` instead of the ambiguous `下载` for individual assignment files.
- Keep table search, CSV download and fullscreen as secondary platform controls because they are useful for long schedules and assessment lists.

## Evidence boundary

The interface does not create detailed preparation tasks for unpublished Canvas Modules. Project planning uses the observed assessment summary as its baseline; facts absent from the full Assignment Brief, such as an unknown team-size rule, remain explicitly unconfirmed rather than being invented.

## v0.4.2 parity retest

The Project Planner is now present for all four courses rather than stopping at a preview. Course-specific facts continue to differ where the source differs: MKTG6104 preserves its known 4–6 person team range, while MKTG6018 and SIEN6006 clearly label team size as requiring confirmation from the full brief. The capability sequence itself is identical in both languages.
