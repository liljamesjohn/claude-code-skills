#!/usr/bin/env python3
"""Read-only Git safety scan for atomic commit planning."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROTECTED_EXACT = {"main", "master", "develop"}
PROTECTED_PATTERNS = ("release/*",)
RISKY_PATTERNS = (
    ".env",
    ".env.*",
    "*.env",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.crt",
    "*.cer",
    "*.der",
    "*credential*",
    "*secret*",
    "*token*",
    "node_modules/*",
    "vendor/*",
    ".venv/*",
    "venv/*",
    "dist/*",
    "build/*",
    ".next/*",
    ".nuxt/*",
    "coverage/*",
    "target/*",
    "*.log",
    "*.zip",
    "*.tar",
    "*.tgz",
    "*.gz",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.webp",
    "*.mp4",
    "*.mov",
    "*.pdf",
)


def run(repo: Path, args: list[str]) -> tuple[int, str, str]:
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


def git(repo: Path, *args: str) -> str:
    code, out, _ = run(repo, list(args))
    return out if code == 0 else ""


def repo_root(path: Path) -> tuple[Path | None, str | None]:
    code, out, err = run(path, ["rev-parse", "--show-toplevel"])
    if code != 0 or not out:
        return None, err or "not a git repository"
    return Path(out), None


def is_protected(branch: str) -> bool:
    return branch in PROTECTED_EXACT or any(
        fnmatch.fnmatch(branch, pattern) for pattern in PROTECTED_PATTERNS
    )


def parse_status(lines: list[str]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for line in lines:
        if not line:
            continue
        status = line[:2]
        path = line[3:] if len(line) > 3 else ""
        if " -> " in path:
            old, new = path.split(" -> ", 1)
            items.append({"status": status, "path": new, "from": old})
        else:
            items.append({"status": status, "path": path})
    return items


def upstream_status(repo: Path) -> dict[str, Any]:
    upstream = git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if not upstream:
        return {"upstream": None, "ahead": None, "behind": None}
    counts = git(repo, "rev-list", "--left-right", "--count", f"{upstream}...HEAD")
    if not counts:
        return {"upstream": upstream, "ahead": None, "behind": None}
    behind, ahead = counts.split()
    return {"upstream": upstream, "ahead": int(ahead), "behind": int(behind)}


def risky_paths(repo: Path, paths: list[str], large_limit: int) -> list[dict[str, Any]]:
    risky: list[dict[str, Any]] = []
    for path in sorted(set(paths)):
        normalized = path.strip()
        lower = normalized.lower()
        reasons = [
            pattern
            for pattern in RISKY_PATTERNS
            if fnmatch.fnmatch(lower, pattern.lower())
            or fnmatch.fnmatch(f"/{lower}", f"*/{pattern.lower()}")
        ]
        full_path = repo / normalized
        try:
            size = full_path.stat().st_size if full_path.is_file() else 0
        except OSError:
            size = 0
        if size >= large_limit:
            reasons.append(f"large-file>={large_limit}")
        if reasons:
            risky.append({"path": normalized, "reasons": sorted(set(reasons)), "size": size})
    return risky


def name_status(repo: Path) -> list[str]:
    out = git(repo, "diff", "--name-status", "--", ".")
    cached = git(repo, "diff", "--cached", "--name-status", "--", ".")
    return [line for line in [*out.splitlines(), *cached.splitlines()] if line]


def diff_stats(repo: Path) -> dict[str, str]:
    return {
        "unstaged": git(repo, "diff", "--stat", "--", "."),
        "staged": git(repo, "diff", "--cached", "--stat", "--", "."),
    }


def scan(repo_arg: Path, large_limit: int) -> dict[str, Any]:
    root, error = repo_root(repo_arg)
    if error or root is None:
        return {"ok": False, "blockers": [error], "repo": str(repo_arg)}

    detached = git(root, "symbolic-ref", "--quiet", "--short", "HEAD") == ""
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    status_lines = [line for line in git(root, "status", "--porcelain=v1", "-uall").splitlines() if line]
    status = parse_status(status_lines)
    conflicts = [line for line in git(root, "ls-files", "-u").splitlines() if line]
    paths = [item["path"] for item in status if item.get("path")]
    risky = risky_paths(root, paths, large_limit)
    clusters = Counter(Path(path).parts[0] if Path(path).parts else path for path in paths)

    blockers: list[str] = []
    if detached or branch == "HEAD":
        blockers.append("detached HEAD")
    if is_protected(branch):
        blockers.append(f"protected branch: {branch}")
    if conflicts:
        blockers.append("merge conflicts present")

    return {
        "ok": not blockers,
        "repo": str(root),
        "branch": branch,
        "protected_branch": is_protected(branch),
        "detached_head": detached or branch == "HEAD",
        "upstream": upstream_status(root),
        "dirty": bool(status),
        "status": status,
        "untracked": [item["path"] for item in status if item["status"] == "??"],
        "conflicts": conflicts[:50],
        "risky_paths": risky,
        "name_status": name_status(root),
        "diff_stats": diff_stats(root),
        "change_clusters": clusters.most_common(20),
        "blockers": blockers,
    }


def md_list(items: list[Any], formatter=lambda x: str(x)) -> list[str]:
    return [f"- {formatter(item)}" for item in items] if items else ["- None"]


def to_markdown(data: dict[str, Any]) -> str:
    if not data.get("ok") and "branch" not in data:
        return "\n".join(["## Git safety scan", "", "- OK: `false`", *md_list(data["blockers"])])

    lines = [
        "## Git safety scan",
        "",
        f"- Repo: `{data['repo']}`",
        f"- Branch: `{data['branch']}`",
        f"- OK to plan commits: `{'true' if data['ok'] else 'false'}`",
        f"- Dirty: `{'true' if data['dirty'] else 'false'}`",
        f"- Upstream: `{data['upstream']['upstream'] or 'none'}`",
        f"- Ahead/behind: `{data['upstream']['ahead']}/{data['upstream']['behind']}`",
        "",
        "### Blockers",
        *md_list(data["blockers"]),
        "",
        "### Change clusters",
        *md_list(data["change_clusters"], lambda item: f"`{item[0]}` ({item[1]})"),
        "",
        "### Status",
        *md_list(data["status"][:80], lambda item: f"`{item['status']}` `{item['path']}`"),
        "",
        "### Risky paths",
        *md_list(
            data["risky_paths"],
            lambda item: f"`{item['path']}` ({', '.join(item['reasons'])})",
        ),
        "",
        "### Name status",
        *md_list(data["name_status"][:80], lambda item: f"`{item}`"),
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only Git safety scan for atomic commit planning."
    )
    parser.add_argument("--repo", default=".", help="Repository or subdirectory to inspect")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--large-limit", type=int, default=5_000_000)
    args = parser.parse_args()

    data = scan(Path(args.repo).expanduser().resolve(), args.large_limit)
    if args.format == "json":
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(to_markdown(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
