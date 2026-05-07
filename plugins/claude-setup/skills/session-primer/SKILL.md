---
name: session-primer
description: Use this skill when starting or refreshing an agentic software engineering session and the agent needs to quickly understand a repository before working. It guides efficient inspection of codebase structure, documentation, commands, active Git state, and recent history, then outputs a compact project brief with only the facts needed to begin work.
compatibility: Requires filesystem access. Git is recommended for history and working-tree context. Python 3.9+ can run the bundled scanner.
---

# Session Primer

Prime a fresh engineering session with enough project context to work safely, without flooding the conversation. Build a compact mental model, then report only the high-signal facts.

## Core rule

Spend context like a budget:

- Prefer file/path inventories, manifests, and documentation indexes before reading source.
- Read complete files only when they are likely to change the working plan.
- Sample representative source entry points instead of traversing everything.
- Stop once you can identify architecture, commands, conventions, current Git state, and likely risk areas.
- Final output must be short: precise bullets and lists, not a full report.

## Available script

- `scripts/prime-scan.py` produces a compact repository scan: Git state, recent commits, manifests, docs, top directories, and a recommended read list.

Resolve the skill directory from the active `SKILL.md` location, then run:

```bash
python3 "$SKILL_DIR/scripts/prime-scan.py" --repo "$REPO" --format markdown
```

Use `--format json` if you need structured data.

## Priming workflow

### 1. Anchor the repository

Identify the repo root, branch, default upstream if available, and whether the working tree is dirty. If Git is unavailable, continue with filesystem inspection.

Read high-signal project instructions first when present:

- `AGENTS.md`, `CLAUDE.md`, `.agents/AGENTS.md`, `.github/copilot-instructions.md`
- Root `README.md`
- `docs/README.md`, architecture/deploy/contributing docs
- Package/workspace manifests and framework config

Do not inspect user-level skills or unrelated personal configuration while priming a repository.

### 2. Build the codebase map

Inventory before deep reading:

- Top-level directories and their apparent roles.
- Apps, packages, services, libraries, database/infra folders.
- Manifests and lockfiles that identify package managers and languages.
- Test, lint, typecheck, build, and dev commands.
- Routing, server, CLI, worker, schema, migration, and public API entry points.

For monorepos, map workspace boundaries first, then inspect only the packages/apps relevant to the user's likely task.

### 3. Use Git history as a signal

Inspect enough Git context to understand the active work:

- `git status --porcelain`
- `git log --oneline -10`
- Current branch name and default branch
- If a feature branch exists, compare against its merge base with the default branch to identify changed areas

Use recent commits to infer project direction and recurring conventions. Do not summarize every commit; extract only themes that affect the session.

### 4. Read source selectively

Read source in this order:

1. Public entry points and route/app shells.
2. Domain modules touched by current Git changes or recent commits.
3. Tests for the same areas to learn expected behavior.
4. Shared utilities only when they are called by the active area.

Stop reading when additional files repeat already-known patterns.

If a task is already known, narrow the primer to that task's likely files and dependencies.

### 5. Produce a compact session brief

Final output should fit on one screen. Use this structure:

```markdown
## Session primer

- Project: [one-line purpose]
- Stack: [languages/frameworks/package manager]
- Shape: [apps/packages/services/docs in a concise list]
- Commands: [validated or manifest-derived commands]
- Git state: [branch, dirty/clean, recent work themes]
- Key docs read: [short path list]
- Entry points: [short path list]
- Conventions/gotchas: [only non-obvious items]
- Ready context: [what work can begin safely now]
```

Omit sections with no useful information. Keep each list short.

## Context controls

- Default read cap: 5-10 high-signal files before reporting.
- Default Git cap: 10 commits and at most 25 changed files unless the task needs more.
- Prefer exact paths over prose explanations.
- Use counts and clusters for large areas instead of file-by-file lists.
- Never paste large package manifests, generated files, lockfiles, or migration bodies into the brief.

Read `references/priming-heuristics.md` only when the repository is large, unfamiliar, or ambiguous after the first scan. Use `assets/session-brief-template.md` if you need a copyable output template.

## Validation before finishing

- Every command in the brief must come from a manifest, script config, Makefile/task file, or project docs.
- Every path in the brief must exist.
- Claims about architecture must be supported by docs or source entry points you actually inspected.
- If uncertainty remains, state it as a short gap instead of guessing.
