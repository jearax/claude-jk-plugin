#!/usr/bin/env python3
"""List the pending git changes jk:prune-comments may edit. Read-only: never writes to git.

Usage:
  list-changed-files.py

Scope = staged, unstaged, and untracked files, minus deleted, ignored, symlinked, generated, and binary files.
Prints one JSON object. Exit 0 = ok, 1 = not a git repo, 2 = no pending changes.
Stdlib only.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prune_rules import Rules  # noqa: E402


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def _paths(cwd, *args):
    return [p for p in _git(cwd, *args, "-z").split("\0") if p]


def changed_files(top):
    try:
        _git(top, "rev-parse", "--verify", "-q", "HEAD")
        tracked = _paths(top, "diff", "--name-only", "--no-renames", "--diff-filter=d", "HEAD")
    except subprocess.CalledProcessError:
        tracked = _paths(top, "ls-files")
    untracked = _paths(top, "ls-files", "--others", "--exclude-standard")
    return sorted(set(tracked) | set(untracked))


def filter_scope(top, candidates, rules=None):
    rules = rules or Rules()
    scope = []
    for path in candidates:
        abs_path = os.path.join(top, path)
        if rules.is_ignored(path) or os.path.islink(abs_path) or not os.path.isfile(abs_path):
            continue
        try:
            with open(abs_path, "rb") as fh:
                if rules.is_generated_or_binary(fh.read(8192)):
                    continue
        except OSError:
            continue
        scope.append(path)
    return scope


def run(cwd=None):
    try:
        top = _git(cwd or os.getcwd(), "rev-parse", "--show-toplevel").strip()
    except (subprocess.CalledProcessError, OSError):
        return 1, {"error": "not-a-repo", "hint": "Run inside a git repository."}
    candidates = changed_files(top)
    if not candidates:
        return 2, {"error": "no-changes", "hint": "No pending git changes; nothing to prune."}
    scope = filter_scope(top, candidates)
    return 0, {"root": top, "scope": scope, "skipped": len(candidates) - len(scope)}


def main():
    code, payload = run()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(code)


if __name__ == "__main__":
    main()
