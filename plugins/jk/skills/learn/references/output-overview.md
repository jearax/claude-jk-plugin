# Output Template: Overview Mode

Use this template when `mode: overview`. Lightweight, decision-focused output.

## Template Structure

```markdown
# {Topic} - Overview

## TL;DR
- **What**: {1-line definition}
- **Problem it solves**: {1-2 lines on the core problem}
- **When to use**: {1 line on best-fit scenarios}

## When to Use / When NOT to Use

### Use {Topic} when:
- {bullet point 1}
- {bullet point 2}
- {bullet point 3}

### Consider alternatives when:
- {bullet point 1}
- {bullet point 2}
- {bullet point 3}

## Comparison with Alternatives
| Feature | {Topic} | {Alt 1} | {Alt 2} | {Alt 3} |
|---------|---------|---------|---------|---------|
| {Feature 1} | ... | ... | ... | ... |
| Learning Curve | ... | ... | ... | ... |
| Community | ... | ... | ... | ... |

**When to choose {Topic}:** {2-3 bullet points}
**When to choose alternatives:** {brief guidance}
```

## Section Guidelines

- **TL;DR**: Same as full mode — scannable in 10 seconds.
- **When to Use/NOT**: Decision matrix format. Help reader decide quickly.
- **Comparison**: Minimum 3 alternatives. Same table as full mode.
- **No code examples** — overview is for decision-making, not implementation.
- **No cheat sheet** — too detailed for overview context.

## Differences from Full Mode

| Aspect | Overview | Full |
|--------|----------|------|
| Code examples | None | 3+ with runnable code |
| Cheat sheet | None | API ref + patterns card |
| Bonus section | None | Niche use cases |
| Decision matrix | Explicit use/not-use | Implied in comparison |
| Length | Short (~100 lines) | Long (~250 lines) |

## Output Language

- Output in Vietnamese per CLAUDE.md rules
- Technical terms keep English with Vietnamese annotation format
