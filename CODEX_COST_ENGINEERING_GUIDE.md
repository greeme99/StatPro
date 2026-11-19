# StatPro Codex Cost Profile

## Applied defaults

- Project instructions are conditional: design, memory, handoff, and review material are loaded only when the task needs them.
- StatPro `.codex/config.toml` disables office, design, browser automation, and Claude Cowork plugins for this repository. `codex-app-tools` remains enabled.
- No new skill was installed. Existing coding skills already cover implementation, debugging, review, and handoff.
- Global skills were reduced from 853 discovered manifests to 21 active manifests. The other 832 were moved, not deleted, to `~/.agents/skills-disabled/20261115-01/`.

## Skill policy

| State | Skills | Use |
|---|---|---|
| Default | `ponytail` | Minimal implementation when code changes are requested |
| Conditional | `diagnosing-bugs`, `systematic-debugging`, `ponytail-review` | Non-obvious failures or material completion review |
| Explicit/long task | `handoff`, `context-save`, `context-restore` | Session continuity only |
| Explicit only | `caveman`, `grill-me`, growth/curator/install skills | Specialized workflow requested by the user |
| Active | 5 system + 16 coding skill manifests | Available to StatPro chats |
| Archived | 832 duplicate or non-StatPro skill manifests | Excluded from discovery; recoverable |

## Restore

- Configuration backups: `C:\Users\0208m\.codex\backups\statpro-token-efficiency-20261115-01\`.
- Restore archived skills from `C:\Users\0208m\.agents\skills-disabled\20261115-01\agent-skills\` or `codex-skills\` to their original skill root. The initially nested `gstack`, `synced`, and `.trash` folders are stored directly under the dated archive.
- Re-enable a project plugin by changing only its entry in `.codex/config.toml` to `enabled = true`, then start a new Codex chat.

## Operating rule

Use a fresh chat after configuration changes. Keep one outcome per chat where practical; use handoff only when retained decisions are cheaper than rediscovery.
