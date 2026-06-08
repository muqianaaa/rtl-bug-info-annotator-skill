#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from common import load_json_or_jsonl, validate_case


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_case.py <case.json|case.jsonl>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    cases = load_json_or_jsonl(path)
    failed = False
    for index, case in enumerate(cases, 1):
        errors = validate_case(case)
        if errors:
            failed = True
            label = case.get("id") or case.get("case_id") or f"line/index {index}"
            for error in errors:
                print(f"ERROR {label}: {error}", file=sys.stderr)
    if failed:
        return 1
    print(f"OK: {len(cases)} case(s) valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
