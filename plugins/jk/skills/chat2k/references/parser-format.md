# Parser Format & CLI Quirks

This document defines the JSON contract emitted by `scripts/parse-transcript.py` and the per-CLI format quirks the parser handles.

## Output contract

```jsonc
{
  "source": "/abs/path/to/transcript.jsonl",  // resolved path
  "format": "jsonl" | "markdown",             // detected format
  "messages": [
    {
      "role": "user" | "assistant",
      "text": "full message text, tool blocks rendered as [tool_use: name] / [tool_result: ...]",
      "timestamp": "2026-07-23T09:24:13.123Z" | null
    }
  ],
  "session_meta": {
    "session_id": "uuid" | null,
    "started_at": "iso8601" | null,
    "last_at": "iso8601" | null,
    "msg_count": 42
  },
  "spec": {                                   // resolved CLI flags
    "current": false,
    "from_path": null,
    "marks": ["topic1"],
    "out_path": null,
    "stdin": false
  },
  "error": "optional, only if parse failed",
  "needs_resolution": true,                    // only if no --current / --from given AND ambiguous candidates
  "candidates": [                              // when needs_resolution=true and multiple sessions are roughly equal
    {"path": "/abs/.jsonl", "msg_count": 42, "mtime": 1753256700.0}
  ]
}
```

## Per-CLI format quirks

### Active CLI detection

The parser detects which CLI is running via env vars (priority order):

| CLI | Detection env vars | Session storage | Handler type |
|---|---|---|---|
| `claude-code` | `CLAUDE_CODE_ENTRYPOINT`, `CLAUDECODE` | `~/.claude/projects/<encoded-cwd>/*.jsonl` | JSONL |
| `codex` | `CODEX_CLI`, `CODEX_SESSION_ID` | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | JSONL |
| `opencode` | `OPENCODE_CLI`, `OPENCODE` | `~/.local/share/opencode/opencode.db` (SQLite) | SQLite → auto-export |
| `cursor` | `CURSOR_TRACE_ID`, `CURSOR_AGENT` | `~/Library/Application Support/Cursor/User/workspaceStorage/<ws>/state.vscdb` (SQLite) | SQLite → auto-export |
| `unknown` | none | scans all known JSONL dirs + `/tmp/chat2k-*.jsonl` cache | generic fallback |

### Generic architecture

Adding a new CLI is one entry in `CLI_HANDLERS`:

```python
CLI_HANDLERS["my-cli"] = {
    "type": "jsonl" | "sqlite" | "generic",
    "list_files": lambda cwd: [...],   # for jsonl/generic
    "export": lambda cwd: "/tmp/...",  # for sqlite
}
```

- **`jsonl`**: CLI writes JSONL files to disk; handler returns the list. CLI to add: ~5 lines.
- **`sqlite`**: CLI stores in SQLite; handler exports to a temp JSONL. CLI to add: ~30 lines (query + write loop).
- **`generic`**: fallback that scans all known locations. Catches any new CLI automatically.

### Claude Code (JSONL)

- Path: `~/.claude/projects/<project-encoded>/*.jsonl`
- Project encoding: `/Users/foo/Bar` → `-Users-foo-Bar`
- `type` field: `user`, `assistant`, `system`, `ai-title`, `attachment`, `queue-operation`, `permission-mode`, `file-history-snapshot`, `last-prompt`, `mode`
- `message.content` is **either** a string OR an array of content blocks (`text`, `tool_use`, `tool_result`).
- `--current` (and bare `/jk:chat2k`) triggers **smart auto-resolve** via `find_best_session()`:
  - Lists all `.jsonl` in the project session dir.
  - Quick-counts user/assistant messages per file.
  - Drops files below `min_messages=5` (treats brand-new empty sessions as "not yet started").
  - Ranks by `(msg_count desc, mtime desc)`.
  - If top has ≥ 2× the runner-up's count → auto-resolve (no prompt).
  - Otherwise → returns `candidates[]` for the agent to present a menu.

### Codex (JSONL — event_msg envelope)

- Path: `~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<session-id>.jsonl`
- No per-cwd dir — sessions are date-bucketed. The parser reads the first few lines of each file and filters by `payload.cwd` matching the current cwd.
- User message: `{"type":"event_msg","payload":{"type":"user_message","message":"..."}}`
- Assistant message: `{"type":"event_msg","payload":{"type":"agent_message","message":"..."}}`
- Session meta: `{"type":"session_meta","payload":{"session_id":"...","cwd":"..."}}`
- Noise types dropped: `token_count`, `turn_context`, `task_started`, `task_complete`, `response_item`, `world_state`, `thread_settings_applied`, `managed`, `restricted`, `special`, `path`, `reasoning`.

### OpenCode

- Primary storage is SQLite (`~/.local/share/opencode/opencode.db`).
- **`/jk:chat2k` auto-handles OpenCode** — no manual export needed. The parser:
  1. Opens the SQLite DB.
  2. Looks up the active session matching current cwd (`SESSION.directory` = `pwd`), falling back to most-recent overall.
  3. Joins `message` + `part` tables, extracts user/assistant text (skips `reasoning` parts).
  4. Writes a JSONL transcript to `/tmp/chat2k-opencode-<session-id>.jsonl` (cached for 60s).
  5. Parses that file via the standard Claude Code envelope.
- Schema: `session(id, directory, title, time_created)`, `message(id, session_id, data:JSON{role}), time_created_ms`, `part(message_id, data:JSON{type, text})`. Reasoning parts are filtered out.

### Cursor Chat

- Sessions live in `~/Library/Application Support/Cursor/User/workspaceStorage/<ws-id>/.cursor/chat-<hash>/transactions.json`.
- Format is JSON (not JSONL); each transaction is a JSON object with `role` and `content`. The parser handles JSON-array files via the same `parse_jsonl` path (one object per line is the assumed format).
- For best results, run Cursor's built-in "Export chat" to get a `.jsonl`/`.md` file, then `--from` it.

### Plain markdown chat dumps

- Recognized: `**User:** ...` / `**Assistant:** ...` (single-line turns) AND `## User` / `## Assistant` / `## Human` / `## AI` (multi-line blocks).
- Unknown heading formats → falls back to scanning each line for `User:` / `Assistant:` prefixes.

## What gets dropped

| Pattern | Why |
|---|---|
| Empty `message.content` | No info to extract |
| `type` ∈ noise set (`system`, `ai-title`, `attachment`, etc.) | Not conversation |
| Tool-result-only blocks with no surrounding text | Tool chatter, not knowledge |
| `permission-mode`, `mode`, `queue-operation` | Runtime metadata |
| `[tool_use: bash]` / `[tool_result: ...]` placeholders kept but flagged | Visible in markdown so the LLM can ignore them when extracting topics |

## What gets normalized

- All whitespace runs → single space within a line.
- Surrounding blank lines stripped.
- Content blocks (text + tool) joined with `\n` so a single message keeps its structure for downstream LLM analysis.
- Timestamps kept as ISO8601 strings (no timezone coercion) — Claude Code uses UTC ISO with `Z`.
