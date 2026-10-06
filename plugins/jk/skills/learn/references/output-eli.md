# Output Template: ELI Mode

Use this template when `mode: eli`, which the classifier returns only for `--eli<N>` without a mode word. Answers one question: **"I know nothing about this; help me understand it from zero."** Load `eli-modifier.md` first for the reader level table and writing rules.

## Template Structure

```markdown
# {Topic} - Explained for a {N}-year-old

## In a Nutshell
{1-2 sentences: what it is + why anyone needs it, in everyday words}

## What You Need to Know First
- **{Prerequisite 1}**: {1-line plain definition}
- **{Prerequisite 2}**: {1-line plain definition}
{Write "No background needed." when there are none}

## Picture It: {Everyday scenario}
{Describe the everyday scenario in 2-4 sentences}

| In everyday life | In {Topic} | Why they match |
|------------------|------------|----------------|
| {analogy part 1} | {real component 1} | {reason} |
| {analogy part 2} | {real component 2} | {reason} |

**Where the analogy stops:** {where it no longer matches reality, and the wrong assumption it could cause}

## How It Works, Step by Step
{Required: one small flow of these steps with plain labels — see visuals.md}

1. **{Step 1}**: {what happens, cause → effect}
2. **{Step 2}**: {what happens}
3. **{Step 3}**: {what happens}

## The Smallest Example
{Runnable code for code topics, or a step-by-step trace for concepts}
```{lang}
{minimal example, every line commented}
```
**What just happened:** {map each part of the example back to the steps above}

## Misconceptions & Warnings
- **Misconception:** {common wrong belief} → **Reality:** {correct fact}
- ⚠️ **{Warning}**: {exact consequence in plain words}

## Glossary
| Term | Plain meaning |
|------|---------------|
| {term} | {plain meaning} |

## Check Yourself
1. {Question on the core idea}
2. {Question on the mechanism}
3. {Question applying it to a new situation}

<details><summary>Answers</summary>

1. {answer}
2. {answer}
3. {answer}

</details>

## Next Steps
- {Next topic 1} — {why it comes next}
- {Next topic 2} — {why it comes next}
- Go further: `/jk:learn overview {topic}` → `usage` → `workflow` → `internals` (add `--eli{N}` to keep this level)
```

## Section Guidelines

- **Order matters**: the reader meets every concept in "What You Need to Know First" or inline before it is used.
- **Analogy**: one scenario only. Always fill the mapping table and "Where the analogy stops".
- **Visuals**: follow `visuals.md` (one mechanism flow, max 6 nodes).
- **Mechanism**: 3-6 steps, each cause → effect. No step may rely on a concept the reader has not met yet.
- **Example**: the smallest thing that shows the mechanism. Example depth follows the reader level table in `eli-modifier.md`.
- **Check yourself**: 3 questions, from recall to application. Answers sit inside `<details>` so the reader can try first.

## Not in This Mode

- No comparison tables or API lists; they distract a beginner. Point to the other modes in "Next Steps" instead.
