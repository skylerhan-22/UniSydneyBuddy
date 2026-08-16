#!/usr/bin/env python3
"""Validate the QBUS6600 gold dataset without external dependencies."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from unisydneybuddy.quality import validate_bundle  # noqa: E402


def main() -> int:
    gold_path = ROOT / "data" / "evals" / "qbus6600_gold.json"
    bundle = json.loads(gold_path.read_text(encoding="utf-8"))
    issues = validate_bundle(bundle)
    if issues:
        for issue in issues:
            print(f"FAIL {issue.code}: {issue.message}")
        return 1
    print("PASS qbus6600_gold.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

