# AGENTS.md (StatPro)

## Active rules

- Stack: Python 3.11+, Pytest, Ruff / React, TypeScript, Vite.
- Make the smallest safe diff. Reuse existing code and dependencies; do not add speculative abstractions.
- Read only files needed for the request. Use `rg`/`rg --files` first and keep command output bounded.
- Run the narrowest relevant check, then broaden only when risk or failures require it.
- Keep replies concise: outcome, changed files, validation, remaining risk.

## Conditional context

- UI or styling change: read project `DESIGN.md` before editing.
- Implementation, debugging, or review: apply the relevant section of `CODEX.md`; do not load unrelated guides.
- Prior decisions or user preferences are material: read only the relevant memory file. Skip empty memory and pending drafts.
- Long session or explicit handoff request: use `handoff`/`context-save`. Do not create handoff artifacts for ordinary tasks.

## Skill routing

- Do not invoke a skill merely because it is installed.
- `ponytail`: implementation where a smaller design or diff matters.
- `diagnosing-bugs` or `systematic-debugging`: non-obvious failures only.
- `ponytail-review`: material code changes at completion; skip for read-only, config-only, or trivial edits.
- `caveman`, `grill-me`, memory, growth, curator, and installation skills: only when explicitly requested or their specialized workflow is clearly required.
- Do not install a skill or plugin unless the user explicitly requests it and no installed capability covers the task.

User instructions and repository safety rules take precedence.
