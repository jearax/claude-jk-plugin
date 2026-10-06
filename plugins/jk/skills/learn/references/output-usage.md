# Output Template: Usage Mode

Use this template when `mode: usage`. Answers one question: **"How do I use it?"** Hands-on and code-first, from setup to the patterns real projects use.

## Template Structure

```markdown
# {Topic} - Usage Guide

## Setup
```{lang}
{install + minimal working setup, copy-paste ready}
```

## Common Use Cases

### 1. {Most common use case}
**When:** {scenario}
```{lang}
{runnable code example}
```
**Why this works:** {1-2 lines on the approach}

### 2. {Use case}
{same structure}

### 3. {Use case}
{same structure}

## Common Patterns

### {Pattern name}
**Solves:** {problem this pattern solves}
```{lang}
{code}
```

{1-3 patterns, from common to advanced}

## Less Common but Useful
**When:** {rare but useful scenario}
```{lang}
{example}
```

## Next Steps
- Quick API lookup: `/jk:learn cheatsheet {topic}`
- Build a complete task: `/jk:learn workflow {task} with {topic}`
- How it works inside: `/jk:learn internals {topic}`
```

## Section Guidelines

- **Setup**: the smallest setup that runs. State versions when the API differs between major releases.
- **Use cases**: 3, ordered by how often real projects need them. Each has "When" + runnable code + "Why this works".
- **Patterns**: idioms that combine features (composition, error handling, testing). Skip the section if the topic has none.
- **Less common**: 1, optional; include it only when it would surprise an experienced user.
- **Code**: runnable and current per the official docs. Comments explain intent, not syntax.
- **Visuals**: follow `visuals.md`; add a diagram only when a use case crosses parties.

## Not in This Mode

- No comparison with alternatives → `overview`
- No architecture or why-it-works explanation → `internals`
- No exhaustive API table → `cheatsheet`
- No full end-to-end task walkthrough → `workflow`
