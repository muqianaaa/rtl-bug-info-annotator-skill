# RTL Bug Info Annotator Skill

An installable skill for generating the `bug_desc` and `fix_hint` fields in
RTL bug benchmark annotations.

The skill is designed for Codex and Claude Code workflows that annotate
Verilog/SystemVerilog bug-fix cases from evidence:

- RTL module specification
- PR title and body
- linked issue text
- fix commit message
- raw unified diff or selected raw diff hunks

This skill packages a workflow for writing concise bug descriptions and
high-level repair suggestions from the collected benchmark evidence.

## What It Produces

```json
{
  "bug_desc": "2-4 evidence-supported sentences.",
  "fix_hint": "1-2 high-level repair suggestion sentences."
}
```

If the evidence is insufficient:

```json
{
  "status": "needs_review",
  "reason": "insufficient evidence"
}
```

## Install For Codex

Copy the skill directory into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R rtl-bug-info-annotator ~/.codex/skills/
```

On Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills"
Copy-Item -Recurse -Force ".\rtl-bug-info-annotator" "$env:USERPROFILE\.codex\skills\"
```

## Install For Claude Code

Install as a user-level Claude Code skill:

```bash
mkdir -p ~/.claude/skills
cp -R rtl-bug-info-annotator ~/.claude/skills/
```

Or install into a project:

```bash
mkdir -p .claude/skills
cp -R rtl-bug-info-annotator .claude/skills/
```

## Usage

Ask the agent:

```text
Use $rtl-bug-info-annotator to generate bug_desc and fix_hint from this RTL bug-fix case JSON.
```

The expected input JSON shape is documented in
`rtl-bug-info-annotator/SKILL.md`.

## Validation Helper

The skill includes a small validator:

```bash
python rtl-bug-info-annotator/scripts/validate_bug_info_case.py case.json
```

It checks required case fields and verifies that `patch_text` looks like raw
unified diff text rather than a natural-language patch summary.

## License

MIT License.
