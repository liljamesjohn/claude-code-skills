#!/usr/bin/env python3
"""Inventory a codebase and summarize documentation update signals."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".nuxt",
    ".turbo",
    ".cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    "target",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

MANIFEST_NAMES = {
    "package.json",
    "pnpm-workspace.yaml",
    "bun.lock",
    "bun.lockb",
    "yarn.lock",
    "package-lock.json",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "poetry.lock",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
    "Gemfile",
    "mix.exs",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "composer.json",
    "deno.json",
    "deno.jsonc",
    "turbo.json",
    "nx.json",
    "lerna.json",
    "workspace.json",
    "Makefile",
    "Justfile",
    "Taskfile.yml",
    "Dockerfile",
    "docker-compose.yml",
}

SOURCE_EXTS = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".py",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".kts",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".scala",
    ".clj",
    ".ex",
    ".exs",
    ".erl",
    ".hrl",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".sql",
}

DOC_EXTS = {".md", ".mdx", ".rst", ".adoc"}
README_NAMES = {"readme.md", "readme.mdx"}


def run_git(repo: Path, args: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=repo,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        return 127, "", "git not found"
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git_root(path: Path) -> Path:
    code, out, _ = run_git(path, ["rev-parse", "--show-toplevel"])
    if code == 0 and out:
        return Path(out)
    return path.resolve()


def is_excluded(path: Path, root: Path) -> bool:
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in EXCLUDED_DIRS for part in rel_parts)


def iter_files(root: Path, max_files: int) -> list[Path]:
    files: list[Path] = []
    for current_root, dirs, names in os.walk(root):
        current = Path(current_root)
        dirs[:] = sorted(
            d for d in dirs if d not in EXCLUDED_DIRS and not is_excluded(current / d, root)
        )
        for name in sorted(names):
            path = current / name
            if is_excluded(path, root):
                continue
            files.append(path)
            if len(files) >= max_files:
                return files
    return files


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def latest_doc_commit(root: Path, doc_paths: list[str]) -> str | None:
    if not doc_paths:
        return None
    code, out, _ = run_git(root, ["log", "-1", "--format=%H", "--", *doc_paths])
    return out if code == 0 and out else None


def parse_name_status(output: str) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            changes.append({"status": status, "path": parts[2], "from": parts[1]})
        elif len(parts) >= 2:
            changes.append({"status": status, "path": parts[1]})
    return changes


def changed_since_doc_update(root: Path, doc_commit: str | None) -> dict[str, Any]:
    committed: list[dict[str, str]] = []
    if doc_commit:
        code, out, _ = run_git(root, ["diff", "--name-status", f"{doc_commit}..HEAD", "--", "."])
        if code == 0:
            committed = parse_name_status(out)

    code, out, _ = run_git(root, ["status", "--porcelain"])
    uncommitted = []
    if code == 0 and out:
        for line in out.splitlines():
            if len(line) > 3:
                uncommitted.append({"status": line[:2].strip() or "?", "path": line[3:]})

    return {"doc_commit": doc_commit, "committed": committed, "uncommitted": uncommitted}


def classify_doc_targets(changes: list[dict[str, str]], readmes: list[str]) -> dict[str, list[str]]:
    readme_dirs = sorted((str(Path(path).parent) for path in readmes), key=len, reverse=True)
    targets: dict[str, list[str]] = defaultdict(list)

    for change in changes:
        changed_path = change["path"]
        parts = Path(changed_path).parts
        target = "README.md"
        for readme_dir in readme_dirs:
            if readme_dir == ".":
                continue
            if changed_path == readme_dir or changed_path.startswith(f"{readme_dir}/"):
                target = f"{readme_dir}/README.md"
                break
        if len(parts) >= 2 and parts[0] in {"apps", "packages", "services", "libs", "crates"}:
            candidate = f"{parts[0]}/{parts[1]}/README.md"
            if candidate in readmes or target == "README.md":
                target = candidate
        targets[target].append(changed_path)

    return dict(sorted(targets.items()))


def inventory(root: Path, max_files: int) -> dict[str, Any]:
    files = iter_files(root, max_files)
    manifests: list[str] = []
    readmes: list[str] = []
    doc_files: list[str] = []
    ext_counts: Counter[str] = Counter()
    source_counts: dict[str, int] = defaultdict(int)

    for path in files:
        relative = rel(path, root)
        lower_name = path.name.lower()
        suffix = path.suffix.lower()

        if path.name in MANIFEST_NAMES:
            manifests.append(relative)
        if lower_name in README_NAMES:
            readmes.append(relative)
        if suffix in DOC_EXTS:
            doc_files.append(relative)
        if suffix:
            ext_counts[suffix] += 1
        if suffix in SOURCE_EXTS:
            parts = Path(relative).parts
            if len(parts) >= 2:
                source_counts["/".join(parts[:2])] += 1
            if len(parts) >= 3:
                source_counts["/".join(parts[:3])] += 1

    dense_dirs = [
        {"path": path, "source_files": count}
        for path, count in sorted(source_counts.items())
        if count >= 20 and f"{path}/README.md" not in readmes
    ]

    return {
        "root": str(root),
        "file_count_sampled": len(files),
        "manifests": sorted(manifests),
        "readmes": sorted(readmes),
        "doc_files": sorted(doc_files),
        "top_extensions": ext_counts.most_common(20),
        "dense_dirs_without_readme": dense_dirs[:30],
    }


def to_markdown(data: dict[str, Any]) -> str:
    inv = data["inventory"]
    changes = data["changes"]
    lines = [
        f"# Repo map: `{inv['root']}`",
        "",
        f"- Files sampled: {inv['file_count_sampled']}",
        f"- Latest documentation commit: `{changes['doc_commit'] or 'not found'}`",
        "",
        "## Manifests",
        *[f"- `{path}`" for path in inv["manifests"][:80]],
        "",
        "## README files",
        *[f"- `{path}`" for path in inv["readmes"][:80]],
        "",
        "## Dense directories without README",
    ]

    if inv["dense_dirs_without_readme"]:
        lines.extend(
            f"- `{item['path']}` ({item['source_files']} source files)"
            for item in inv["dense_dirs_without_readme"]
        )
    else:
        lines.append("- None detected")

    lines.extend(["", "## Changes since documentation update"])
    all_changes = changes["committed"] + changes["uncommitted"]
    if all_changes:
        for item in all_changes[:200]:
            lines.append(f"- `{item['status']}` `{item['path']}`")
    else:
        lines.append("- No committed or uncommitted changes detected")

    lines.extend(["", "## Suggested documentation targets"])
    targets = data["doc_targets"]
    if targets:
        for target, paths in targets.items():
            preview = ", ".join(f"`{path}`" for path in paths[:8])
            suffix = " ..." if len(paths) > 8 else ""
            lines.append(f"- `{target}` ← {preview}{suffix}")
    else:
        lines.append("- No change-driven targets detected")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository or subdirectory to inspect")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--since-doc-update", action="store_true")
    parser.add_argument("--max-files", type=int, default=10_000)
    args = parser.parse_args()

    root = git_root(Path(args.repo).expanduser().resolve())
    inv = inventory(root, args.max_files)
    doc_commit = latest_doc_commit(root, inv["doc_files"]) if args.since_doc_update else None
    changes = changed_since_doc_update(root, doc_commit) if args.since_doc_update else {
        "doc_commit": None,
        "committed": [],
        "uncommitted": [],
    }
    all_changes = changes["committed"] + changes["uncommitted"]
    data = {
        "inventory": inv,
        "changes": changes,
        "doc_targets": classify_doc_targets(all_changes, inv["readmes"]),
    }

    if args.format == "markdown":
        print(to_markdown(data))
    else:
        print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
