---
name: jk:prune-comments
description: "Remove junk code comments and tighten the valuable ones without touching code. Works only on pending git changes (staged, unstaged, untracked) and applies the edits directly; stops when there are none. Use when the user says 'prune comments', 'clean up AI comments', 'remove junk comments', 'dọn comment rác', 'xoá comment thừa', 'tinh gọn comment', or wants AI-generated comment noise removed before committing. Not for writing new docs or refactoring code."
argument-hint: "[instructions] [--junk \"<criteria>\"] [--keep \"<criteria>\"]"
allowed-tools: Read Edit Glob Grep Bash
license: MIT
metadata:
  author: jjuidev
  version: "1.0.0"
---

# /jk:prune-comments: Prune junk comments

Delete comments that carry no information, tighten the ones that do, and leave every byte of code alone. The reader is the next engineer opening the file: what survives should explain why, a constraint, or a non-obvious behavior, in as few lines as the facts need.

## Outcome

Pending changed files contain only comment changes from this run: junk deleted, kept comments tightened, applied directly to the working tree. The user has seen a per-comment summary.

## Authority

- Edit comment text inside in-scope files. Never edit code, identifiers, imports, string literals, formatting, or whitespace outside comments. Never create, rename, or delete files.
- Run `scripts/list-changed-files.py` to get the scope. It is read-only. Never run git commands that write (add, commit, reset, stash, checkout, restore).
- Scope is pending git changes only. Never widen it to the whole tree or to files the user names outside the pending changes.

## Arguments

| Input | Meaning |
|---|---|
| free text | Task instructions: which paths or file types to include or skip, what to focus on. Narrows the scope the script returns; never widens it. |
| `--junk "<criteria>"` | Extra junk definition for this run (tier 1). Repeatable. |
| `--keep "<criteria>"` | Extra keep definition for this run (tier 1). Repeatable. |

## Workflow

Run the script with an absolute path inside this skill's directory; any `python3` works (stdlib only). It prints JSON.

```bash
python3 "<skill-base-dir>/scripts/list-changed-files.py"
```

1. **Scope.** Exit 1 `not-a-repo` or exit 2 `no-changes` → tell the user there are no pending git changes to prune and stop. On success apply the free-text instructions to `scope` (paths are relative to `root`). Scope empty → report that nothing matched and stop.
2. **Decide and edit.** For each file: read it, classify every comment with the tier flow below, apply deletions and tightening with Edit. When deleting a whole-line comment, delete its line; when deleting a trailing comment, remove only the comment and the whitespace before it.
3. **Verify.** Re-check every Edit: `old_string` and `new_string` may differ only in comment text and the line or whitespace a deletion removes. Fix any edit that touched code by editing it back. When the project has an obvious fast check (for example `npm run lint`, `tsc --noEmit`, `go vet`), run it and report the result.
4. **Summarize.** Table: `file:line`, action (`deleted` / `tightened`), before → after (shortened), deciding tier (`T0⚠`, `T1`, `T2`, `T3`). Then totals per action and tier, plus any check output. The edits stay applied as unstaged changes.

## Tier flow

Evaluate each comment top-down and stop at the first verdict. Within one tier, Keep beats Junk.

| Tier | Source | Keep verdict | Junk verdict |
|---|---|---|---|
| T0 | [`references/keep-list.md`](references/keep-list.md): tool directives, build pragmas, coverage, generated, doc contracts, legal | Keep untouched | Only when `--junk` names the pattern explicitly → delete, mark ⚠ |
| T1 | `--keep` / `--junk` of this run | Keep untouched | Delete |
| T2 | [`references/junk-catalog.md`](references/junk-catalog.md): the owner's definitions | Keep untouched | Delete |
| T3 | [`references/antislop.md`](references/antislop.md): baseline patterns | Keep, may tighten | Delete |
| none | No tier matched | Keep, may tighten | n/a |

Tighten only comments kept at T3 or matched by no tier, following [`references/tighten-rules.md`](references/tighten-rules.md). Read `junk-catalog.md` on every run: it is the owner's file and changes between runs. Empty template sections mean no T2 rules.

## Failure modes this skill guards against

- **Deleting a directive** (`@ts-expect-error`, `eslint-disable-next-line`, `//go:build`) breaks lint or the build. T0 runs first for that reason.
- **"Tightening" that changes meaning**, such as dropping a unit, a condition, or an issue link. When unsure, leave the comment as is.
- **Collateral code edits** while removing a trailing comment or re-indenting. Step 3 catches them, so run it on every file before the summary.
- **Translating comments.** Keep each comment in its original language.
- **Running git yourself.** A `git reset`, `stash`, or `checkout` can lose the user's pending work, which is exactly what this skill edits.

## Done when

- Every in-scope edit changes comment text only.
- The summary table and totals were shown.
- No git command that writes was run.
