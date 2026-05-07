# Git Plugin

## Responsibility

`git` packages Git workflow skills. It currently contains `atomic-commits`, which helps create safe, focused commits with strict Conventional Commit messages. It does not push, merge, rebase, or mutate remote state by itself.

## Entry points

- `.claude-plugin/plugin.json` — plugin metadata and `skills` path.
- `skills/atomic-commits/SKILL.md` — commit workflow rules and safety requirements.
- `skills/atomic-commits/scripts/git-safety-scan.py` — read-only scanner for branch, status, risky paths, and diff clusters.

## Internal map

| Path | Purpose |
| --- | --- |
| `skills/atomic-commits/assets/commit-message-template.md` | Optional commit body template. |
| `skills/atomic-commits/references/atomic-planning.md` | Guidance for splitting mixed changes into atomic units. |
| `skills/atomic-commits/scripts/git-safety-scan.py` | Preflight scanner used before staging/committing. |

## Data/control flow

Claude Code loads the `atomic-commits` skill from `skills/atomic-commits/SKILL.md`. When invoked, the skill directs the agent to run Git read operations and the safety scanner before staging explicit paths or hunks. Commit creation remains an agent action after review and validation, not automatic plugin behavior.

## Commands and validation

| Task | Command |
| --- | --- |
| Validate plugin | `claude plugin validate plugins/git` |
| Validate JSON | `python3 -m json.tool plugins/git/.claude-plugin/plugin.json >/dev/null` |
| Check whitespace | `git diff --check` |
| Run scanner manually | `python3 plugins/git/skills/atomic-commits/scripts/git-safety-scan.py --repo . --format markdown` |

## Safe change rules

- Preserve the skill safety rules: explicit staging only, no force-push, no protected-branch commits unless user overrides.
- Keep `git-safety-scan.py` read-only.
- Update `references/atomic-planning.md` when commit-splitting behavior changes.
