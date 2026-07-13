# Output Template: Quick Mode

Use this template when `mode: quick` (default). Lightweight, terminal-friendly, top use cases only.

## Template Structure

```markdown
# {Topic} - Quick Learn

## TL;DR
- **What**: {1-line definition}
- **Best for**: {1-line on strongest use case}
- **Not for**: {1-line on when to avoid}

## Top Use Cases (most common)

### 1. {Strongest Use Case}
**When:** {most common scenario}
```{lang}
{minimal, runnable code example}
```

### 2. {Second Use Case}
**When:** {scenario}
```{lang}
{minimal, runnable code example}
```

## Quick Compare
| {Topic} | {Top Alternative} |
|---------|-------------------|
| {best for} | {best for} |

**Choose {Topic} when:** {1-line rule of thumb}
```

## Section Guidelines

- **TL;DR**: 3 lines max. Scannable in 5 seconds.
- **Top Use Cases**: 2 examples MAX — only the strongest, most widely used patterns. No niche cases.
- **Quick Compare**: Single alternative only. One-row table. No exhaustive comparison.
- **No cheat sheet, no bonus section** — quick mode is for "give me the gist".

## Differences from Full Mode

| Aspect | Quick | Full |
|--------|-------|------|
| Use cases | 2 (strongest only) | 3+ |
| Comparison | 1 alternative | 3+ alternatives |
| Cheat sheet | None | API ref + patterns |
| Bonus | None | Niche use cases |
| Output | MD terminal | HTML browser |

## Output Language

- Output in Vietnamese per CLAUDE.md rules
- Technical terms keep English with Vietnamese annotation format
