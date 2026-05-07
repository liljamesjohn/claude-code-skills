# Caveman Plugin

## Responsibility

`caveman` provides Claude-Code-only compressed communication mode. It owns the caveman skill, Claude Code hooks, and optional statusline badge. It deliberately excludes Cursor, Windsurf, Gemini, Codex, commit/review helper skills, and document compression tooling.

## Entry points

- `.claude-plugin/plugin.json` — registers the skill path and Claude Code hooks.
- `skills/caveman/SKILL.md` — source prompt for caveman levels, persistence, examples, and boundaries.
- `hooks/caveman-activate.js` — `SessionStart` hook that writes the active mode flag and injects the ruleset.
- `hooks/caveman-mode-tracker.js` — `UserPromptSubmit` hook that updates mode from prompts and reinforces active mode.
- `hooks/caveman-config.js` — default mode resolution and safe flag read/write helpers.
- `hooks/caveman-statusline.sh` / `hooks/caveman-statusline.ps1` — optional statusline badge scripts.

## Internal map

| Path | Purpose |
| --- | --- |
| `skills/caveman/SKILL.md` | Behavior definition for `lite`, `full`, `ultra`, `wenyan-lite`, `wenyan-full`, and `wenyan-ultra`. |
| `hooks/package.json` | Forces CommonJS so hook scripts can use `require()` safely under varied parent configs. |
| `hooks/caveman-config.js` | Reads `CAVEMAN_DEFAULT_MODE` or user config, validates modes, protects flag reads/writes. |
| `hooks/caveman-activate.js` | Loads `SKILL.md`, filters examples to the active mode, and emits hidden startup context. |
| `hooks/caveman-mode-tracker.js` | Handles `/caveman` commands, natural-language activation/deactivation, and per-turn reminders. |

## Data/control flow

```text
SessionStart hook -> .caveman-active flag -> statusline badge
SessionStart hook -> full caveman rules -> Claude hidden context
UserPromptSubmit hook -> prompt parsing -> .caveman-active flag
UserPromptSubmit hook -> active flag -> short reinforcement context
```

The flag path is `${CLAUDE_CONFIG_DIR}/.caveman-active`, falling back to `~/.claude/.caveman-active`. The valid modes are `off`, `lite`, `full`, `ultra`, `wenyan-lite`, `wenyan`, `wenyan-full`, and `wenyan-ultra`.

## Commands and validation

| Task | Command |
| --- | --- |
| Validate plugin | `claude plugin validate plugins/caveman` |
| Validate JSON | `python3 -m json.tool plugins/caveman/.claude-plugin/plugin.json >/dev/null` |
| Check whitespace | `git diff --check` |
| Smoke test activation | `CLAUDE_CONFIG_DIR="$(mktemp -d)" CAVEMAN_DEFAULT_MODE=ultra node plugins/caveman/hooks/caveman-activate.js >/tmp/caveman-activate.out` |

## Safe change rules

- Keep hook file references relative to `${CLAUDE_PLUGIN_ROOT}` or the hook directory; plugin installs run from Claude Code cache.
- Any flag write must use `safeWriteFlag()` from `caveman-config.js`.
- Any flag read used for model context or terminal output must validate against the mode whitelist.
- Preserve normal prose for security warnings, irreversible actions, and code/commit/PR content as defined in `SKILL.md`.
- Do not reintroduce bundled `commit`, `review`, or `compress` modes unless adding those skills as separate plugin entries.
