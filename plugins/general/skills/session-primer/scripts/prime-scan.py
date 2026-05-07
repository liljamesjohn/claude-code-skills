#!/usr/bin/env python3
"""Compact repository scan for priming an agentic coding session."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

EXCLUDED_DIRS = {
    ".git",
    ".agents",
    ".claude",
    ".cursor",
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
}

MANIFESTS = {
    "package.json",
    "pnpm-workspace.yaml",
    "bun.lock",
    "bun.lockb",
    "yarn.lock",
    "package-lock.json",
    "pyproject.toml",
    "requirements.txt",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
    "Gemfile",
    "deno.json",
    "deno.jsonc",
    "turbo.json",
    "nx.json",
    "Makefile",
    "Justfile",
    "Taskfile.yml",
    "Dockerfile",
    "docker-compose.yml",
}

DOC_NAMES = {
    "README.md",
    "README.mdx",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "docs/README.md",
    ".github/copilot-instructions.md",
}

ENTRY_NAMES = {
    "main.py",
    "__main__.py",
    "main.go",
    "main.rs",
    "index.ts",
    "index.tsx",
    "index.js",
    "server.ts",
    "server.js",
    "app.ts",
    "app.tsx",
    "app.js",
    "middleware.ts",
    "next.config.ts",
    "next.config.js",
}

SOURCE_EXTS = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".py",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".rb",
    ".php",
    ".cs",
    ".sql",
}


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except FileNotFoundError:
        return 127, ""
    return proc.returncode, proc.stdout.strip()


def git(root: Path, *args: str) -> str:
    code, out = run(["git", *args], root)
    return out if code == 0 else ""


def repo_root(path: Path) -> Path:
    code, out = run(["git", "rev-parse", "--show-toplevel"], path)
    return Path(out) if code == 0 and out else path.resolve()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def iter_files(root: Path, max_files: int) -> list[Path]:
    files: list[Path] = []
    for current_root, dirs, names in os.walk(root):
        current = Path(current_root)
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        for name in sorted(names):
            path = current / name
            try:
                parts = path.relative_to(root).parts
            except ValueError:
                continue
            if any(part in EXCLUDED_DIRS for part in parts):
                continue
            files.append(path)
            if len(files) >= max_files:
                return files
    return files


def package_scripts(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return {}
    return {str(k): str(v) for k, v in scripts.items()}


def default_branch(root: Path) -> str:
    symbolic = git(root, "symbolic-ref", "refs/remotes/origin/HEAD")
    if symbolic.startswith("refs/remotes/origin/"):
        return symbolic.removeprefix("refs/remotes/origin/")
    for candidate in ("main", "master", "staging"):
        if git(root, "rev-parse", "--verify", f"origin/{candidate}"):
            return candidate
    return ""


def changed_against_default(root: Path, default: str, limit: int) -> list[str]:
    if not default:
        return []
    base = git(root, "merge-base", "HEAD", f"origin/{default}")
    if not base:
        return []
    out = git(root, "diff", "--name-only", f"{base}..HEAD", "--", ".")
    return [line for line in out.splitlines() if line][:limit]


def inventory(root: Path, max_files: int) -> dict[str, Any]:
    files = iter_files(root, max_files)
    manifests: list[str] = []
    docs: list[str] = []
    entries: list[str] = []
    package_commands: dict[str, list[str]] = {}
    top_dirs: Counter[str] = Counter()
    source_dirs: Counter[str] = Counter()
    extensions: Counter[str] = Counter()

    for path in files:
        relative = rel(path, root)
        parts = Path(relative).parts
        if parts:
            top_dirs[parts[0]] += 1
        if path.suffix:
            extensions[path.suffix.lower()] += 1
        if path.name in MANIFESTS:
            manifests.append(relative)
        if relative in DOC_NAMES or path.name.lower() in {"readme.md", "readme.mdx"}:
            docs.append(relative)
        if path.name in ENTRY_NAMES or relative.startswith(("src/app/", "app/", "pages/", "routes/")):
            entries.append(relative)
        if path.suffix.lower() in SOURCE_EXTS and parts:
            source_dirs["/".join(parts[: min(2, len(parts))])] += 1
        if path.name == "package.json":
            scripts = package_scripts(path)
            if scripts:
                package_commands[relative] = list(scripts)[:16]

    return {
        "file_count_sampled": len(files),
        "manifests": sorted(manifests)[:40],
        "docs": sorted(docs)[:40],
        "entry_points": sorted(entries)[:40],
        "package_commands": package_commands,
        "top_dirs": top_dirs.most_common(20),
        "source_dirs": source_dirs.most_common(20),
        "extensions": extensions.most_common(12),
    }


def git_state(root: Path, change_limit: int) -> dict[str, Any]:
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    default = default_branch(root)
    status = [line for line in git(root, "status", "--porcelain").splitlines() if line]
    commits = [line for line in git(root, "log", "--oneline", "-10").splitlines() if line]
    changed = changed_against_default(root, default, change_limit)
    status_paths = [line[3:] for line in status if len(line) > 3]
    clusters = Counter(Path(path).parts[0] if Path(path).parts else path for path in changed + status_paths)
    return {
        "branch": branch,
        "default_branch": default,
        "dirty": bool(status),
        "status": status[:change_limit],
        "recent_commits": commits,
        "changed_against_default": changed,
        "change_clusters": clusters.most_common(12),
    }


def recommend_reads(inv: dict[str, Any], state: dict[str, Any]) -> list[str]:
    reads: list[str] = []
    for path in inv["docs"]:
        if path in DOC_NAMES or path.endswith("/README.md") or path.endswith("/README.mdx"):
            reads.append(path)
    reads.extend(inv["manifests"][:8])
    for path in state["changed_against_default"][:8]:
        if path not in reads:
            reads.append(path)
    reads.extend(path for path in inv["entry_points"][:8] if path not in reads)
    return reads[:20]


def scan(repo: Path, max_files: int, change_limit: int) -> dict[str, Any]:
    root = repo_root(repo)
    inv = inventory(root, max_files)
    state = git_state(root, change_limit)
    return {
        "root": str(root),
        "git": state,
        "inventory": inv,
        "recommended_reads": recommend_reads(inv, state),
    }


def md_list(items: list[Any], formatter=lambda x: str(x)) -> list[str]:
    return [f"- {formatter(item)}" for item in items] if items else ["- None detected"]


def to_markdown(data: dict[str, Any]) -> str:
    git_data = data["git"]
    inv = data["inventory"]
    lines = [
        "## Primer scan",
        "",
        f"- Root: `{data['root']}`",
        f"- Branch: `{git_data['branch'] or 'unknown'}`",
        f"- Default branch: `{git_data['default_branch'] or 'unknown'}`",
        f"- Working tree: `{'dirty' if git_data['dirty'] else 'clean'}`",
        "",
        "### Top directories",
        *md_list(inv["top_dirs"], lambda item: f"`{item[0]}` ({item[1]} files)"),
        "",
        "### Manifests",
        *md_list(inv["manifests"], lambda item: f"`{item}`"),
        "",
        "### Documentation",
        *md_list(inv["docs"], lambda item: f"`{item}`"),
        "",
        "### Entry points",
        *md_list(inv["entry_points"][:20], lambda item: f"`{item}`"),
        "",
        "### Package commands",
    ]
    if inv["package_commands"]:
        for manifest, commands in inv["package_commands"].items():
            lines.append(f"- `{manifest}`: {', '.join(f'`{cmd}`' for cmd in commands)}")
    else:
        lines.append("- None detected")

    lines.extend(["", "### Recent commits"])
    lines.extend(md_list(git_data["recent_commits"], lambda item: f"`{item}`"))
    lines.extend(["", "### Changed areas"])
    lines.extend(md_list(git_data["change_clusters"], lambda item: f"`{item[0]}` ({item[1]})"))
    lines.extend(["", "### Recommended first reads"])
    lines.extend(md_list(data["recommended_reads"], lambda item: f"`{item}`"))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Produce a compact repository scan for session priming."
    )
    parser.add_argument("--repo", default=".", help="Repository or subdirectory to inspect")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--max-files", type=int, default=8000)
    parser.add_argument("--change-limit", type=int, default=25)
    args = parser.parse_args()

    data = scan(Path(args.repo).expanduser().resolve(), args.max_files, args.change_limit)
    if args.format == "json":
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(to_markdown(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
