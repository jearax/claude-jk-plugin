---
name: jk:herdr-kickoff
description: "Kick off a new task or project in Herdr: set the workspace label, ensure the four standard tabs (planner, cooker, dev-serve, git-check), and spawn agents in the two agent tabs. Reuses the current workspace by default; --new creates a separate one. Requires HERDR_ENV=1. Use when the user says 'kickoff', 'start a new task', 'new project', or asks to set up a Herdr workspace for new work. Not for prompting agents with work, running commands in panes, or inspecting Herdr state."
argument-hint: '<task-name> [--new [path]] [--fresh] [--no-agents] [--planner-exec <exec>] [--cooker-exec <exec>]'
license: MIT
metadata:
  author: jjuidev
  version: '1.0.0'
---

# /jk:herdr-kickoff: Kick off a task workspace in Herdr

One command replaces the manual ritual: workspace label, four standard tabs, and a live planner/cooker pair primed to work together — then the tab that issued the command closes itself. Reusing the current workspace is the default; `--new` scaffolds a separate one.

## Outcome

Workspace labeled with the task name, exactly the four standard tabs, both agent tabs hosting live named agents (unless `--no-agents`), planner primed, summary shown, then the caller tab closed. Nothing else touched.

## Guard

```bash
test "${HERDR_ENV:-}" = 1
```

On failure, say this skill only runs inside Herdr and stop. The installed `herdr` skill holds the CLI doctrine; the binary's `--help` is the syntax authority (verified against 0.9.5).

## Standard layout

| Tab       | Holds             | Agent     |
| --------- | ----------------- | --------- |
| planner   | agent pane        | `planner` |
| cooker    | agent pane        | `cooker`  |
| dev-serve | shell, left empty | none      |
| git-check | shell, left empty | none      |

## Arguments

| Input                                            | Meaning                                                                                                                                                                   |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<task-name>`                                    | Workspace label. Missing → ask once, never guess. A positional containing `/` or `~` is a workdir path instead and implies `--new`; when a name and a path both appear, the label is the name. |
| `--new [<value>]`                                | Separate workspace. The value is a project path when it contains `/` or starts with `~` — workdir = it, label = its basename (a positional name wins over the basename); otherwise a task/ticket name — workdir = `$PWD`, label = the value. Missing value → AskUserQuestion once. A missing folder is created with `mkdir -p`, never asked. Without `--new`: reuse, workdir is `$PWD`. |
| `--fresh`                                        | Reuse branch: close every tab except the caller's, then create all four. Ignored with `--new`.                                                                            |
| `--no-agents`                                    | Tabs only; skip spawning and priming.                                                                                                                                     |
| `--planner-exec <exec>` / `--cooker-exec <exec>` | Executables launched in the two agent tabs. Defaults `claude-planner` / `claude-cooker` (`.zshrc` aliases wrapping `claude --settings <profile>`).                        |

## Workflow

Parse every id from the JSON the commands print, never from memory. Batch the shell work: step 3 is one Bash call, step 4 is one Bash call.

1. **Guard.** Stop when it fails.
2. **Inputs.** Missing name → ask once. A positional containing `/` or `~` is a workdir path and implies `--new`; the value is then a project path (workdir = it, `mkdir -p` when missing, label = basename unless a name positional exists) or a task/ticket name (workdir = `$PWD`, label = it). `--new` with no value → ask once. Reuse: workdir is `$PWD`.
3. **Workspace + tabs, one pass.** The label lands first (rename or create) so a rejected name aborts before any tab mutation.
   - Reuse: `herdr workspace rename "$HERDR_WORKSPACE_ID" "<task-name>"`; ws stays `$HERDR_WORKSPACE_ID`.
   - `--new`: `herdr workspace create --cwd <workdir> --label "<task-name>" --no-focus`; ws and the initial tab id come from the JSON.
   - `herdr tab list --workspace <ws>`; create each missing standard tab with `herdr tab create --workspace <ws> --label <tab> --cwd <workdir> --no-focus`; the payload is pane-centric — pane = `.result.root_pane`, the new tab's `tab_id` rides on that nested pane object (no top-level tab key). For an existing tab take its pane from `herdr pane list --workspace <ws>` (`tab_id` match).
   - `--fresh`: close every tab but `$HERDR_TAB_ID` before creating. `--new`: close the initial tab after the four exist. Report what was closed.
4. **Spawn both agents, one pass.** Skip with `--no-agents`. Skip a tab already hosting a live agent (`herdr agent list`, `tab_id` match). Launch both panes back-to-back so they boot in parallel:

   ```bash
   herdr pane run <planner-pane> "<planner-exec>"; herdr pane run <cooker-pane> "<cooker-exec>"
   ```

   Detection is not instantaneous (plain execs: seconds; `--settings` wrappers: 60–90 s). Poll until both pane ids appear in `herdr agent list` — that JSON is the success signal:

   ```bash
   herdr agent list
   ```

   `herdr agent wait <pane> --timeout 20000` polls one pane, but judge it by its JSON payload, never its exit code — it can exit non-zero on a healthy agent. Let the think-time between turns pace the polls; a still-absent pane after ~2 minutes is a dead exec: report the exec name, leave that tab a plain shell. Name each detected agent after its role: `herdr agent rename <pane> planner` / `cooker`. Names are unique per workspace in 0.9.5, not server-wide; keep the `-2`, then `-3` retry only for a same-workspace clash, expected rare. Use the final names everywhere below.

5. **Prime the planner.** Skip with `--no-agents` or a dead planner. Read [`references/planner-prime.md`](references/planner-prime.md), substitute `<cooker-name>` with the live cooker name, and submit without `--wait`:

   ```bash
   herdr agent prompt planner "<primed-text>"
   ```

6. **Summarize.** Workspace line (id, label, branch, primed yes/no), `tab | id | status` (created / existing / closed), `agent | name | pane | state`.
7. **Close the caller tab — reuse branch only, the final command, nothing after it.** Without `--new`: `herdr tab close "$HERDR_TAB_ID"`, no confirmation — the calling tab was absorbed into the task workspace and is disposable ritual; when it was its workspace's only tab, also `herdr workspace close <that-ws>`. With `--new`: leave the caller tab alive — the kickoff lives in another workspace and this session keeps running.

## Failure modes

- **Self-kill timing:** mid-run `$HERDR_TAB_ID` is never closed (excluded from `--fresh` and the initial-tab cleanup); on the reuse branch the caller tab closes exactly once, as the final command, right after the summary; `--new` keeps it alive. The `--new` initial tab closes only after the four exist, so no zero-tab window.
- **Agent identity:** the live-agent check runs before every spawn (no stacking); names are unique per workspace in 0.9.5 — the `-2` fallback covers a same-workspace clash, expected rare.
- **Dead exec and lying exit codes:** `pane run` just types the command; a missing executable leaves `command not found` text and no agent, and `agent wait` can exit non-zero while returning healthy-state JSON. Only the `agent list` payload decides life or death; the ~2 minute cap turns a dead exec into a visible skip instead of a hang.
- **Focus and orphans:** every create uses `--no-focus`; reuse is the default so repeated kickoffs do not pile up abandoned workspaces.

## Done when

- Label equals the task name; exactly the four standard tabs (initial tab gone on `--new`; caller tab plus four on `--fresh`).
- Both agent tabs host live role-named agents, or `--no-agents` was set; planner primed when present.
- Summary shown; on the reuse branch the caller tab closed last (plus its workspace when that emptied), on `--new` it stayed alive; nothing else outside this workspace touched.
