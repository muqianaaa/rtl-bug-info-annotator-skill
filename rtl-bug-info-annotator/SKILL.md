---
name: rtl-bug-info-annotator
description: Generate and review the bug_desc and fix_hint fields for RTL benchmark bug_info annotations from hardware bug-fix evidence such as RTL specs, PR titles/bodies, issues, commit messages, and raw unified diffs. Use when Codex or Claude Code needs to annotate Verilog/SystemVerilog/Chisel bug-fix cases, produce concise evidence-grounded bug descriptions and repair hints, avoid patch leakage, or decide whether evidence is insufficient.
---

# RTL Bug Info Annotator

Use this skill to turn a real RTL bug-fix case into the benchmark fields:

```json
{
  "bug_info": {
    "bug_desc": "...",
    "fix_hint": "..."
  }
}
```

This skill packages Section 6 of the benchmark workflow: produce concise, evidence-supported `bug_desc` and `fix_hint` text fields that explain the bug scenario, failure, approximate root-cause scope, and high-level repair direction without leaking full patch code.

## Inputs

Require a case object with these fields:

```json
{
  "repo": "owner/repo",
  "lang": "v/sv/chisel",
  "rtl_files": ["target RTL file paths"],
  "spec": "generated behavior spec text",
  "pr_title": "PR title",
  "pr_body": "PR body",
  "commit_message": "fix commit message",
  "issue_text": "linked issue text or empty string",
  "patch_text": "raw unified diff or selected raw diff hunks"
}
```

Treat `patch_text` as invalid if it is only a natural-language summary. It must be raw unified diff text or selected raw diff hunks with file paths and hunk bodies.

## Workflow

1. Validate the evidence object.
   - Confirm required fields exist.
   - Confirm `patch_text` looks like a raw diff or selected diff hunk.
   - Prefer running `scripts/validate_bug_info_case.py <case.json>` when the input is in a file.

2. Focus evidence on target RTL files.
   - Prioritize hunks touching `rtl_files`.
   - Keep PR/issue/commit text as supporting evidence.
   - Do not use unrelated tests, logs, or design rules unless they appear in the provided evidence.

3. Generate `bug_desc`.
   - Write 2-4 sentences.
   - Include trigger condition or scenario.
   - Include observable incorrect behavior.
   - Include approximate root-cause scope, such as module, file, state, condition, or signal path.

4. Generate `fix_hint`.
   - Write 1-2 sentences.
   - Describe the high-level repair direction.
   - Mention module/file/key signal names only if they appear in the evidence.
   - Do not copy patch code, complete assignments, expressions, or full conditions.

5. Review the result.
   - Check evidence support, quality, no patch copying, no hallucination, and valid patch evidence.
   - If any core evidence is missing, output `{"status":"needs_review","reason":"insufficient evidence"}` instead of guessing.
   - Use `references/prompts.md` for exact generation and review prompt templates.

## Output

Return valid JSON only when generating the annotation:

```json
{
  "bug_desc": "2-4 evidence-supported sentences.",
  "fix_hint": "1-2 high-level repair suggestion sentences."
}
```

If the case cannot be annotated safely:

```json
{
  "status": "needs_review",
  "reason": "insufficient evidence"
}
```

When reviewing an existing annotation, return:

```json
{
  "passed": true,
  "checks": {
    "evidence_supported": true,
    "bug_desc_quality": true,
    "fix_hint_quality": true,
    "no_patch_copying": true,
    "no_hallucination": true,
    "patch_evidence_valid": true
  },
  "reasoning": "one sentence summary",
  "revised": {
    "bug_desc": "...",
    "fix_hint": "..."
  }
}
```

## Quality Rules

- Generate only from provided PR, issue, commit, spec, and patch evidence.
- Do not invent tests, failure logs, protocol rules, or module behavior.
- Do not output complete repair code.
- Do not directly copy patch expressions into `fix_hint`.
- Keep `bug_desc` useful to an engineer unfamiliar with the project.
- Keep `fix_hint` high-level enough that it guides repair without giving away the exact patch.

## Reference

- Read `references/prompts.md` when exact generation or review prompt text is needed.
