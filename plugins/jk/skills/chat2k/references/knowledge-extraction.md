# Knowledge Extraction Heuristics

How to group a normalized chat transcript into **decided knowledge** and drop noise.

## Step 1 — Topic clustering

A **topic cluster** is a contiguous run of messages on one subject. Heuristic detection:

1. Start a new cluster when:
   - A user message introduces a new keyword not seen in the previous 3 messages.
   - The previous cluster ended with a decision ("let's go with X", "chốt", "dùng X").
   - 5+ messages pass without same-keyword overlap.
2. Stay in the same cluster when:
   - Same entities (framework names, tool names, error codes) appear.
   - Same question is being answered across multiple turns.
   - User is clarifying/refining an earlier point.

**Mark-driven filtering** (when `--marks` is given): keep only clusters whose topic tokenizes to share ≥ 1 word with any mark (case-insensitive substring match).

## Step 2 — Decided-signal detection

A cluster contains **decided knowledge** if one of:

- Explicit decision marker: `decision:`, `let's go with`, `we'll use`, `chốt`, `quyết định`, `dùng X cho Y`, `chọn X`
- Comparative structure: assistant gave a side-by-side (pros/cons, vs) and user accepted (no follow-up correction)
- Q&A + acceptance: user asked a question, assistant answered, next user turn thanks / agrees / moves on (no objection)
- Citation present: assistant cited an official doc URL AND the answer is non-trivial

If no decided signal → **drop the cluster** (it's discussion, not knowledge).

## Step 3 — Extract fields per topic

For each surviving cluster, fill:

| Field | How to extract |
|---|---|
| `topic` | Concise title (≤ 8 words). Prefer the user's own phrasing if they used one (`let's compare X vs Y` → "X vs Y") |
| `subjects` | Items compared/discussed (frameworks, libs, tools, approaches). Strip duplicates. |
| `pros` | Per-subject advantages. From assistant's analysis + user additions. |
| `cons` | Per-subject disadvantages. Same source. |
| `use_cases` | When each subject fits. Usually phrased as "use X for Y" or "X is good when …". |
| `decision` | What was decided. If no decision → "open" or "no decision". Cite the deciding message. |
| `sources` | URLs / doc references mentioned in the discussion. **MUST be verified** before including. |

## Step 4 — Multi-subject rollup

If a cluster compares > 4 subjects, group related ones in a sub-section. Example: comparing 6 React state libs → one "State management" topic with 6 subjects in a table, not 6 separate topics.

## Step 5 — Filter noise within clusters

Even within a "decided" cluster, drop:

- Greetings, pleasantries, "thanks", "ok"
- Retries: "let me try again", "actually nevermind", "give me a sec"
- Tool-call traces that don't carry meaning
- Redundant rephrasing of the same point
- System reminders, hook outputs

## Step 6 — Filter noise at the message level

Before clustering, drop messages that are entirely:
- One word / one emoji
- Pure tool output (`[tool_use: bash]`, `[tool_result: ...]`)
- Command echoes / command outputs that don't carry decisions
- Repeated context (user saying "as I said before, …")

## Anti-patterns

- **Don't** extract every Q&A as a topic. Only Q&A with a *result the user accepted*.
- **Don't** invent pros/cons the chat didn't surface. If the chat only mentioned pros, list only pros.
- **Don't** infer a decision the chat didn't make. If no decision → write "open" explicitly.
- **Don't** include URLs the chat mentioned without verifying them.
