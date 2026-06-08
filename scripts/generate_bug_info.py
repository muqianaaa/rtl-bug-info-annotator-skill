#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    add_llm_args,
    extract_json_object,
    load_json_or_jsonl,
    openai_compatible_chat,
    read_text,
    render_prompt,
    require_api_key,
    sha256_text,
    stable_case_id,
    validate_case,
    write_jsonl,
)


def valid_annotation(data: dict) -> bool:
    if set(data.keys()) == {"status", "reason"}:
        return data.get("status") == "needs_review"
    return set(data.keys()) == {"bug_desc", "fix_hint"} and all(
        isinstance(data.get(key), str) and data[key].strip()
        for key in ("bug_desc", "fix_hint")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate RTL bug_info annotations.")
    parser.add_argument("input", help="case JSON or JSONL")
    parser.add_argument("output", help="output JSONL")
    parser.add_argument("--prompt", default=str(Path(__file__).resolve().parents[1] / "prompts" / "generate_bug_info.txt"))
    add_llm_args(parser)
    args = parser.parse_args()

    api_key = require_api_key(args.api_key)
    prompt_template = read_text(args.prompt)
    prompt_hash = sha256_text(prompt_template)
    cases = load_json_or_jsonl(args.input)
    records = []

    for index, case in enumerate(cases):
        case_id = stable_case_id(case, index)
        errors = validate_case(case)
        if errors:
            records.append({"id": case_id, "error": "invalid_case", "details": errors})
            continue

        case_json = json.dumps(case, ensure_ascii=False, sort_keys=True, indent=2)
        prompt = render_prompt(prompt_template, {"CASE_JSON": case_json})
        raw = openai_compatible_chat(
            base_url=args.base_url,
            api_key=api_key,
            model=args.model,
            prompt=prompt,
            temperature=args.temperature,
            top_p=args.top_p,
            seed=args.seed,
            timeout=args.timeout,
            max_retries=args.max_retries,
        )
        try:
            annotation = extract_json_object(raw)
            if not valid_annotation(annotation):
                raise ValueError("annotation JSON does not match expected schema")
            record = {"id": case_id, "annotation": annotation}
        except Exception as exc:
            record = {"id": case_id, "error": "invalid_model_output", "details": str(exc), "raw_output": raw}

        record["metadata"] = {
            "model": args.model,
            "base_url": args.base_url,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "seed": args.seed,
            "prompt_path": args.prompt,
            "prompt_sha256": prompt_hash,
        }
        records.append(record)

    write_jsonl(args.output, records)
    print(f"Wrote {len(records)} record(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
