#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REQUIRED_CASE_FIELDS = {
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


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_jsonl(path: str | Path, records: list[dict[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def load_json_or_jsonl(path: str | Path) -> list[dict[str, Any]]:
    text = read_text(path).strip()
    if not text:
        return []
    if text[0] in "[{":
        data = json.loads(text)
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return data
        raise ValueError("JSON input must be an object or an array of objects")
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"line {line_no}: JSONL record must be an object")
        records.append(item)
    return records


def looks_like_diff(text: str) -> bool:
    if not isinstance(text, str) or not text.strip():
        return False
    return bool(
        re.search(r"(?m)^diff --git ", text)
        or re.search(r"(?m)^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@", text)
        or (re.search(r"(?m)^\+\+\+ ", text) and re.search(r"(?m)^--- ", text))
    )


def validate_case(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_CASE_FIELDS - case.keys())
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
    if "rtl_files" in case and not isinstance(case["rtl_files"], list):
        errors.append("rtl_files must be a list")
    if "patch_text" in case and not looks_like_diff(case["patch_text"]):
        errors.append("patch_text must be raw unified diff text or selected raw diff hunks")
    return errors


def stable_case_id(case: dict[str, Any], index: int) -> str:
    value = case.get("id") or case.get("case_id")
    if value:
        return str(value)
    digest = hashlib.sha256(
        json.dumps(case, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    return f"case-{index + 1}-{digest}"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_prompt(template: str, replacements: dict[str, str]) -> str:
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            raise
        data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("model output must be a JSON object")
    return data


def openai_compatible_chat(
    *,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    temperature: float,
    top_p: float,
    seed: int | None,
    timeout: int,
    max_retries: int,
) -> str:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "top_p": top_p,
    }
    if seed is not None:
        payload["seed"] = seed

    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    for attempt in range(max_retries + 1):
        request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError) as exc:
            if attempt >= max_retries:
                raise RuntimeError(f"LLM request failed after {attempt + 1} attempts: {exc}") from exc
            time.sleep(2**attempt)
    raise RuntimeError("unreachable")


def add_llm_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY"))
    parser.add_argument("--model", required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--max-retries", type=int, default=2)


def require_api_key(api_key: str | None) -> str:
    if not api_key:
        print("ERROR: set OPENAI_API_KEY or pass --api-key", file=sys.stderr)
        raise SystemExit(2)
    return api_key
