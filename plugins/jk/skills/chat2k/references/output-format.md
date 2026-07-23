# Output Markdown Format

The generated `.md` file follows this template. Fill every section. Skip the References section only if no links survived verification.

## Template

```markdown
# {Title}

> {One-line summary — what was decided, in 1 sentence}

---

## Overview

{2-4 sentences. What was the session about, what subjects were discussed, what's the takeaway in plain language.}

---

## Topics

### 1. {Topic title}

**Subjects**: {comma-separated list of compared items}

| Subject | Pros | Cons | Use cases |
|---|---|---|---|
| {name} | {adv1}; {adv2} | {disadv1} | {case1}; {case2} |
| {name} | {adv1} | {disadv1}; {disadv2} | {case1} |

**Decision**: {what was decided, or "open — no decision yet"}.

**Rationale**: {why this decision was made, citing the deciding message}.

**Sources**:
- [{title1}]({url1})
- [{title2}]({url2})

---

### 2. {Next topic}

{repeat the structure}

---

## Decisions Summary

| # | Topic | Decision | Why |
|---|---|---|---|
| 1 | {topic} | {decision} | {one-line reason} |
| 2 | {topic} | open | {why not decided} |

---

## References

- [{title}]({url}) — {one-line: what this is / why it matters}
- [{title}]({url}) — {one-line}
- [broken] {url} — dropped: {reason}
```

> **No Notes section.** The output is knowledge, not commentary. Insights belong in the topic body or Pros/Cons tables, not a stray trailing section.

## Style rules

- **Heading levels**: `#` title, `##` major section, `###` per topic.
- **Tables**: use GitHub-flavored markdown. Numbers in columns right-aligned if comparing.
- **Comparisons**: prefer tables over prose when 2+ subjects share the same dimensions (pros/cons/use cases).
- **Decisions**: every comparison topic MUST have a `Decision` line — even if it's "open". A topic without a decision gets dropped.
- **Sources line in body** — convert to a bullet list (one link per line), NOT a single comma-separated line:
  ```markdown
  # ✅ CORRECT — list format
  **Sources**:
  - [Bun build CLI](https://bun.sh/docs/cli/build)
  - [Bun bundler docs](https://bun.com/docs/bundler)
  - [esbuild docs](https://esbuild.github.io/)

  # ❌ WRONG — single line
  **Sources**: [Bun build CLI](https://bun.sh/docs/cli/build), [Bun bundler docs](https://bun.com/docs/bundler), [esbuild docs](https://esbuild.github.io/)
  ```
- **Link format — clean markdown only**:
  - Use `[title](url)` — never bare URLs.
  - **NO `[verified]` markers anywhere** — verification happened silently before writing.
  - **NO `[src: https://...]` inline citations in body, tables, or anywhere** — this is the most common mistake. Body citations should be plain markdown links `[claim text](url)` OR omitted entirely (the reader finds the source in References).
  - Tables: no `[src: ...]` annotations in cells. Keep cells clean.
  - Bad: `Output ESM sạch `[src: https://rollupjs.org/]``
  - Good: `Output ESM sạch`
  - Bad: `~34.10s [src: https://bun.com/docs/bundler]`
  - Good: `~34.10s` (cite in References if needed)
- **Broken links**: only kept if at least one passing link survived (for transparency). Mark as `[broken] {url} — dropped: {reason}`.
- **PII redaction**: replace any email, API key, token, env var value with `<redacted>` before writing.
- **No emojis** in body content (matches house style).

## References section — exact format

```markdown
## References

- [Bun build CLI](https://bun.sh/docs/cli/build) — flags, targets, formats, `--compile`, plugin/loader API
- [Bun bundler docs](https://bun.com/docs/bundler) — entry points, watch, JS API, benchmark framing
- [esbuild docs](https://esbuild.github.io/) — speed rationale, built-in JS/TS/CSS/JSX
- [Rollup docs](https://rollupjs.org/) — tree-shaking, plugin API, output formats
- [Tony Cabaye, 2024 Bundlers Comparison](https://tonai.github.io/blog/posts/bundlers-comparison/) — empirical pros/cons + library build benchmarks
- [tsdown repo](https://github.com/rolldown/tsdown) — Rolldown/Oxc-backed, tsup-compatible successor
- [tsup repo](https://github.com/egoist/tsup) — esbuild-backed library bundler
```

One blank line max between entries. **Each entry: `[title](url) — one-line description`** (em-dash + description). Alphabetized by source title. Each entry ≤ 120 chars. No `[verified]`. No `[src: ...]`. No bare URLs.

## Filename

Default: `<pwd>/chat2k-{YYYY-MM-DD}-{slug}.md` — absolute path **resolved from the current working directory at run time**.

- `{pwd}` = the directory the user is in when invoking `/jk:chat2k` (e.g. `/Users/foo/projects/bar`). The default file lands in that directory, not in `~/.claude/notes/`.
- `slug` = lowercase, dash-separated, max 5 words from the first topic title.
- Date is the session's last timestamp (fallback: current date).
- If user passed `--out`, that absolute path wins. A relative `--out` is resolved against `pwd`.

## Size limits

- Single topic body ≤ 30 lines. If exceeded, group adjacent sub-topics or move detail to a sub-heading.
- Total note ≤ 500 lines. If exceeded, trim low-density prose; keep tables and decisions.
- References section ≤ 50 entries. If exceeded, keep only the most-cited 50.
