# Research Strategy Reference

Defines research orchestration for each mode. Execute in order: Phase A → B → C.

## Phase A: Official Docs (all modes)

1. Fetch official documentation for the topic:
   - **Preferred:** invoke docs-seeker skill (`/ak:docs-seeker`) with `"{topic}"` if registered → extracts API reference, guides, quickstart.
   - **Fallback:** `WebSearch("{topic} official documentation")` → `WebFetch(<official-doc-url>)` on the canonical docs site. Extract API reference, guides, quickstart manually.
   - (See SKILL.md "Dependencies & Fallback" for the detection rule.)
2. If URL was provided (from input routing):
   - Already fetched via `mcp__web_reader__webReader` (fallback: `WebFetch`) in input routing step
   - Use this as primary source, supplement with the Phase A docs fetch above

## Phase B: Web Research (parallel WebSearch calls)

Run searches in **parallel** using multiple `WebSearch` tool calls simultaneously.

### Source Priority (IMPORTANT)

When evaluating search results, prioritize in this order:
1. **Official documentation** — official docs sites, GitHub README, official guides
2. **Official repositories** — GitHub/GitLab repos by the original authors
3. **Well-known blogs** — authors recognized in that ecosystem (e.g. Kent C. Dodds for React, Josh W. Comeau for CSS, etc.)
4. **Strong communities** — Stack Overflow answers with high votes, dev.to, MDN, CSS-Tricks, etc.
5. **Other sources** — only if higher-priority sources lack the needed info

When multiple sources conflict, **official docs always win**.

### Search Templates

| # | Query Template | Used By Modes |
|---|---------------|---------------|
| S1 | `"{topic} most common use cases best practices"` | quick, cheatsheet |
| S2 | `"{topic} vs alternatives comparison {year}"` | full, overview, detail |
| S3 | `"{topic} common use cases examples best practices"` | full, detail, cheatsheet |
| S4 | `"{topic} advanced patterns tricks less known"` | full, detail |
| S5 | `"{topic} architecture internals source code"` | detail only |

### Mode → Search Mapping

| Mode | Searches | Parallel? |
|------|----------|-----------|
| quick | S1 | Single call |
| full | S2, S3, S4 | Yes (3 parallel) |
| overview | S2 | Single call |
| detail | S2, S3, S4, S5 | Yes (4 parallel) |
| cheatsheet | S1, S3 | Yes (2 parallel) |

**Year placeholder**: Replace `{year}` with current year.

## Phase C: Synthesis

1. Combine Phase A (official docs) + Phase B (web search results)
2. Deduplicate overlapping information
3. Extract: key concepts, API signatures, code examples, comparison data
4. Organize by the output template structure (see `output-{mode}.md`)
5. If information is insufficient for any section:
   - Run 1 additional targeted search for that specific gap
   - Max 1 follow-up search to avoid token waste

## Token Budget Guidelines

| Mode | Max Research Tokens | Sources |
|------|--------------------|---------|
| quick | Minimal (~1 search) | 1 search + docs fetch |
| overview | Low (~2 searches) | 1 search + docs fetch |
| cheatsheet | Low (~2 searches) | 2 searches + docs fetch |
| full | Medium (~3 searches) | 3 searches + docs fetch |
| detail | High (~4 searches) | 4 searches + docs fetch |

Keep research focused — prefer depth on target topic over breadth of alternatives.
