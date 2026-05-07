# General Plugin

## Responsibility

`general` packages broad agent workflow skills that help Claude Code understand and document repositories. It does not own Git commit workflows or communication style hooks.

## Entry points

- `.claude-plugin/plugin.json` — plugin metadata and `skills` path.
- `skills/session-primer/SKILL.md` — repository priming workflow.
- `skills/codebase-documentation/SKILL.md` — AI-agent-focused documentation workflow.

## Internal map

| Path | Purpose |
| --- | --- |
| `skills/session-primer/assets/` | Session brief output template. |
| `skills/session-primer/references/` | Heuristics for efficient repository inspection. |
| `skills/session-primer/scripts/prime-scan.py` | Read-only repository scan helper. |
| `skills/codebase-documentation/assets/` | README templates. |
| `skills/codebase-documentation/references/` | Documentation strategy guidance. |
| `skills/codebase-documentation/scripts/repo-map.py` | Read-only documentation inventory helper. |

## Data/control flow

Claude Code loads `plugin.json`, discovers `skills/`, then invokes each `SKILL.md` based on the skill frontmatter description and user request. Bundled scripts are only helpers referenced by the skill instructions; they are not hooks and do not run automatically.

## Commands and validation

| Task | Command |
| --- | --- |
| Validate plugin | `claude plugin validate plugins/general` |
| Validate JSON | `python3 -m json.tool plugins/general/.claude-plugin/plugin.json >/dev/null` |
| Check whitespace | `git diff --check` |

## Safe change rules

- Keep skill directories in `skills/<skill-name>/SKILL.md` format.
- Keep helper scripts read-only unless the skill explicitly documents file writes.
- If a skill name changes, update both the skill frontmatter and any marketplace/user-facing references.
