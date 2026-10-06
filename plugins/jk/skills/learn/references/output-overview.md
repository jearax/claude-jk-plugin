# Output Template: Overview Mode

Use this template when `mode: overview` (default). Answers one question: **"What is it, and should I use it?"** Decision-focused, short, no code.

## Template Structure

```markdown
# {Topic} - Overview

## TL;DR
- **What**: {1-line definition}
- **Problem it solves**: {1-2 lines on the core problem}
- **Best fit**: {1 line on best-fit scenarios}

## Core Concepts
{Optional context map: where the topic sits — see visuals.md}

- **{Concept 1}**: {1-line meaning}
- **{Concept 2}**: {1-line meaning}
- **{Concept 3}**: {1-line meaning}

## When to Use / When Not to Use

### Use {Topic} when:
- {situation 1}
- {situation 2}
- {situation 3}

### Consider alternatives when:
- {situation 1}
- {situation 2}

## Comparison with Alternatives
| Criterion | {Topic} | {Alt 1} | {Alt 2} | {Alt 3} |
|-----------|---------|---------|---------|---------|
| {Criterion 1} | ... | ... | ... | ... |
| Learning curve | ... | ... | ... | ... |
| Community / maturity | ... | ... | ... | ... |

**Choose {Topic} when:** {1-2 bullet points}
**Choose an alternative when:** {brief guidance}

## Next Steps
- How to use it: `/jk:learn usage {topic}`
- How it works inside: `/jk:learn internals {topic}`
- What to read in the official docs: `/jk:learn docs {topic}`
```

## Section Guidelines

- **TL;DR**: scannable in 10 seconds.
- **Visuals**: follow `visuals.md`; the comparison table is the primary visual.
- **Core concepts**: 3-5 names the reader will meet everywhere in the docs. Name and one-line meaning only; how they work belongs to `internals`.
- **When to use / not**: a decision matrix. Each bullet is a concrete situation, not a generic quality ("fast", "easy").
- **Comparison**: at least 3 alternatives. Criteria must fit the topic: bundle size for a frontend library, latency or guarantees for a protocol, and so on.

## Not in This Mode

- No code, install command, or API → `usage` / `cheatsheet`
- No architecture or internal mechanics → `internals`
