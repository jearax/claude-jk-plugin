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
| `jk:learn` | Learn a library/framework/concept via structured research. Each mode answers one question: `overview` (default — what it is, should I use it), `usage` (how to use it), `workflow` (one real task end to end), `internals` (how it works inside), `cheatsheet` (API lookup), `docs` (official reading map). `--eli<N>` adjusts any mode to reader level N; alone, it explains the topic from zero. Supports URL input and `--md`/`--html` output. |
| `jk:translate` | Context-aware bilingual translator (EN/mixed → Vietnamese) for dev/IT content — error messages, tickets, docs, PRs. Verifies uncertain IT terms against official docs. Output: parallel EN↔VI chunks, console-readable. |
| `jk:chat2k` | Chat-to-Knowledge — turn the running chat session (or a transcript from claude, opencode, codex, cursor) into a beautiful Markdown note. Give a free-text focus to extract just one topic from a long multi-topic session; without one it keeps *decided* knowledge (comparisons, pros/cons, use cases, decisions, verified links). Filters noise, never dumps transcripts. |
| `jk:leetcode-problem` | LeetCode practice scaffolder — research a problem by id/slug/URL, generate empty `solve`/`solve2`/… stubs with rich doc comments (summary, happy-case example, complexity ladder, keywords) + failing tests — identically for every language app in the practice repo. Remembers the active problem + chat language for the session. `--explain` = adaptive guided discussion until the user understands, then offers to scaffold. |
| `jk:prune-comments` | Remove junk code comments and tighten the valuable ones without touching code. Tiered rules: tool directives always kept → `--keep`/`--junk` → your `junk-catalog.md` → anti-slop baseline. Runs on pending git changes (or `--full`) behind a temporary checkpoint commit, then asks Accept/Reject. |

## Usage examples

```text
/jk:learn nextjs
/jk:learn usage tanstack-router
/jk:learn workflow auth with better-auth
/jk:learn internals react hooks
/jk:learn cheatsheet zod
/jk:learn docs nextjs
/jk:learn event loop --eli5
/jk:learn internals tcp --eli15
/jk:learn usage https://orm.drizzle.team/docs/overview

/jk:translate Fix the flaky test in auth.spec.ts. The JWT expires before the assertion runs.

/jk:chat2k
/jk:chat2k extract knowledge of react
/jk:chat2k auth flow --from /path/to/session.jsonl --out ~/notes/auth-review.md

/jk:leetcode-problem 217
/jk:leetcode-problem two-sum
/jk:leetcode-problem --explain

/jk:prune-comments
/jk:prune-comments chỉ dọn src/auth, bỏ qua test
/jk:prune-comments --full --junk "section banners in tests" --keep "Vietnamese business-rule comments"
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
      leetcode-problem/
        SKILL.md            # name: jk:leetcode-problem
        references/
        scripts/
      prune-comments/
        SKILL.md            # name: jk:prune-comments
        references/         # keep-list, junk-catalog (yours), antislop, tighten-rules, patterns.json
        scripts/
        tests/
        evals/
```

Marketplace containing a single plugin (`jk`). Add more plugins under `plugins/<name>/` and register in `.claude-plugin/marketplace.json`.

## License

MIT © jjuidev

`jk:prune-comments` adapts patterns from [miqdadbadjuber/anti-slop](https://github.com/miqdadbadjuber/anti-slop) (MIT).
