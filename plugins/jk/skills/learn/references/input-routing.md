# Input Routing Reference

How SKILL.md routes after `classify-input.py` returns `{mode, topic, html, url, eli}`.

## Classifier Rules

- **Mode word**: only the first word, and only when it is exactly `overview`, `usage`, `workflow`, `internals`, `cheatsheet`, or `docs` (case-insensitive). There are no aliases. Any other first word is part of the topic, so `memory usage` stays a topic.
- **Default**: no mode word → `overview`; no mode word with `--eli<N>` → `eli`.
- **Flags** may appear anywhere and only as standalone tokens: `--eli<N>` (N = 1-99), `--md`, `--html`. Anything else, including `--eli0` or `--eli` without N, stays in the topic.

## Routing Table

| Mode | Answers | Default Output | Template |
|------|---------|----------------|----------|
| `none` | Empty input, or a mode word / flags without a topic | `AskUserQuestion` | — |
| `overview` | What is it, and should I use it? | MD terminal | `output-overview.md` |
| `usage` | How do I use it? | HTML browser | `output-usage.md` |
| `workflow` | How do I get one real task done, end to end? | HTML browser | `output-workflow.md` |
| `internals` | How does it work inside? | HTML browser | `output-internals.md` |
| `cheatsheet` | Where is that API / option again? | HTML browser | `output-cheatsheet.md` |
| `docs` | What should I read, and in what order? | MD terminal | `output-docs.md` |
| `eli` | I know nothing; explain it from zero | MD terminal | `output-eli.md` |

When `eli` is not null, also load `eli-modifier.md`, for every mode.

## URL Handling

When `url` is not null:
1. Fetch the page: `mcp__web_reader__webReader(url=<url>)` if registered, else `WebFetch(<url>)` (see SKILL.md "Dependencies & Fallback").
2. When `topic` equals the URL, take the topic from the page `<title>`, `<meta name="description">`, or first `<h1>`. Otherwise keep `topic` as the user's context (e.g. `check this for hooks`).
3. Use the page as the primary source, then continue with the mode's research strategy and template.

## Output Format

`--html` forces HTML and `--md` forces MD terminal; otherwise the mode default from the table applies.

When `html: true`:
1. Generate the full MD content first.
2. Render with `scripts/render-learn-html.py`; use `html-anything` only when `eli` is set or the script fails (see SKILL.md Step 5).
3. Save to the current working directory as `./{topic-slug}-learn.html`, unless the user gives a path.
4. Open it in the browser.
5. Do not print the raw MD to the terminal.

When `html: false`: print the MD content to the terminal.

## Examples

| Input | mode | topic | eli | html |
|-------|------|-------|-----|------|
| `zustand` | overview | zustand | null | false |
| `usage tanstack router` | usage | tanstack router | null | true |
| `internals react hooks --md` | internals | react hooks | null | false |
| `workflow auth with better-auth` | workflow | auth with better-auth | null | true |
| `cheatsheet zod --eli15` | cheatsheet | zod | 15 | true |
| `docs nextjs` | docs | nextjs | null | false |
| `event loop --eli5` | eli | event loop | 5 | false |
| `memory usage` | overview | memory usage | null | false |
| `usage https://orm.drizzle.team/docs/overview` | usage | (URL) | null | true |
