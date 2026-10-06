# Output Template: Internals Mode

Use this template when `mode: internals`. Answers one question: **"How does it work inside, and why does it behave the way it does?"** Mental model, design decisions, and the failure modes they cause.

## Template Structure

```markdown
# {Topic} - Internals

## Mental Model
{2-4 sentences: the one picture an expert keeps in mind}

## Architecture
{Main components and how they connect. Required diagram with 3+ components — see visuals.md}

| Component | Responsibility |
|-----------|----------------|
| {component} | {responsibility} |

## Execution Flow
{Required diagram of this path — see visuals.md}

1. **{Step 1}**: {what happens, cause → effect}
2. **{Step 2}**: {what happens}
3. **{Step 3}**: {what happens}

## Design Decisions & Trade-offs

### {Decision 1}
- **Chosen:** {what the authors chose}
- **Cost:** {what it gives up}
- **Effect on users:** {observable behavior}

{2-4 decisions}

## Pitfalls and Their Causes
1. **{Pitfall}**: {symptom} → **Cause:** {internal mechanism behind it} → **Avoid by:** {fix}
2. ...
3. ...

## Performance
- {cost model: what is expensive, what is cheap, and why}
- {memory / latency / bundle considerations where relevant}

## Next Steps
- Apply it in code: `/jk:learn usage {topic}`
- Go deeper: {official architecture doc, RFC, or source file path}
```

## Section Guidelines

- **Visuals**: follow `visuals.md` (architecture, execution flow, plus state or data model diagrams when relevant).
- **Explain why, not just what**: tie every mechanism to a design decision or a constraint.
- **Execution flow**: 3-8 steps, each cause → effect, along the most important path (a request, a render, a handshake).
- **Pitfalls**: at least 3, each traced back to a mechanism above. A pitfall without a cause belongs in `cheatsheet`.
- **Sources**: internals claims must come from official docs, specs, or source code. Label anything inferred as inference.

## Not in This Mode

- No setup or tutorial code → `usage` (small snippets that demonstrate a mechanism are fine)
- No comparison with alternatives → `overview`
