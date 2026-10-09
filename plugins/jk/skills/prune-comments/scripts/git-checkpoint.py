#!/usr/bin/env python3
"""Checkpoint the working tree before jk:prune-comments edits, then accept or roll back.

Usage:
  git-checkpoint.py begin [--full]   snapshot state, print the file scope
  git-checkpoint.py accept           keep the edits, drop the checkpoint, restore the index
  git-checkpoint.py reject           restore in-scope files, drop the checkpoint, restore the index
  git-checkpoint.py status           report a pending or orphaned checkpoint

Prints one JSON object. Exit 0 = ok, 1 = guard failure, 2 = no pending changes.
Stdlib only. Requires git >= 2.26 (restore --pathspec-from-file).
"""
import datetime
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prune_rules import Rules  # noqa: E402

MARKER = "jk:prune-comments checkpoint"
STATE_NAME = "jk-prune-comments.json"
IN_PROGRESS = ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply")


class GuardError(Exception):
    def __init__(self, error, hint):
        super().__init__(error)
        self.payload = {"error": error, "hint": hint}


class Git:
    def __init__(self, cwd):
        try:
            top = self._run(cwd, "rev-parse", "--show-toplevel")
        except subprocess.CalledProcessError:
            raise GuardError("not-a-repo", "Run inside a git repository.")
        self.top = top.strip()

    @staticmethod
    def _run(cwd, *args, stdin=None):
        return subprocess.run(
            ["git", *args], cwd=cwd, input=stdin, capture_output=True, text=True, check=True
        ).stdout

    def __call__(self, *args, stdin=None):
        return self._run(self.top, *args, stdin=stdin)

    def ok(self, *args):
        try:
            self(*args)
            return True
        except subprocess.CalledProcessError:
            return False

    def paths(self, *args):
        return [p for p in self(*args, "-z").split("\0") if p]

    def git_path(self, name):
        return os.path.join(self.top, self("rev-parse", "--git-path", name).strip())

    def head(self):
        return self("rev-parse", "HEAD").strip()

    def commit_checkpoint(self):
        identity = []
        if not self.ok("config", "user.email"):
            identity = ["-c", "user.name=jk", "-c", "user.email=jk@local"]
        self(*identity, "-c", "commit.gpgsign=false", "commit", "--no-verify", "-q", "-m", MARKER)


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


def _load_state(git):
    path = git.git_path(STATE_NAME)
    if not os.path.exists(path):
        raise GuardError("no-checkpoint", "Nothing to accept or reject. Run `begin` first.")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh), path


def _guard_head(git, state):
    if state["mode"] == "commit" and git.head() != state["ckpt"]:
        raise GuardError(
            "head-moved",
            f"HEAD is no longer the checkpoint {state['ckpt'][:12]}. Nothing was changed. "
            f"Inspect `git log`, then recover manually with `git reset --soft {state['base'][:12]}` "
            f"and `git read-tree {state['idx'][:12]}` once the checkpoint is HEAD again.",
        )


def _drop_checkpoint(git, state, state_path):
    if state["mode"] == "commit":
        git("reset", "--soft", "-q", state["base"])
        git("read-tree", state["idx"])
    os.remove(state_path)


def cmd_begin(git, full):
    if not git.ok("rev-parse", "--verify", "-q", "HEAD"):
        raise GuardError("no-commits", "The repository has no commits yet; commit once first.")
    for name in IN_PROGRESS:
        if os.path.exists(git.git_path(name)):
            raise GuardError("operation-in-progress", f"Finish or abort the pending {name} first.")
    if os.path.exists(git.git_path(STATE_NAME)):
        raise GuardError("pending-checkpoint", "A previous run is still pending. Run `status`.")

    base = git.head()
    dirty = bool(git("status", "--porcelain").strip())
    if not dirty and not full:
        return 2, {"error": "no-changes", "hint": "No pending changes. Ask for paths or --full."}

    idx = git("write-tree").strip()
    if dirty:
        git("add", "-A")
        git.commit_checkpoint()
        mode = "commit"
    else:
        mode = "clean"
    ckpt = git.head()

    if full:
        candidates = git.paths("ls-files")
    else:
        candidates = git.paths("diff", "--name-only", "--no-renames", "--diff-filter=d", base, ckpt)
    scope = filter_scope(git.top, candidates)

    state = {
        "ckpt": ckpt, "idx": idx, "base": base, "mode": mode, "full": full, "scope": scope,
        "created": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    with open(git.git_path(STATE_NAME), "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    return 0, {
        "ckpt": ckpt, "mode": mode, "scope": scope, "skipped": len(candidates) - len(scope),
    }


def cmd_accept(git):
    state, state_path = _load_state(git)
    _guard_head(git, state)
    changed = git.paths("diff", "--name-only", state["ckpt"])
    _drop_checkpoint(git, state, state_path)
    return 0, {"accepted": changed}


def cmd_reject(git):
    state, state_path = _load_state(git)
    _guard_head(git, state)
    in_scope = set(state["scope"])
    changed = git.paths("diff", "--name-only", state["ckpt"])
    restore = [p for p in changed if p in in_scope]
    if restore:
        git(
            "restore", f"--source={state['ckpt']}", "--worktree",
            "--pathspec-from-file=-", "--pathspec-file-nul",
            stdin="\0".join(restore),
        )
    _drop_checkpoint(git, state, state_path)
    return 0, {"restored": restore, "outside_scope_untouched": [p for p in changed if p not in in_scope]}


def cmd_status(git):
    state_path = git.git_path(STATE_NAME)
    if os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as fh:
            state = json.load(fh)
        return 0, {"pending": True, "orphan": False, "state": state}
    if git.ok("rev-parse", "--verify", "-q", "HEAD") and git("log", "-1", "--format=%s").strip() == MARKER:
        return 0, {
            "pending": True, "orphan": True,
            "hint": "HEAD is a checkpoint commit without state. `git reset --soft HEAD~1` "
                    "removes it and keeps all changes, but the original staged/unstaged split is lost.",
        }
    return 0, {"pending": False}


def run(argv, cwd=None):
    if not argv or argv[0] not in {"begin", "accept", "reject", "status"}:
        return 1, {"error": "usage", "hint": "git-checkpoint.py begin [--full] | accept | reject | status"}
    try:
        git = Git(cwd or os.getcwd())
        if argv[0] == "begin":
            return cmd_begin(git, "--full" in argv[1:])
        return {"accept": cmd_accept, "reject": cmd_reject, "status": cmd_status}[argv[0]](git)
    except GuardError as exc:
        return 1, exc.payload
    except subprocess.CalledProcessError as exc:
        return 1, {"error": "git-failed", "hint": (exc.stderr or str(exc)).strip()}


def main():
    code, payload = run(sys.argv[1:])
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(code)


if __name__ == "__main__":
    main()
