# Input Routing Reference

How SKILL.md should route after `classify-input.py` returns JSON result.

## Routing Table

| Mode | Condition | Output | References to Load |
|------|-----------|--------|--------------------|
| `none` | Empty/missing input | `AskUserQuestion` | None |
| `quick` | Default (bare topic), fast, quick, brief, tell me about | MD terminal | `output-quick.md`, `research-strategy.md` (1 search) |
| `full` | full, strict, hard, comprehensive, thorough | HTML browser | `output-full.md`, `research-strategy.md` (3 searches) |
| `detail` | detail, deep, deep dive | HTML browser | `output-detail.md`, `research-strategy.md` (4 searches) |
| `overview` | overview | MD terminal | `output-overview.md`, `research-strategy.md` (1 search) |
| `cheatsheet` | cheat, cheatsheet | HTML browser | `output-cheatsheet.md`, `research-strategy.md` (2 searches) |
| URL | Any URL detected | HTML browser (full mode) | Fetch URL → `output-full.md`, `research-strategy.md` |

## URL Handling

When `url` field is not null:
1. Fetch URL content: `mcp__web_reader__webReader(url=<url>)`
2. Extract topic from page `<title>`, `<meta name="description">`, or first `<h1>`
3. Use extracted topic as `topic` value going forward
4. Include page content as additional research source
5. Proceed with `mode: full` research strategy (HTML output)

## Output Format Handling

Determined by mode + explicit flags (`--html` / `--md`):

| Mode | Default Output | Override |
|------|---------------|----------|
| quick | MD terminal | `--html` → HTML |
| overview | MD terminal | `--html` → HTML |
| full | HTML browser | `--md` → MD terminal |
| detail | HTML browser | `--md` → MD terminal |
| cheatsheet | HTML browser | `--md` → MD terminal |

When `html: true`:
1. Complete all research and MD generation normally
2. Activate `html-anything` skill with the MD content
3. Save to CWD as `./{topic}-learn.html`
4. Open in browser
5. Do NOT output raw MD to terminal

When `html: false`:
- Output MD content directly to terminal

## Edge Cases

- **URL + intent keyword**: URL takes priority, intent keyword ignored
- **Multiple flags**: `--md` and `--html` supported; unknown flags treated as part of topic
- **Very long topic**: No truncation needed — LLM handles it naturally
- **Non-English topic**: No special handling — LLM processes naturally
