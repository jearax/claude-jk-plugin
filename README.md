# claude-jk-plugin

**jjuidev Kit (`jk`)** — companion skills for [Claude Code](https://github.com/anthropics/claude-code) under the `/jk:*` namespace.

**Dual distribution**: Claude Code plugin marketplace **+** [`npx skills`](https://github.com/vercel-labs/skills) CLI (works with OpenCode, Codex, Cursor, and 50+ agents).

Maintained by [jjuidev](https://github.com/jearax).

## Prerequisites

- Claude Code ≥ 2.x (Plugins GA) **or** any agent supported by `npx skills`
- **claudekit** installed — `jk` skills depend on shared assets (`docs-seeker`, `html-anything`, `ai-multimodal`) and the shared Python venv at `~/.claude/skills/.venv/bin/python3`

## Install

### A. Claude Code (plugin marketplace)

```bash
# From GitHub (after publish)
/plugin marketplace add jearax/claude-jk-plugin
/plugin install jk@jk-marketplace

# Local development
/plugin marketplace add /Users/tandm/Documents/jjuidev/npm/ai-skills/claude-jk-plugin
/plugin install jk@jk-marketplace
```

Update flow:

```bash
/plugin marketplace update jk-marketplace
/plugin update jk
```

### B. OpenCode / Codex / Cursor / others (via `npx skills`)

```bash
# From GitHub (after publish)
npx skills add jearax/claude-jk-plugin -a opencode -g

# Local development
npx skills add /Users/tandm/Documents/jjuidev/npm/ai-skills/claude-jk-plugin -a opencode -g
```

Install targets (global mode):

| Agent | Path |
|---|---|
| OpenCode | `~/.agents/skills/jk-learn/` |
| Claude Code | `~/.claude/skills/jk-learn/` |
| Codex | `~/.codex/skills/jk-learn/` |
| Cursor | `~/.cursor/skills/jk-learn/` |

Default mode is `copy`. To re-install after updates, re-run the command.

## Skills included

| Skill | Description |
|---|---|
| `jk:learn` | Learn a library/framework via structured research. Modes: `quick`, `full`, `detail`, `overview`, `cheatsheet`. Supports URL input and `--md`/`--html` output. |
| `jk:translate` | Context-aware bilingual translator (EN/mixed → Vietnamese) for dev/IT content — error messages, tickets, docs, PRs. Verifies uncertain IT terms against official docs. Output: parallel EN↔VI chunks, console-readable. |
| `jk:chat2k` | Chat-to-Knowledge — extract *decided* knowledge (topics compared, pros/cons, use cases, decisions, verified links) from any CLI chat session (claude, opencode, codex, cursor) into a beautiful Markdown note. Filters noise, never dumps transcripts. |

## Usage examples

```text
/jk:learn nextjs
/jk:learn full tanstack-router
/jk:learn cheatsheet zod
/jk:learn https://orm.drizzle.team/docs/overview

/jk:translate Fix the flaky test in auth.spec.ts. The JWT expires before the assertion runs.

/jk:chat2k --current
/jk:chat2k --from /path/to/session.jsonl --out ~/notes/auth-review.md
/jk:chat2k --current --marks "auth,deployment"
```

## Migrating from `ckc` (v1.x → v2.0.0)

v2.0.0 renames the namespace `/ckc:*` → `/jk:*` (breaking). To migrate:

```bash
# Remove old ckc installs (orphaned after upgrade)
rm -rf ~/.claude/skills/ckc-* ~/.agents/skills/ckc-* ~/.codex/skills/ckc-* ~/.cursor/skills/ckc-*

# Reinstall under jk
/plugin marketplace add jearax/claude-jk-plugin
/plugin install jk@jk-marketplace
```

Old `/ckc:*` commands now resolve to `/jk:*`.

## Add a new skill

1. Create `plugins/jk/skills/<skill-name>/SKILL.md` with YAML frontmatter (`name:` and `description:` required).
2. Drop assets into `plugins/jk/skills/<skill-name>/references/`, `scripts/`, etc.
3. **Reference assets with relative paths** (e.g. `references/foo.md`, `scripts/bar.py`) — works in both Claude Code plugin runtime and `npx skills` installs. Avoid `${CLAUDE_PLUGIN_ROOT}` for cross-tool compatibility.
4. Bump `version` in `plugins/jk/.claude-plugin/plugin.json`.
5. Commit & push.

## Structure

```
.claude-plugin/
  marketplace.json          # Claude Code marketplace catalog
plugins/
  jk/
    .claude-plugin/
      plugin.json           # plugin manifest
    skills/
      learn/
        SKILL.md            # name: jk:learn
        references/
        scripts/
      translate/
        SKILL.md            # name: jk:translate
        references/
        evals/
      chat2k/
        SKILL.md            # name: jk:chat2k
        references/
        scripts/
        tests/
        evals/
```

Marketplace containing a single plugin (`jk`). Add more plugins under `plugins/<name>/` and register in `.claude-plugin/marketplace.json`.

## License

MIT © jjuidev
