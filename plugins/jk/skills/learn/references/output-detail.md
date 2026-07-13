# Output Template: Detail Mode

Use this template when `mode: detail`. Extends full mode with internals and edge cases.

## Template Structure

```markdown
# {Topic} - Deep Dive Guide

## TL;DR
- **What**: {1-line definition}
- **Problem it solves**: {1-2 lines on the core problem}
- **When to use**: {1 line on best-fit scenarios}

## Comparison with Alternatives
| Feature | {Topic} | {Alt 1} | {Alt 2} | {Alt 3} |
|---------|---------|---------|---------|---------|
| {Feature 1} | ... | ... | ... | ... |
| Learning Curve | ... | ... | ... | ... |
| Performance | ... | ... | ... | ... |
| Community | ... | ... | ... | ... |

**When to choose {Topic}:** {2-3 bullet points}

## Architecture Internals

### How It Works Under the Hood
{Explain the core architecture, data flow, key design decisions}

### Key Design Patterns Used
- {Pattern 1}: {how it's applied}
- {Pattern 2}: {how it's applied}

## Common Use Cases (with Code Examples)

### 1. {Use Case Title}
**When:** {scenario}
```{lang}
{detailed, well-commented code example}
```
**Why this works:** {1-2 lines explaining the approach}

### 2. {Use Case Title}
{... same structure, deeper examples ...}

### 3. {Use Case Title}
{... same structure ...}

## Advanced Patterns

### {Advanced Pattern}
```{lang}
{code showing advanced usage}
```

## Edge Cases & Gotchas

### Common Pitfalls
1. **{Pitfall 1}**: {description + fix}
2. **{Pitfall 2}**: {description + fix}
3. **{Pitfall 3}**: {description + fix}

### Performance Considerations
- {consideration 1}
- {consideration 2}

## Cheat Sheet
| Function/Method | Purpose | Example |
|----------------|---------|---------|
| ... | ... | ... |

## Bonus: Less Common Use Cases
{Same as full mode — 1-2 niche use cases}
```

## Section Guidelines

- **Architecture Internals**: Explain WHY, not just WHAT. Show mental model.
- **Code Examples**: More detailed than full mode. Include comments explaining reasoning.
- **Edge Cases**: Minimum 3 pitfalls. Each with description + how to avoid/fix.
- **Performance**: Include memory, speed, bundle size considerations if applicable.
- **Advanced Patterns**: Show power-user techniques.

## Differences from Full Mode

| Aspect | Detail | Full |
|--------|--------|------|
| Architecture section | Included | Not included |
| Edge cases | 3+ pitfalls | Not included |
| Code depth | Well-commented, explained | Concise, runnable |
| Performance | Dedicated section | Not included |
| Research | 4 searches (extra: internals) | 3 searches |

## Output Language

- Output in Vietnamese per CLAUDE.md rules
- Technical terms keep English with Vietnamese annotation format
- Code comments in English
