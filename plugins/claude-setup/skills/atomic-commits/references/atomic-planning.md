# Atomic Planning

Use this reference only when changes are large, mixed, or difficult to split.

## Partition by intent

A good atomic commit has one intent and can be reviewed, reverted, or cherry-picked independently.

Good units:

- Add a feature and its direct tests.
- Fix one bug and update the assertion that covers it.
- Rename one concept across code and docs.
- Add one migration plus code that tolerates it.
- Update one dependency/tooling concern.

Bad units:

- "Misc cleanup."
- Formatting plus behavior changes in the same commit.
- Several unrelated fixes because they touch the same file.
- Generated artifacts mixed with source changes.
- Tests updated without the behavior they validate, unless the tests expose existing behavior.

## Mixed files

When one file contains multiple concerns:

1. Inspect full file diff.
2. Stage only relevant hunks with `git add -p -- <path>`.
3. Use split hunks when available.
4. If patch staging cannot isolate safely, ask whether to defer or manually edit into separable changes.

Never stage unrelated hunks just because they share a file with the desired unit.

## Safety review before staging

Exclude by default:

- `.env`, `.env.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, credential stores, token dumps.
- `node_modules`, `vendor`, virtualenvs, dependency caches.
- Build output: `dist`, `build`, `.next`, `.nuxt`, `target`, `coverage`.
- Logs, caches, screenshots, videos, archives, large binaries.

If the user explicitly wants one of these committed, stage it by exact path only and mention it in the commit body.

## Verification selection

Prefer project-native checks:

- Package scripts (`test`, `lint`, `typecheck`, `check`, `format:check`).
- Make/Just/Task targets.
- CI workflow commands.
- README or agent instruction commands.

Match check scope to commit scope:

- Docs-only: spelling/link/style check if available; otherwise `Verification: not run, docs-only change`.
- Tests-only: run the relevant test command or note why not.
- Shared code: run unit tests plus type/lint checks if available.
- Build/tooling: run the tooling command affected by the change.

Do not invent results. If skipped, say exactly why.

## Conventional Commit details

Header format:

```text
type(scope): imperative summary
```

- `type` must be one of: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- `scope` is the smallest useful affected area: package, app, module, route, command, config, docs.
- Summary is imperative and concise: "add auth retry guard", not "added auth retry guard".
- Lowercase summary unless naming code symbols.
- Use `!` only for breaking changes: `feat(api)!: remove legacy token field`.
- Breaking commits require a footer:
  ```text
  BREAKING CHANGE: [what changed and migration impact]
  ```

## Agent-optimized body

Include a body when the diff's intent is not obvious from the header. Future agents should understand why the commit exists without rereading every line.

Useful body sections:

```text
What:
- ...

Why:
- ...

Constraints:
- ...

Affected:
- `path`

Verification:
- command or "not run, reason"
```

Keep bodies short. Do not paste the diff.
