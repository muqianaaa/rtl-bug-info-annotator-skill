# RTL Bug Info Annotator

A reproducible toolchain for generating `bug_desc` and `fix_hint` fields in
RTL bug benchmark annotations.

The toolchain uses fixed prompt templates, explicit model parameters, and
JSON/JSONL input-output files. It is intended for Verilog/SystemVerilog
bug-fix cases with collected evidence:

- RTL module specification
- PR title and body
- linked issue text
- fix commit message
- raw unified diff or selected raw diff hunks

## Repository Layout

```text
prompts/
  generate_bug_info.txt
  review_bug_info.txt
scripts/
  generate_bug_info.py
  review_bug_info.py
  validate_case.py
examples/
  case.jsonl
  generated.jsonl
```

## Input Format

Each case is a JSON object. Inputs may be a single JSON object, a JSON array, or
JSONL with one case per line.

```json
{
  "id": "case-id",
  "repo": "owner/repo",
  "lang": "sv",
  "rtl_files": ["rtl/example.sv"],
  "spec": "module behavior specification",
  "pr_title": "PR title",
  "pr_body": "PR body",
  "commit_message": "fix commit message",
  "issue_text": "",
  "patch_text": "raw unified diff or selected raw diff hunks"
}
```

`patch_text` should be raw unified diff text or selected raw diff hunks.

## Validate Cases

```bash
python scripts/validate_case.py examples/case.jsonl
```

## Generate Annotations

The scripts call an OpenAI-compatible Chat Completions endpoint.

```bash
export OPENAI_API_KEY="..."
python scripts/generate_bug_info.py examples/case.jsonl outputs/generated.jsonl \
  --model gpt-4.1 \
  --temperature 0 \
  --top-p 1
```

For a custom compatible endpoint:

```bash
python scripts/generate_bug_info.py examples/case.jsonl outputs/generated.jsonl \
  --base-url https://api.openai.com/v1 \
  --model gpt-4.1 \
  --temperature 0 \
  --top-p 1
```

Each output line records:

- input case id
- generated annotation JSON
- model name
- base URL
- decoding parameters
- prompt SHA-256

## Review Annotations

```bash
python scripts/review_bug_info.py examples/case.jsonl outputs/generated.jsonl outputs/reviewed.jsonl \
  --model gpt-4.1 \
  --temperature 0 \
  --top-p 1
```

## Prompt Reproducibility

Prompt templates are stored as plain text under `prompts/`. Do not edit prompts
between runs unless the run is intentionally a new experiment. The scripts store
the prompt hash in every output record so result files can be matched to the
exact prompt version used.

LLM APIs can still change model weights or serving behavior over time. To make
runs auditable, always record the model name, base URL, prompt hash, input file,
date, and decoding parameters.

## License

MIT License.
