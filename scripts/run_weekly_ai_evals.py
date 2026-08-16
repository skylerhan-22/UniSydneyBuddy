from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from unisydneybuddy.pipeline.module_ai import summarise_module, validate_module_summary_coverage


ROOT = Path(__file__).resolve().parents[1]


def flattened(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False).casefold()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the four-course Weekly Brief AI evaluation")
    parser.add_argument("--live", action="store_true", help="Call the configured OpenAI API")
    args = parser.parse_args()
    cases = json.loads((ROOT / "data/evals/weekly_ai_cases.json").read_text(encoding="utf-8"))
    if not args.live:
        print(json.dumps({"cases": len(cases), "courses": [case["course_code"] for case in cases], "status": "ready", "live_api_called": False}, ensure_ascii=False, indent=2))
        return 0
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required for --live")
    rows = []
    for case in cases:
        result = summarise_module(
            course_title=case["course_title"],
            week_number=case["week"],
            module_names=[f"Week {case['week']}"],
            module_items=case["module_items"],
            module_text=case["module_text"],
            announcements=[],
            language="中文",
        )
        readable = [item for item in case["module_items"] if f"{item}\n[NO READABLE BODY SYNCED]" not in case["module_text"]]
        text = flattened(result)
        passed = validate_module_summary_coverage(
            result,
            expected_items=case["module_items"],
            readable_items=readable,
            announcement_titles=[],
        ) and all(term.casefold() in text for term in case["expected_terms"]) and not any(term.casefold() in text for term in case["forbidden_terms"])
        rows.append({"course_code": case["course_code"], "passed": passed})
    report = {"cases": rows, "passed": sum(row["passed"] for row in rows), "total": len(rows)}
    output = ROOT / "data/evals/latest_weekly_ai_eval.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
