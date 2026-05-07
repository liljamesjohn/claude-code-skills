# Claude Code Skills Marketplace

## Purpose

This repository is a Claude Code plugin marketplace for reusable agent skills. It publishes three plugins:

- `general` — session priming and codebase documentation skills.
- `git` — atomic commit workflow skill.
- `caveman` — compressed communication mode for Claude Code.

## Architecture map

| Area | Purpose | Key entry points |
| --- | --- | --- |
| `.claude-plugin/` | Marketplace manifest Claude Code reads when users add this repo as a marketplace. | `.claude-plugin/marketplace.json` |
| `plugins/general/` | General-purpose AI agent workflow skills. | `plugins/general/.claude-plugin/plugin.json`, `plugins/general/skills/*/SKILL.md` |
| `plugins/git/` | Git workflow skills and supporting scripts. | `plugins/git/.claude-plugin/plugin.json`, `plugins/git/skills/atomic-commits/SKILL.md` |
| `plugins/caveman/` | Claude-Code-only caveman mode skill plus hooks. | `plugins/caveman/.claude-plugin/plugin.json`, `plugins/caveman/hooks/*.js` |

## Install and use

Add the marketplace in Claude Code:

```bash
/plugin marketplace add liljamesjohn/claude-code-skills
```

Install plugins:

```bash
/plugin install general@claude-setup
/plugin install git@claude-setup
/plugin install caveman@claude-setup
```

## Validation

Run these after changing manifests, skills, or hooks:

```bash
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
claude plugin validate .
claude plugin validate plugins/general
claude plugin validate plugins/git
claude plugin validate plugins/caveman
git diff --check
```

For caveman hook changes, also run a temporary-config smoke test so hook writes do not touch real Claude config:

```bash
tmpdir=$(mktemp -d)
CLAUDE_CONFIG_DIR="$tmpdir" CAVEMAN_DEFAULT_MODE=ultra node plugins/caveman/hooks/caveman-activate.js >/tmp/caveman-activate.out
test "$(cat "$tmpdir/.caveman-active")" = "ultra"
rm -rf "$tmpdir" /tmp/caveman-activate.out
```

## Safe change rules

- Keep marketplace plugin entries in `.claude-plugin/marketplace.json` aligned with `plugins/<name>/.claude-plugin/plugin.json`.
- Keep each plugin self-contained. Claude Code copies plugin directories into cache, so hooks and scripts must only reference files under their plugin root.
- Do not add Cursor, Windsurf, Gemini, Codex, or standalone installer files unless the marketplace is intentionally expanded beyond Claude Code.
- Do not commit generated caches, `__pycache__`, local Claude config, or secret files.

## Documentation map

- `plugins/general/README.md` — general plugin structure and skills.
- `plugins/git/README.md` — atomic commit plugin and Git safety script.
- `plugins/caveman/README.md` — caveman mode skill, hooks, and flag flow.
