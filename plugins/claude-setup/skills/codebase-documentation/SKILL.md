---
name: codebase-documentation
description: Use this skill when creating or updating codebase documentation for AI coding agents. It covers initial repository documentation, monorepo/package/app README hierarchies, dense-folder documentation, and efficient incremental updates by reviewing Git changes since documentation was last updated.
compatibility: Requires filesystem access and git for incremental updates; Python 3.9+ improves repository inventory via the bundled script.
---

# Codebase Documentation

Create practical, current documentation that helps AI agents perform agentic software development in an unfamiliar codebase. Prefer concise, navigable README files over broad prose.

## Core principles

- Document what an agent needs to act safely: architecture, entry points, commands, data flow, invariants, conventions, extension points, and gotchas.
- Keep docs close to the code they explain. Use one root `README.md`, then nested `README.md` files for apps, packages, services, libraries, and dense folders.
- Optimize for future incremental updates. Include enough structure that a later agent can map code changes to the right README quickly.
- Do not rewrite stable documentation unnecessarily. When updating, inspect Git changes since the last documentation update and patch only affected sections/files.
- Avoid marketing copy, exhaustive API reference, and generic best practices the agent already knows.

## Available script

- `scripts/repo-map.py` inventories a repository, finds README files, identifies likely documentation targets, and reports changed files since the latest commit that touched documentation.

Resolve the skill directory from the active `SKILL.md` location, then run:

```bash
python3 "$SKILL_DIR/scripts/repo-map.py" --repo "$REPO" --format markdown --since-doc-update
```

Use `--format json` when you need machine-readable output.

## Workflow

### 1. Establish scope

Use the current repository if the user does not name a path. For a monorepo, assume the whole repo unless the user names a package/app.

Identify:

- Git root and current branch.
- Package managers, build systems, frameworks, runtime languages.
- Existing documentation files: root `README.md`, nested `README.md`, `docs/`, agent instructions, architecture notes.
- Repository shape: apps, packages, services, libraries, database/schema folders, infra, scripts, tests.

### 2. Decide initial creation vs incremental update

**Initial documentation** when no adequate docs exist or the user asks to document the whole codebase:

1. Inventory the full repo, ignoring generated/vendor/build directories.
2. Read manifests/configs first, then representative source entry points.
3. Create a documentation plan: root README plus local READMEs where they will reduce future navigation cost.
4. Write docs in dependency order: root overview first, then package/app/dense-folder docs.

**Incremental update** when docs already exist:

1. Find the latest commit touching docs:
   ```bash
   git log -1 --format=%H -- README.md '**/README.md' docs
   ```
2. Diff code since that commit:
   ```bash
   git diff --name-status <doc_commit>..HEAD -- .
   git status --porcelain
   ```
3. Map changed files to owning docs by nearest ancestor `README.md`, package/app boundaries, or root README.
4. Read only changed files plus nearby manifests/tests/public entry points needed to understand impact.
5. Patch affected docs and leave unrelated sections untouched.

If there is no prior documentation commit, treat the task as initial documentation.

### 3. Choose README locations

Always consider:

- Root `README.md` for repository-level orientation.
- `apps/*/README.md` for deployable applications.
- `packages/*/README.md`, `libs/*/README.md`, or `modules/*/README.md` for reusable packages.
- `services/*/README.md` for service boundaries, APIs, jobs, queues, integrations.
- Database/schema/migration folders when data model rules are critical.
- Dense folders with many source files, public APIs, routing trees, or non-obvious conventions.

Do not create README files in trivial folders where names and local code are self-explanatory.

### 4. Write for agentic use

Each README should answer:

- What this area is responsible for.
- Where the important entry points are.
- How data/control flows through it.
- Which commands validate or operate on it.
- What conventions and invariants must be preserved.
- How to safely extend/change it.
- What related docs or sibling areas matter.

Use templates from `assets/readme-template.md` and `assets/folder-readme-template.md` when drafting new files. Read `references/doc-strategy.md` for detailed heuristics.

### 5. Validate

Before finishing:

1. Re-read changed docs for stale claims, broken relative links, and over-broad statements.
2. Ensure each README has a clear purpose and no duplicated boilerplate.
3. Check that every documented command, path, and package name exists.
4. If code files changed while documenting, run the repository validators requested by the user or required by the project.
5. Summarize which docs were created/updated and which code changes drove the updates.

## Gotchas

- README hierarchy is a navigation system, not a dumping ground. Split when a local README prevents repeated deep code searches.
- In monorepos, root docs should explain the map and shared workflows; package/app docs should explain local behavior.
- Generated files, lockfiles, build outputs, vendored dependencies, and migrations may be change signals but are rarely the primary explanation source.
- If docs and code disagree, trust code and update docs to match.
- If the user asks for documentation for humans/end users instead of AI agents, adapt the audience but keep the same inventory and validation discipline.
