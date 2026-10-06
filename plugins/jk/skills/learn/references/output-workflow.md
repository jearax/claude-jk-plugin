# Output Template: Workflow Mode

Use this template when `mode: workflow`. Answers one question: **"How do I get one real task done with it, end to end?"** One task, ordered steps, from an empty project to a verified result.

The topic usually names the task (`workflow auth with better-auth`). When it names only the technology (`workflow prisma`), pick the most common end-to-end task for it and state that choice in the Goal section.

## Template Structure

```markdown
# {Task} with {Topic} - Workflow

## Goal
- **Result**: {what exists and works at the end}
- **Assumes**: {starting point: stack, versions, accounts or keys needed}
- **Steps**: {N} steps, ~{time estimate}

## Flow
{Required: the steps below as a flow with check/decision nodes — see visuals.md}

## Step 1: {Action}
{1-2 lines: what this step achieves and why it comes now}
```{lang}
{code or command}
```
> **Check:** {how to confirm this step worked: command output, page, log line}

## Step 2: {Action}
{same structure}

{3-8 steps in total}

## Verify the Whole Flow
{End-to-end check: the request, test, or manual action that proves the task is done}

{Required when data moves between 2+ parties: the data flow of the finished system — see visuals.md}

## Common Failures
| Symptom | Step | Fix |
|---------|------|-----|
| {error or wrong behavior} | {step number} | {fix} |

## Next Steps
- Variations of this task: {related tasks, e.g. add OAuth after email login}
- Individual features used here: `/jk:learn usage {topic}`
```

## Section Guidelines

- **One task only**: every step moves toward the stated result. Side features go to "Next Steps".
- **Order matters**: each step depends only on earlier steps. Files and commands appear in the order the reader creates and runs them.
- **Every step is checkable**: a "Check" line, written as a blockquote, tells the reader how to know the step worked before moving on.
- **Visuals**: follow `visuals.md` (step flow required; data flow required when data crosses parties).
- **Complete, not minimal**: include the glue that isolated examples skip (env vars, config files, wiring between parts).
- **Current**: commands and APIs match the official docs for the stated versions.

## Not in This Mode

- No catalog of unrelated use cases → `usage`
- No comparison with alternatives → `overview`
- No explanation of internal mechanics → `internals`
