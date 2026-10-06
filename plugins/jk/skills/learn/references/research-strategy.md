# Research Strategy Reference

Defines research per mode. Execute in order: Phase A → B → C. Each mode researches only what its own template needs.

## Phase A: Official Sources (all modes)

1. Fetch the official documentation for the topic:
   - **Preferred:** the `/ak:docs-seeker` skill with `"{topic}"`, if registered.
   - **Fallback:** `WebSearch("{topic} official documentation")` → `WebFetch(<official-doc-url>)` on the canonical docs site.
   - (See SKILL.md "Dependencies & Fallback" for the detection rule.)
   - **Concept topics** (protocols, runtime behavior, patterns such as TCP, DNS, event loop) often have no docs site. Use the authoritative spec or reference instead: RFC, W3C/WHATWG spec, MDN, or the runtime's official page for that concept.
2. If a URL was provided, it was already fetched during routing. Use it as the primary source and supplement it with Phase A.

Pick the docs pages that match the mode: introduction/concepts for `overview`, guides and examples for `usage`, tutorials or end-to-end guides for `workflow`, architecture or design docs for `internals`, API reference for `cheatsheet`, and the docs index (navigation, sitemap, `llms.txt`, changelog) for `docs`.

## Phase B: Web Research

Run the mode's searches in **parallel** with multiple `WebSearch` calls.

### Source Priority

1. **Official documentation**: docs sites, official guides
2. **Official repositories**: GitHub/GitLab repos by the original authors (README, docs, issues, discussions)
3. **Recognized experts**: authors known in that ecosystem
4. **Strong communities**: highly voted Stack Overflow answers, MDN
5. **Other sources**: only when higher-priority sources lack the information

When sources conflict, **official sources always win**.

### Search Templates

| # | Query Template | Mode |
|---|----------------|------|
| S1 | `"{topic} vs alternatives comparison {year}"` | overview |
| S2 | `"{topic} common use cases examples best practices"` | usage |
| S3 | `"{topic} patterns real world project"` | usage |
| S4 | `"{topic} step by step tutorial end to end"` | workflow |
| S5 | `"{topic} common errors troubleshooting"` | workflow |
| S6 | `"{topic} architecture internals how it works"` | internals |
| S7 | `"{topic} pitfalls gotchas performance"` | internals |
| S8 | `"{topic} API reference options"` | cheatsheet |
| S9 | `"{topic} official documentation getting started guide"` | docs |
| S10 | `"{topic} explained for beginners how it works"` | eli |

### Mode → Search Mapping

| Mode | Searches | Parallel? |
|------|----------|-----------|
| overview | S1 | Single call |
| usage | S2, S3 | Yes (2 parallel) |
| workflow | S4, S5 | Yes (2 parallel) |
| internals | S6, S7 | Yes (2 parallel) |
| cheatsheet | S8 | Single call |
| docs | S9 | Single call |
| eli | S10 | Single call |

`--eli<N>` on another mode adds no searches; it only changes how the content is written.

**Docs note:** every URL in the output must be opened with `WebFetch` first. Drop links that fail; never build a URL from a guessed path.

**Eli note:** S10 results only help pick the analogy and the order of explanation. Every fact shown to the reader (mechanism steps, warnings, definitions) must still match the Phase A official source. Beginner tutorials simplify, and some simplify into errors.

**Year placeholder**: replace `{year}` with the current year.

## Phase C: Synthesis

1. Combine Phase A (official sources) and Phase B (web results).
2. Deduplicate overlapping information.
3. Keep only what the mode's template asks for; drop the rest.
4. If a template section still lacks information, run 1 more targeted search for that gap. Never more than 1 follow-up search.
5. If the information still cannot be verified, omit the field or mark it as unverified. Never invent data to fill a table.
