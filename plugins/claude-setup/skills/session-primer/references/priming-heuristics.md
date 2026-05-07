# Priming Heuristics

Use this reference only when the initial scan leaves uncertainty or the repository is large enough that indiscriminate reading would bloat context.

## Source priority

Read in this order:

1. Agent/developer instructions: `AGENTS.md`, `CLAUDE.md`, contributing docs, workflow docs.
2. Project overview docs: root `README.md`, `docs/README.md`, architecture/deploy docs.
3. Manifests and workspace config: package manager files, build config, language manifests, framework config.
4. Entry points: app router, server startup, CLI main, worker registration, public exports, schema definitions.
5. Active areas: files changed in the working tree or feature branch.
6. Tests for active areas.

Skip generated/vendor/build output unless the user's task specifically involves it.

## Recognizing repository shape

- `apps`, `packages`, `libs`, `services`, `crates`, `cmd`, `internal` usually signal a multi-package or multi-service layout.
- `src/app`, `app`, `pages`, `routes`, `server`, `api`, `workers`, `jobs` usually contain execution entry points.
- `supabase`, `prisma`, `drizzle`, `migrations`, `schema` usually need extra care because they define persistent data shape.
- `.github`, `lefthook`, `pre-commit`, `biome`, `eslint`, `oxlint`, `ruff`, `cargo`, `go test`, and CI configs often reveal validators.

## Git analysis

Use Git to answer three questions:

1. What branch or feature line is active?
2. What files are currently changed?
3. What themes appear in recent commits?

For feature branches, compare against the default branch merge base when available. Cluster changed files by top-level or package path instead of listing everything.

## Reading stop conditions

Stop priming when you can name:

- The project purpose in one sentence.
- Main technologies and package manager.
- The top-level map and important local areas.
- How to run checks or where commands are defined.
- Active Git work and likely risk areas.
- The files/docs you would open first for a concrete task.

More reading is only justified if a current task depends on details not covered above.

## Final brief quality bar

Good:

- `Stack: Next.js, TypeScript, Bun, Supabase; validators from package.json and AGENTS.md.`
- `Entry points: src/app, src/lib/supabase, supabase/migrations.`
- `Git state: feature branch, clean tree, recent commits focus on Supabase auth SMTP.`

Bad:

- Long prose history of the repository.
- Exhaustive file tree.
- Generic claims like "uses best practices."
- Commands inferred from framework defaults but not verified in the repo.
