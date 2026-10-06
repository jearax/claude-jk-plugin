# ELI Modifier (`--eli<N>`)

Load this file whenever the classifier returns `eli` (not null). It changes **how** the content is written, never **what** sections a mode contains. N is the reader level: "explain like I'm N".

- With a mode word (`overview`, `usage`, `workflow`, `internals`, `cheatsheet`, `docs`): keep that mode's template and apply the rules below on top.
- Without a mode word: `mode: eli` uses the dedicated beginner template `output-eli.md`.

## Reader Level (N)

| N | Reader | Vocabulary | Examples |
|---|--------|------------|----------|
| 1-7 | No technical background | Everyday words only; define every technical term inline | Story or step-by-step trace; no code unless the topic is code itself |
| 8-14 | Uses apps and computers, has not programmed | Common tech words allowed (app, server, file); define deeper terms | Trace or tiny code, every line explained |
| 15+ | Has some programming or general tech basics | Standard terms allowed; define only topic-specific terms | Minimal runnable code |

## Rules (all levels)

1. **Define before use**: never use a term before it is explained. Define it inline on first use, and expand every abbreviation.
2. **One primary analogy per concept**: pick one familiar scenario (restaurant, post office, library, traffic). Map its parts to the real components, then state where the analogy stops matching reality.
3. **Keep every warning**: simplifying must never soften a warning. Security risks, data loss, irreversible commands, and cost impacts stay explicit, with their consequence in plain words.
4. **Keep accuracy**: the level changes vocabulary, prerequisites, and example depth only. Facts still match the official sources.
5. **Tone**: short sentences, active verbs, respectful adult tone. No baby talk, and no "simply", "just", "obviously"; what is obvious to an expert is not obvious to a beginner.

## Applying the Modifier to Each Mode

| Mode | What changes |
|------|--------------|
| `overview` | Add one analogy to the TL;DR; core concepts get plain-language definitions; comparison criteria are explained in a short note under the table |
| `usage` | Add a one-line "what this does" before each code block; comment every non-trivial line |
| `workflow` | State the goal in plain words; each step explains what it achieves before the code |
| `internals` | Open with an analogy for the architecture; each flow step gets a plain-language restatement |
| `cheatsheet` | Add a "Plain meaning" column to the API table |
| `docs` | Mark beginner-friendly pages; say what to read first when everything feels new |

Every mode with the modifier ends with a short **Glossary** table (term → plain meaning) for the terms it introduced.
