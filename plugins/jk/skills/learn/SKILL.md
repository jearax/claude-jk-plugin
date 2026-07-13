---
name: jk:learn
description: "Learn technologies, libraries, frameworks through structured research. Use when user says 'learn X', 'tell me about X', 'overview of X', 'detail X', 'cheatsheet X', 'full X', or provides a URL. Generates comparisons, code examples, cheat sheets."
argument-hint: "[quick|full|detail|overview|cheatsheet] [topic-or-url] [--md|--html]"
metadata:
  author: jjuidev
  version: "1.0.0"
---

# /jk:learn — Quick Learn Skill

Learn a new library, framework, or technology through one command. Auto-research, compare alternatives, synthesize use cases, and generate cheat sheets.

## Modes

| Mode | Trigger | Output | Research |
|------|---------|--------|----------|
| **quick** (default) | Bare topic, fast, quick, brief, simple, short | MD terminal | Light — 1 search |
| **full** | full, strict, hard, comprehensive, thorough | HTML browser | Full — 3 searches |
| **detail** | detail, deep, deep dive | HTML browser | Deep — 4 searches |
| **overview** | overview | MD terminal | Light — 1 search |
| **cheatsheet** | cheat, cheatsheet | HTML browser | API-focused — 1 search |

**Override flags**: `--html` forces HTML, `--md` forces MD terminal.

## Dependencies & Fallback

`jk:learn` is **standalone** — it works with only built-in tools. Companion skills from claudekit/AgentKit are used when available for richer output; each has a built-in fallback. Resolve in order (preferred → fallback):

| Capability | Preferred (if registered in runtime) | Fallback (always available) |
|---|---|---|
| Official docs fetch | `/ak:docs-seeker` skill | `WebSearch` + `WebFetch(<official-doc-url>)` |
| URL → markdown | `mcp__web_reader__webReader` MCP tool | `WebFetch(<url>)` |
| MD → HTML render | `html-anything` skill | Write minimal self-contained HTML (`<!doctype html>…<pre>{md}</pre>…`) to `./{topic}-learn.html`, or fall back to `--md` terminal output |
| Visual analysis | `ai-multimodal` skill | Skip (optional — only when visual context adds value) |
| Python (input classifier) | `~/.claude/skills/.venv/bin/python3` | `python3` (script is stdlib-only) |

**Detection rule:** before invoking a preferred capability, check whether the skill / slash command / MCP tool is registered in the current runtime. If not, use the fallback column **silently** — do not error, warn, or ask the user. Never block on a missing companion skill.

## Process Flow

```mermaid
flowchart TD
    A["User: /jk:learn {args}"] --> B["Run classify-input.py"]
    B --> C{"Mode?"}
    C -->|none| D["AskUserQuestion"]
    C -->|quick (default)| E["Light research → MD terminal"]
    C -->|full| F["Full research → HTML"]
    C -->|detail| G["Deep research → HTML"]
    C -->|overview| H["Light research → MD terminal"]
    C -->|cheatsheet| I["API research → HTML"]
    C -->|URL| J["webReader → full research → HTML"]
    D --> E
    J --> F
```

## Step 1: Classify Input

Run the classifier script to parse user input:

```bash
# Path relative to this SKILL.md folder.
# Script is stdlib-only (sys, re, json) — any python3 works.
# Prefer shared claudekit venv if present, else system python3.
~/.claude/skills/.venv/bin/python3 scripts/classify-input.py "$ARGUMENTS" 2>/dev/null \
  || python3 scripts/classify-input.py "$ARGUMENTS"
```

> Resolve `scripts/classify-input.py` to absolute path of this skill folder before executing. The skill folder is the directory containing this SKILL.md (auto-detected by the agent runtime).

Parse JSON output: `{mode, topic, html, url}`.

If `mode: "none"` → use `AskUserQuestion` to ask user what they want to learn.

## Step 2: Route by Mode

Load `references/input-routing.md` for full routing logic.

**Quick reference:**

| Mode | Research | Output Template |
|------|----------|-----------------|
| quick | docs-seeker + 1 WebSearch | `references/output-quick.md` |
| full | docs-seeker + 3 WebSearch | `references/output-full.md` |
| overview | docs-seeker + 1 WebSearch | `references/output-overview.md` |
| detail | docs-seeker + 4 WebSearch | `references/output-detail.md` |
| cheatsheet | docs-seeker + 1 WebSearch | `references/output-cheatsheet.md` |

## Step 3: Execute Research

Load `references/research-strategy.md` for detailed research plan.

1. **Phase A**: Activate `docs-seeker` skill with topic → fetch official docs
2. **Phase B**: Run parallel `WebSearch` calls per mode (see research-strategy.md for query templates)
3. **Phase C**: Synthesize all sources into structured output

If URL was provided → already fetched via `mcp__web_reader__webReader` in routing step.

## Step 4: Generate Output

Load the appropriate `references/output-{mode}.md` template.

Fill template sections with research results. Follow the template structure exactly.

**Output language**: Vietnamese per CLAUDE.md rules. Technical terms keep English format: `English_Word (Vietnamese_Word)`.

## Step 5: Output Format

If `html: true` (full, detail, cheatsheet modes, or `--html` flag):
1. Complete MD content generation first
2. Activate `html-anything` skill with the generated MD content
3. Save HTML output to **current working directory** (e.g. `./{topic}-learn.html`), unless user specifies a different path
4. Ensure HTML has `<meta charset="UTF-8">` — Vietnamese text per CLAUDE.md rules
5. Open HTML in browser
6. Do NOT output raw MD to terminal

If `html: false` (quick, overview modes, or `--md` flag):
- Output MD content directly to terminal

## Workflow Position

**Related skills (optional — from claudekit/AgentKit, with built-in fallbacks, see Dependencies & Fallback above):**
- `docs-seeker` — fetches official documentation (fallback: `WebSearch` + `WebFetch`)
- `html-anything` — renders MD to HTML (fallback: minimal inline HTML or `--md` terminal)
- `ai-multimodal` — can supplement with visual analysis if needed (fallback: skip)
