# Output Template: Cheatsheet Mode

Use this template when `mode: cheatsheet`. Focused, scannable, API-first.

## Template Structure

```markdown
# {Topic} - Cheat Sheet

## Quick Start
```{lang}
{minimal setup/getting-started code, 5-10 lines max}
```

## API Quick Reference

### Core API
| Function/Method | Purpose | Signature | Example |
|----------------|---------|-----------|---------|
| {fn1} | {what it does} | {signature} | `{example}` |
| {fn2} | {what it does} | {signature} | `{example}` |
| {fn3} | {what it does} | {signature} | `{example}` |

### Configuration Options
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| ... | ... | ... | ... |

## Patterns Quick Card

### Pattern 1: {Name}
```
{visual pattern representation, like a mini flowchart or pseudo-code}
```

### Pattern 2: {Name}
```
{visual pattern representation}
```

### Pattern 3: {Name}
```
{visual pattern representation}
```

## Common Pitfalls

1. **{Pitfall}**: {1-line description} → Fix: {1-line fix}
2. **{Pitfall}**: {1-line description} → Fix: {1-line fix}
3. **{Pitfall}**: {1-line description} → Fix: {1-line fix}
4. **{Pitfall}**: {1-line description} → Fix: {1-line fix}
5. **{Pitfall}**: {1-line description} → Fix: {1-line fix}

## Memory Aids

- {Mnemonic or mental model 1}
- {Mnemonic or mental model 2}
```

## Section Guidelines

- **Quick Start**: Absolute minimum to get running. Copy-paste friendly.
- **API Reference**: Comprehensive. Include ALL commonly used functions.
- **Patterns**: Visual and scannable. Think "flashcard" not "textbook".
- **Pitfalls**: 3-5 items. Format: Problem → Fix. One line each.
- **Memory Aids**: Mnemonics, mental models, acronyms — anything that aids recall.

## Design Principles

1. **Scannable in 30 seconds**: Reader should find any API in <30s
2. **Copy-paste ready**: Every example should work standalone
3. **No prose**: Tables, code blocks, bullet points only. No paragraphs.
4. **Visual hierarchy**: Use headers and separators to create clear sections
5. **Concise**: Every word must earn its place

## Output Language

- Output in Vietnamese per CLAUDE.md rules
- Technical terms keep English with Vietnamese annotation format
- Keep API signatures in English (code is universal)
