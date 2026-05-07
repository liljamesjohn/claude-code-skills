---
name: atomic-commits
description: Use this skill to create safe, focused, atomic Git commits with strict Conventional Commits messages. Proactively use only after a completed substantial work unit on a feature branch when the diff contains coherent commit-sized changes; otherwise wait for explicit user request. It partitions large diffs by intent, stages only specific files or hunks, verifies each unit, and never touches remote history.
compatibility: Requires git and filesystem access. Python 3.9+ can run the bundled read-only safety scanner.
---

# Atomic Commits

Create one or more focused Git commits that are independently reviewable, revertible, and cherry-pickable. Optimize commit messages for future AI/code agents: concise header, useful body, no diff duplication.

## Activation policy

Proactively invoke this skill only when all are true:

- Work is complete enough to preserve.
- Current branch is a feature branch.
- The diff contains one or more coherent logical units.
- Committing would preserve the user's intent.

Do **not** auto-trigger for exploratory edits, partial work, unresolved failures, review checkpoints, dirty generated output, or ambiguous changes. In those cases, wait for the user.

## Hard safety rules

- Refuse on `main`, `master`, `develop`, `release/*`, or any branch project docs mark protected unless the user explicitly overrides.
- Stop and ask on: no Git repo, detached HEAD, merge conflicts, ambiguous changes, or no coherent commit-sized unit.
- Never amend, rebase, reset, force-push, pull, merge, tag, or modify remote state.
- Never use `git add .`, `git add -A`, `git commit -a`, or `--no-verify`.
- Stage only explicit paths or explicit hunks.
- Never stage secrets, `.env*`, credentials, dependency directories, generated build artifacts, coverage, caches, logs, or large binaries unless explicitly requested.

## Available script

- `scripts/git-safety-scan.py` is read-only. It reports branch safety, upstream, status, conflicts, untracked files, risky paths, diff stats, and changed-file clusters.

Resolve the skill directory from the active `SKILL.md`, then run:

```bash
python3 "$SKILL_DIR/scripts/git-safety-scan.py" --repo "$REPO" --format markdown
```

Use `--format json` when planning with structured data.

## Commit workflow

1. **Run preflight**
   - Run the safety scanner.
   - Also inspect `git status --porcelain=v1 -uall`, current branch, upstream status, and untracked files.
   - If blocked by safety rules, stop before staging.

2. **Analyze the full diff**
   - Review `git diff --stat`, `git diff --name-status`, and relevant file diffs.
   - Partition by intent, not file. A commit should answer one "why".
   - Prefer multiple small commits over one broad commit.

3. **Plan atomic units**
   - For each unit, list: intent, paths/hunks, Conventional Commit header, verification.
   - If a file has mixed concerns, use hunk-level staging with `git add -p -- <path>` or equivalent.
   - Read `references/atomic-planning.md` if the diff is large or mixed.

4. **Verify before each commit**
   - Run relevant project-native checks when discoverable from scripts, Makefiles, CI, or docs.
   - Scope checks to the logical unit when possible; run broader checks when the unit affects shared behavior.
   - If checks fail, fix or stop. Do not commit while claiming passing verification.

5. **Stage safely**
   - Stage explicit files: `git add -- path/to/file`.
   - For mixed files, stage explicit hunks: `git add -p -- path/to/file`.
   - Re-check with `git diff --cached --stat` and `git diff --cached`.
   - Inspect staged diff for secrets/credentials before committing.

6. **Commit**
   - Commit only after `git diff --cached` contains exactly one logical unit.
   - Use strict Conventional Commits:
     ```text
     type(scope): imperative summary
     ```
   - Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
   - Use `!` only for breaking changes and include a `BREAKING CHANGE:` footer.
   - Include a body when it helps future agents understand intent, constraints, affected modules, verification, limitations, or follow-up.
   - Include required project/system trailers, if any.

7. **Continue**
   - After each commit, run `git status --porcelain=v1 -uall` and re-check remaining diff.
   - Continue until no coherent commit-sized changes remain.
   - Leave ambiguous or partial changes unstaged and report them.

## Message body guidance

Use `assets/commit-message-template.md` when a body is useful. Keep bodies factual and agent-oriented:

- What changed.
- Why it changed.
- Important design constraints.
- Affected files/modules.
- Verification actually run.
- Known limitations or follow-up.

Do not include noisy implementation dumps that duplicate the diff.

## Final response

Report only:

- Commits created: hash + header.
- Verification run per commit.
- Remaining uncommitted changes, if any.
- Any skipped risky files or blockers.
