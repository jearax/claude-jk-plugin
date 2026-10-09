---
name: jk:prune-comments
description: "Remove junk code comments and tighten the valuable ones without touching code. Works on pending git changes (untracked files included) or the whole tree with --full, behind a temporary checkpoint commit so every run ends with accept or reject. Use when the user says 'prune comments', 'clean up AI comments', 'remove junk comments', 'dọn comment rác', 'xoá comment thừa', 'tinh gọn comment', or wants AI-generated comment noise removed before committing. Not for writing new docs or refactoring code."
argument-hint: "[instructions] [--full] [--junk \"<criteria>\"] [--keep \"<criteria>\"]"
allowed-tools: Read Edit Glob Grep Bash AskUserQuestion
license: MIT
metadata:
  author: jjuidev
  version: "1.0.0"
---

# /jk:prune-comments: Prune junk comments

Delete comments that carry no information, tighten the ones that do, and leave every byte of code alone. The reader is the next engineer opening the file: what survives should explain why, a constraint, or a non-obvious behavior, in as few lines as the facts need.

## Outcome

In-scope files contain only comment changes: junk deleted, kept comments tightened. The user has seen a per-comment summary and chosen **Accept** or **Reject**, and the git state matches that choice.

## Authority

- Edit comment text inside in-scope files. Never edit code, identifiers, imports, string literals, formatting, or whitespace outside comments. Never create, rename, or delete files.
- Run `scripts/git-checkpoint.py`. It is the only git writer: it creates and removes a temporary checkpoint commit and restores the index. Do not run other git commands that write (commit, reset, stash, checkout, restore) yourself.
- Ask the user via AskUserQuestion when there are no pending changes and before the final accept/reject.

## Arguments

| Input | Meaning |
|---|---|
| free text | Task instructions: which paths or file types to include or skip, what to focus on. Narrows the scope the script returns; never widens it. |
| `--full` | Scope = every tracked and untracked file instead of pending changes. |
| `--junk "<criteria>"` | Extra junk definition for this run (tier 1). Repeatable. |
| `--keep "<criteria>"` | Extra keep definition for this run (tier 1). Repeatable. |

## Workflow

Run the script with an absolute path inside this skill's directory; any `python3` works (stdlib only). Every subcommand prints JSON.

```bash
CP="<skill-base-dir>/scripts/git-checkpoint.py"
python3 "$CP" status
```

1. **Recover.** `status` → if `pending` is true, a previous run did not finish. Show its scope and ask Accept/Reject for that run first (`accept` / `reject`). For `orphan: true`, relay the hint and stop.
2. **Checkpoint.** `python3 "$CP" begin` (add `--full` when passed). Exit 2 `no-changes` → ask the user: scan the whole tree (`--full`), or stop. Exit 1 → report `error` and `hint`, stop. On success keep `ckpt` and `scope`.
3. **Scope.** Apply the free-text instructions to `scope`. Scope is empty → run `reject` (restores nothing, drops the checkpoint) and report that nothing matched.
4. **Decide and edit.** For each file: read it, classify every comment with the tier flow below, apply deletions and tightening with Edit. When deleting a whole-line comment, delete its line; when deleting a trailing comment, remove only the comment and the whitespace before it.
5. **Verify.** `git diff <ckpt> -- <scope files>`. Every hunk must touch comment text only. Revert any hunk that changes code by editing it back to the checkpoint content, then re-check. When the project has an obvious fast check (for example `npm run lint`, `tsc --noEmit`, `go vet`), run it and report the result.
6. **Summarize.** Table: `file:line`, action (`deleted` / `tightened`), before → after (shortened), deciding tier (`T0⚠`, `T1`, `T2`, `T3`). Then totals per action and tier, plus any check output.
7. **Decide.** AskUserQuestion: **Accept** (keep edits; they become unstaged changes, the original staging is restored) or **Reject** (restore every in-scope file). Run `accept` or `reject` and report its JSON result.

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
- **Collateral code edits** while removing a trailing comment or re-indenting. Step 5 catches them, so run it on every file before the summary.
- **Translating comments.** Keep each comment in its original language.
- **Running git yourself.** A manual `git reset` or `git commit` breaks the checkpoint guard and can lose the user's staging.

## Done when

- `git diff <ckpt>` shows comment-only hunks within scope.
- The summary table and totals were shown.
- The user chose Accept or Reject, the matching subcommand returned exit 0, and `status` reports `pending: false`.
