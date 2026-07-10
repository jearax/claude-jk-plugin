# claude-ckc-plugin

**Claude Kit Custom (`ckc`)** — companion skills for [claudekit](https://github.com/anthropics/claude-code) under the `/ckc:*` namespace.

**Dual distribution**: Claude Code plugin marketplace **+** [`npx skills`](https://github.com/vercel-labs/skills) CLI (works with OpenCode, Codex, Cursor, and 50+ agents).

Maintained by [jjuidev](https://github.com/jearax).

## Prerequisites

- Claude Code ≥ 2.x (Plugins GA) **or** any agent supported by `npx skills`
- **claudekit** installed — `ckc` skills depend on shared assets (`docs-seeker`, `html-anything`, `ai-multimodal`) and the shared Python venv at `~/.claude/skills/.venv/bin/python3`

## Install

### A. Claude Code (plugin marketplace)

```bash
# From GitHub (after publish)
/plugin marketplace add jearax/claude-ckc-plugin
/plugin install ckc@ckc-marketplace

# Local development
/plugin marketplace add /Users/tandm/Documents/jjuidev/npm/ai-skills/claude-ckc-plugin
/plugin install ckc@ckc-marketplace
```

Update flow:

```bash
/plugin marketplace update ckc-marketplace
/plugin update ckc
```

### B. OpenCode / Codex / Cursor / others (via `npx skills`)

```bash
# From GitHub (after publish)
npx skills add jearax/claude-ckc-plugin -a opencode -g

# Local development
npx skills add /Users/tandm/Documents/jjuidev/npm/ai-skills/claude-ckc-plugin -a opencode -g
```

Install targets (global mode):

| Agent | Path |
|---|---|
| OpenCode | `~/.agents/skills/ckc-learn/` |
| Claude Code | `~/.claude/skills/ckc-learn/` |
| Codex | `~/.codex/skills/ckc-learn/` |
| Cursor | `~/.cursor/skills/ckc-learn/` |

Default mode is `copy`. To re-install after updates, re-run the command.

## Skills included

| Skill | Description |
|---|---|
| `ckc:learn` | Learn a library/framework via structured research. Modes: `quick`, `full`, `detail`, `overview`, `cheatsheet`. Supports URL input and `--md`/`--html` output. |
| `ckc:dev-translate` | Context-aware bilingual translator (EN/mixed → Vietnamese) for dev/IT content — error messages, tickets, docs, PRs. Verifies uncertain IT terms against official docs. Output: parallel EN↔VI chunks, console-readable. |

## Usage examples

```text
/ckc:learn nextjs
/ckc:learn full tanstack-router
/ckc:learn cheatsheet zod
/ckc:learn https://orm.drizzle.team/docs/overview

/ckc:dev-translate Fix the flaky test in auth.spec.ts. The JWT expires before the assertion runs.
```

## Add a new skill

1. Create `plugins/ckc/skills/<skill-name>/SKILL.md` with YAML frontmatter (`name:` and `description:` required).
2. Drop assets into `plugins/ckc/skills/<skill-name>/references/`, `scripts/`, etc.
3. **Reference assets with relative paths** (e.g. `references/foo.md`, `scripts/bar.py`) — works in both Claude Code plugin runtime and `npx skills` installs. Avoid `${CLAUDE_PLUGIN_ROOT}` for cross-tool compatibility.
4. Bump `version` in `plugins/ckc/.claude-plugin/plugin.json`.
5. Commit & push.

## Structure

```
.claude-plugin/
  marketplace.json          # Claude Code marketplace catalog
plugins/
  ckc/
    .claude-plugin/
      plugin.json           # plugin manifest
    skills/
      learn/
        SKILL.md            # name: ckc:learn
        references/
        scripts/
      dev-translate/
        SKILL.md            # name: ckc:dev-translate
        references/
        evals/
```

Marketplace containing a single plugin (`ckc`). Add more plugins under `plugins/<name>/` and register in `.claude-plugin/marketplace.json`.

## License

MIT © jjuidev
