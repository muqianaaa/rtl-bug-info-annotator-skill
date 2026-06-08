#!/usr/bin/env python3
"""Validate an RTL bug_info annotation case or generated output JSON."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


CASE_REQUIRED = {
    "repo",
    "lang",
    "rtl_files",
    "spec",
    "pr_title",
    "pr_body",
    "commit_message",
    "issue_text",
    "patch_text",
}


def looks_like_diff(text: str) -> bool:
    if not isinstance(text, str) or not text.strip():
        return False
    return bool(
        re.search(r"(?m)^diff --git ", text)
        or re.search(r"(?m)^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@", text)
        or (re.search(r"(?m)^\+\+\+ ", text) and re.search(r"(?m)^--- ", text))
    )


def validate_case(data: dict) -> list[str]:
    errors: list[str] = []
    missing = sorted(CASE_REQUIRED - data.keys())
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
    if "rtl_files" in data and not isinstance(data["rtl_files"], list):
        errors.append("rtl_files must be a list")
    if "patch_text" in data and not looks_like_diff(data["patch_text"]):
        errors.append("patch_text must be raw unified diff text or selected raw diff hunks")
    return errors


def validate_generated(data: dict) -> list[str]:
    errors: list[str] = []
    if set(data.keys()) == {"status", "reason"}:
        if data["status"] != "needs_review":
            errors.append("status must be needs_review")
        return errors
    if set(data.keys()) != {"bug_desc", "fix_hint"}:
        errors.append("generated output must contain exactly bug_desc and fix_hint")
        return errors
    for key in ("bug_desc", "fix_hint"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{key} must be a non-empty string")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_bug_info_case.py <case-or-output.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        print("ERROR: top-level JSON must be an object", file=sys.stderr)
        return 1

    if "patch_text" in data:
        errors = validate_case(data)
        kind = "case"
    else:
        errors = validate_generated(data)
        kind = "generated_output"

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: valid {kind} JSON")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
