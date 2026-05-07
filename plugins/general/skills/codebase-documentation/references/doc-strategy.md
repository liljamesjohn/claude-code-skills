# Documentation Strategy

Use this reference when deciding what to document, where README files belong, or how to update documentation from Git changes.

## Repository survey order

Read high-signal files first:

1. Root manifests and configs: package manager files, workspace config, language build files, framework config, Docker/compose, CI, Makefile/Taskfile/Justfile.
2. Agent/developer instructions: AGENTS, CLAUDE, CONTRIBUTING, docs/deploying, architecture docs.
3. Application/package manifests under common boundaries: `apps`, `packages`, `services`, `libs`, `crates`, `cmd`, `internal`, `src`.
4. Entry points: app routers, server startup, CLI main files, public exports, schema files, migrations, infra modules.
5. Tests and examples that reveal intended behavior.

Avoid reading every source file before forming a map. Sample representative files first, then drill into areas selected for documentation.

## README hierarchy

### Root README

The root README is the agent's first navigation layer. Include:

- What the repository builds and why it exists.
- Major applications/packages/services and ownership boundaries.
- Architecture/data-flow overview.
- Development setup and validation commands.
- Environment/configuration model without secrets.
- Documentation map linking nested READMEs.
- Cross-cutting conventions and gotchas.

Keep root details shallow. Link to nested README files for local details.

### App/package/service README

Create one when the folder is independently buildable, deployable, versioned, imported by other modules, or operationally important.

Include:

- Responsibility and boundaries.
- Entry points and public APIs.
- Local commands for build/test/lint/dev.
- Dependencies on other workspace packages/services.
- Runtime configuration and external integrations.
- Local extension rules and test strategy.

### Dense-folder README

Create one when a folder has enough complexity that agents will otherwise waste time re-discovering structure. Good signals:

- 20+ meaningful source files.
- Multiple subdomains with a shared convention.
- Routing trees, state machines, job processors, workflow definitions, or schema-heavy code.
- Non-obvious invariants or generated-code boundaries.
- Frequent Git churn across many files.

Do not create one for a folder whose children are self-explanatory and already covered by a parent README.

## Incremental update algorithm

1. Identify documentation files:
   - `README.md`
   - `**/README.md`
   - `docs/**/*.md`, `docs/**/*.mdx`
   - project-specific architecture or agent instruction files only if the user asked to keep them updated.
2. Find the latest commit touching documentation:
   - Prefer the latest commit touching the documentation file closest to the changed code.
   - Fall back to the latest commit touching any README/docs file.
3. Build a changed-file set:
   - `git diff --name-status <doc_commit>..HEAD -- .`
   - Add uncommitted changes from `git status --porcelain`.
4. Classify each changed file:
   - Manifest/config/build/CI changes affect root or package README commands/setup.
   - Public API/entrypoint changes affect package/app README API and extension sections.
   - Route/controller/job/schema changes affect local architecture/data-flow sections.
   - Tests often indicate behavior changes; read paired source and update behavior notes if needed.
5. Select docs to patch:
   - Nearest ancestor README for local changes.
   - Root README for repo map, setup, command, architecture, or cross-cutting changes.
   - Create a new local README only if changed code reveals a durable complex area.

## Information quality bar

Good agent-facing documentation is:

- Specific: names real files, commands, modules, and boundaries.
- Operational: tells agents how to validate and where to edit.
- Durable: avoids listing every small implementation detail likely to churn.
- Local: explains an area where the code lives.
- Honest: states uncertainty only when the code does not provide an answer.

Remove or avoid:

- "This folder contains..." sentences that only restate filenames.
- Generic framework explanations.
- Outdated setup steps copied from templates.
- Large generated file lists.
- Claims about production infrastructure unless verified in repo config.

## Suggested update summary

When finishing, report:

```markdown
Updated documentation:
- `README.md` — refreshed repository map and validation commands.
- `apps/web/README.md` — added auth flow and route ownership notes.

Change basis:
- Compared code since documentation commit `<hash>`.
- Key changed areas: `apps/web/app/(auth)`, `packages/auth`, `supabase/migrations`.
```
