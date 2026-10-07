#!/usr/bin/env python3
"""Parse a chat transcript (JSONL or markdown) into normalized JSON.

Deterministic parser — zero external deps, zero token overhead.
Output: JSON to stdout with {source, format, messages, session_meta}.

Detects format automatically:
- JSONL: one JSON object per line (Claude Code / Codex / OpenCode format)
- Markdown: a `.md` file with **User:** / **Assistant:** or ## User / ## Assistant headings

Filters out noise:
- Empty messages
- Tool-result-only blocks with no text
- System / meta line types
- "ai-title" / "attachment" / "queue-operation" / "permission-mode" / etc.
"""
import sys
import re
import json
import os
import time
import shlex
import sqlite3
import tempfile
from pathlib import Path

OUT_DIR_ENV = "JK_CHAT2K_OUT_DIR"

# JSONL line types that are NOT messages from the user/assistant conversation
NOISE_TYPES = {
    "last-prompt",
    "mode",
    "permission-mode",
    "queue-operation",
    "file-history-snapshot",
    "ai-title",
    "attachment",
    "system",
}

SYSTEM_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)
COMMAND_NAME_RE = re.compile(r"<command-name>(.*?)</command-name>", re.DOTALL)
COMMAND_ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.DOTALL)
COMMAND_TAGS_RE = re.compile(r"<command-(?:message|name|args)>.*?</command-(?:message|name|args)>", re.DOTALL)


def _clean_text(text: str) -> str:
    """Strip harness-injected noise from a message body.

    - `<system-reminder>` blocks are runtime context, not conversation.
    - Slash-command envelopes collapse to `/name args` so the invocation stays readable.
    """
    text = SYSTEM_REMINDER_RE.sub("", text)
    name = COMMAND_NAME_RE.search(text)
    if name:
        args = COMMAND_ARGS_RE.search(text)
        invocation = f"{name.group(1).strip()} {args.group(1).strip() if args else ''}".strip()
        text = COMMAND_TAGS_RE.sub("", text).strip()
        text = f"{invocation}\n{text}".strip()
    return text.strip()


def parse_jsonl(path: str) -> dict:
    """Parse JSONL transcript from any CLI: Claude Code, Codex, OpenCode.

    Supports two envelope shapes:
      Claude Code:  {"type":"user", "message":{"content":"..."}}
      Codex:        {"type":"event_msg", "payload":{"type":"user_message", "message":"..."}}
    """
    messages = []
    session_id = None
    started_at = None
    last_at = None

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue

            obj_type = obj.get("type", "")
            payload = obj.get("payload", {}) or {}

            # Codex session_meta — capture session_id and cwd
            if obj_type == "session_meta":
                sid = payload.get("session_id") or payload.get("id")
                if sid and not session_id:
                    session_id = sid
                continue

            # Skip noise types — broader set than Claude Code's
            # Harness-injected meta turns (skill bodies, caveats) are not conversation
            if obj.get("isMeta"):
                continue

            if obj_type in NOISE_TYPES:
                # Capture session id from any payload that has it
                sid = obj.get("sessionId") or payload.get("session_id")
                if sid and not session_id:
                    session_id = sid
                continue

            action_type = payload.get("type", "") if obj_type == "event_msg" else obj_type

            # Resolve (role, text) per CLI format
            role, text = None, None
            if obj_type == "user" or action_type == "user_message":
                role = "user"
                if obj_type == "user":
                    text = _extract_text(obj.get("message", {}).get("content", ""))
                else:
                    text = payload.get("message", "")
            elif obj_type == "assistant" or action_type == "agent_message":
                role = "assistant"
                if obj_type == "assistant":
                    text = _extract_text(obj.get("message", {}).get("content", ""))
                else:
                    text = payload.get("message", "")

            if not role or not text:
                continue
            text = _clean_text(str(text))
            if not text:
                continue

            timestamp = obj.get("timestamp") or obj.get("createdAt")
            messages.append(
                {
                    "role": role,
                    "text": text,
                    "timestamp": timestamp,
                }
            )

            if timestamp:
                if not started_at or timestamp < started_at:
                    started_at = timestamp
                if not last_at or timestamp > last_at:
                    last_at = timestamp

    return {
        "source": str(path),
        "format": "jsonl",
        "messages": messages,
        "session_meta": {
            "session_id": session_id,
            "started_at": started_at,
            "last_at": last_at,
            "msg_count": len(messages),
        },
    }


def _extract_text(content) -> str:
    """Extract plain text from a message content field.

    Handles both string content and array-of-blocks content. Only `text` blocks
    are kept: tool_use / tool_result / thinking blocks are execution traces, not
    knowledge, so a tool-only turn yields "" and is dropped by the caller.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "\n".join(p for p in parts if p)
    return str(content)


def parse_markdown(path: str) -> dict:
    """Parse a markdown chat dump.

    Recognized headings:
    - `**User:** ...` / `**Assistant:** ...` (one-line turns)
    - `## User` / `## Assistant` / `## Human` / `## AI` (multi-line turns)
    """
    text = Path(path).read_text(encoding="utf-8")
    messages = []

    # Pattern 1: heading blocks (multi-line)
    heading_pattern = re.compile(
        r"^#{2,4}\s*(?P<role>User|Human|Assistant|AI|Claude)\s*$\n(?P<body>.+?)(?=^#{2,4}\s*(?:User|Human|Assistant|AI|Claude)\s*$|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )

    for m in heading_pattern.finditer(text):
        role = _normalize_role(m.group("role"))
        body = m.group("body").strip()
        if body:
            messages.append({"role": role, "text": body, "timestamp": None})

    if not messages:
        # Pattern 2: inline role-prefixed lines
        # Accepts: **User:** body, **Assistant:** body, User: body, **User:** body
        # The colon may sit inside or outside the bold span.
        inline_pattern = re.compile(
            r"^\*?\*(?P<role>User|Human|Assistant|AI|Claude)\*?\*:\s*(?P<body>.+)$",
            re.IGNORECASE,
        )
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            m = inline_pattern.match(line)
            if not m:
                # Fallback: accept colon-inside-bold variant **User:** body
                m = re.match(
                    r"^\*\*"
                    r"(?P<role>User|Human|Assistant|AI|Claude)"
                    r":\s*\*?\*?\s*"
                    r"(?P<body>.+)$",
                    line,
                    flags=re.IGNORECASE,
                )
            if m:
                role = _normalize_role(m.group("role"))
                messages.append(
                    {"role": role, "text": m.group("body").strip(), "timestamp": None}
                )

    return {
        "source": str(path),
        "format": "markdown",
        "messages": messages,
        "session_meta": {
            "session_id": None,
            "started_at": None,
            "last_at": None,
            "msg_count": len(messages),
        },
    }


def _normalize_role(raw: str) -> str:
    """Map any role alias to 'user' or 'assistant'."""
    r = raw.strip().lower()
    if r in ("user", "human"):
        return "user"
    return "assistant"


def detect_and_parse(path: str) -> dict:
    """Auto-detect format and parse."""
    if not os.path.exists(path):
        return {
            "source": path,
            "format": "unknown",
            "messages": [],
            "session_meta": {
                "session_id": None,
                "started_at": None,
                "last_at": None,
                "msg_count": 0,
            },
            "error": f"file not found: {path}",
        }
    if path.endswith(".jsonl") or path.endswith(".json"):
        return parse_jsonl(path)
    return parse_markdown(path)


def _claude_session_dir(cwd: str) -> Path:
    """Claude Code: ~/.claude/projects/<encoded-cwd>/

    Claude Code encodes every non-alphanumeric char as `-`
    (`/Users/me/.config` → `-Users-me--config`).
    """
    return Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", cwd)


def _claude_project_dir_for(cwd: str) -> Path:
    """Nearest existing Claude Code project dir for `cwd` or one of its parents.

    The shell cwd can drift into a subdirectory of the directory the session was
    started in; the transcript stays under the session's original cwd.
    """
    for candidate in [Path(cwd), *Path(cwd).parents]:
        d = _claude_session_dir(str(candidate))
        if d.is_dir():
            return d
    return _claude_session_dir(cwd)


def _claude_current_session_file() -> Path:
    """Transcript of the running Claude Code session, via CLAUDE_CODE_SESSION_ID."""
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        return None
    matches = list((Path.home() / ".claude" / "projects").glob(f"*/{session_id}.jsonl"))
    return max(matches, key=lambda p: p.stat().st_mtime) if matches else None


def _codex_session_root() -> Path:
    """Codex: ~/.codex/sessions/ (date-based YYYY/MM/DD/rollout-*.jsonl)"""
    return Path.home() / ".codex" / "sessions"


def _opencode_session_dir() -> Path:
    """OpenCode: ~/.local/share/opencode/storage/session/ (SQLite — see note)"""
    return Path.home() / ".local" / "share" / "opencode" / "storage" / "session"


def _cursor_session_dir() -> Path:
    """Cursor: ~/Library/Application Support/Cursor/User/workspaceStorage/
    (per-workspace; messages live in .cursor/chat-{hash}/transactions.json)"""
    return Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage"


# ----------------------------------------------------------------------------
# CLI handler registry
# ----------------------------------------------------------------------------
# Each CLI has a handler that knows how to find (and optionally export) its
# session files. Add a new CLI by adding a handler here — no other code change
# needed.
#
# Types:
#   "jsonl"   — sessions are stored as .jsonl files on disk; list_files() returns them.
#   "sqlite"  — sessions in SQLite DB; export(cwd) writes a JSONL to /tmp and returns it.
#   "generic" — unknown CLI; list_files() scans all known JSONL dirs across CLIs.

CLI_HANDLERS = {
    "claude-code": {
        "type": "jsonl",
        "list_files": lambda cwd: _list_session_files("claude-code", cwd),
    },
    "codex": {
        "type": "jsonl",
        "list_files": lambda cwd: _list_session_files("codex", cwd),
    },
    "opencode": {
        "type": "sqlite",
        "export": lambda cwd: _opencode_export_current(cwd),
    },
    "cursor": {
        "type": "sqlite",
        "export": lambda cwd: _cursor_export_current(cwd),
    },
    "unknown": {
        "type": "generic",
        "list_files": lambda cwd: _list_generic_sessions(cwd),
    },
}


def detect_cli() -> str:
    """Detect which CLI is currently running.

    Returns one of: 'claude-code', 'codex', 'opencode', 'cursor', 'unknown'.

    Detection priority:
      1. Env vars set by the CLI itself (most reliable).
      2. Path-based heuristic (which session dir actually has content).
    """
    if os.environ.get("CLAUDE_CODE_ENTRYPOINT") or os.environ.get("CLAUDECODE"):
        return "claude-code"
    if os.environ.get("CODEX_CLI") or os.environ.get("CODEX_SESSION_ID"):
        return "codex"
    if os.environ.get("OPENCODE_CLI") or os.environ.get("OPENCODE"):
        return "opencode"
    if os.environ.get("CURSOR_TRACE_ID") or os.environ.get("CURSOR_AGENT"):
        return "cursor"
    # Path-based fallback: which session dir has any content?
    cwd = os.getcwd()
    candidates = [
        ("claude-code", _claude_session_dir(cwd)),
        ("codex", _codex_session_root()),
        ("opencode", _opencode_session_dir()),
        ("cursor", _cursor_session_dir()),
    ]
    for name, d in candidates:
        try:
            if d.is_dir() and any(d.iterdir()):
                return name
        except OSError:
            continue
    return "unknown"


def _list_session_files(cli: str, cwd: str) -> list:
    """List candidate session files for a given CLI, filtered to current cwd when possible.

    Returns list of Path. For CLIs that store per-cwd (Claude Code), the filter
    is implicit. For CLIs that store all sessions together (Codex), we examine
    each file's `cwd` field and keep only those matching the current cwd.
    """
    if cli == "claude-code":
        d = _claude_project_dir_for(cwd)
        return list(d.glob("*.jsonl")) if d.is_dir() else []

    if cli == "codex":
        d = _codex_session_root()
        if not d.is_dir():
            return []
        # All *.jsonl under YYYY/MM/DD/ — filter by cwd inside the file
        all_files = list(d.glob("*/*/*/*.jsonl"))
        matches = []
        for p in all_files:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        if i > 5:  # cwd is in first few lines
                            break
                        if '"cwd"' in line and cwd in line:
                            matches.append(p)
                            break
            except OSError:
                continue
        return matches

    if cli == "opencode":
        # OpenCode stores sessions in SQLite (opencode.db). The .jsonl fallback
        # works only if the user has export enabled. Best-effort scan.
        d = _opencode_session_dir()
        if not d.is_dir():
            return []
        return list(d.glob("*.jsonl"))

    if cli == "cursor":
        d = _cursor_session_dir()
        if not d.is_dir():
            return []
        # Cursor uses transactions.json per workspace — look for .cursor symlinks
        candidates = []
        for ws in d.iterdir():
            if not ws.is_dir():
                continue
            for store in (ws / ".cursor").glob("chat-*/transactions.json"):
                candidates.append(store)
            for store in ws.glob("**/transactions.json"):
                if "chat-" in str(store):
                    candidates.append(store)
        return candidates

    return []


def _cursor_export_current(cwd: str) -> str:
    """Export the active Cursor chat session to a temp JSONL.

    Cursor's storage is per-workspace SQLite at:
      ~/Library/Application Support/Cursor/User/workspaceStorage/<ws-hash>/state.vscdb
    Schema varies by version; chat data lives in `ItemTable` keyed by
    `chat-<id>` or `composer.<id>` (blob, JSON-encoded).

    For Linux: ~/.config/Cursor/User/workspaceStorage/
    """
    import platform

    if platform.system() == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage"
    elif platform.system() == "Linux":
        base = Path.home() / ".config" / "Cursor" / "User" / "workspaceStorage"
    else:
        return ""

    if not base.is_dir():
        return ""

    # Find the most-recently-modified state.vscdb (best-effort workspace match)
    candidates = sorted(base.glob("*/state.vscdb"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        return ""

    db_path = candidates[0]
    session_id = f"cursor-{db_path.parent.name}"
    out_path = Path(tempfile.gettempdir()) / f"chat2k-{session_id}.jsonl"

    if out_path.is_file() and (time.time() - out_path.stat().st_mtime) < 60:
        return str(out_path)

    try:
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        # Cursor uses vscode's storageItem format. Look for chat-like keys.
        c.execute(
            "SELECT key, value FROM ItemTable WHERE key LIKE '%chat%' OR key LIKE '%composer%'"
        )
        rows = c.fetchall()
        conn.close()

        with open(out_path, "w", encoding="utf-8") as f:
            for key, value in rows:
                try:
                    data = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    continue
                # Best-effort: extract text from common shapes
                for msg in _cursor_extract_messages(data):
                    f.write(json.dumps(msg, ensure_ascii=False) + "\n")

        return str(out_path) if out_path.stat().st_size > 0 else ""
    except (sqlite3.Error, OSError) as e:
        print(f"chat2k: cursor export failed: {e}", file=sys.stderr)
        return ""


def _cursor_extract_messages(data) -> list:
    """Best-effort extraction of user/assistant message dicts from Cursor's chat blob.

    Returns a list of {"type": "user"|"assistant", "message": {"content": "..."}, "timestamp": "..."}.
    Cursor's schema varies by version; this is a defensive extractor.
    """
    out = []
    try:
        # Try common shapes
        messages = data.get("messages", data.get("conversation", data.get("turns", [])))
        if isinstance(messages, list):
            for m in messages:
                if not isinstance(m, dict):
                    continue
                role = m.get("role") or m.get("type") or m.get("sender", "")
                role = role.lower()
                if role not in ("user", "assistant", "human", "ai"):
                    continue
                role = "user" if role in ("user", "human") else "assistant"
                content = m.get("content") or m.get("text") or m.get("message", "")
                if isinstance(content, list):
                    content = " ".join(
                        c.get("text", "") if isinstance(c, dict) else str(c) for c in content
                    )
                if not content or not str(content).strip():
                    continue
                out.append(
                    {
                        "type": role,
                        "message": {"content": str(content)},
                        "timestamp": m.get("timestamp") or m.get("createdAt"),
                    }
                )
    except (AttributeError, TypeError):
        pass
    return out


def _list_generic_sessions(cwd: str) -> list:
    """Generic fallback: scan ALL known session dirs across all CLIs.

    Used when detect_cli() returns 'unknown'. Best-effort — picks the most
    recent sessions from any known JSONL storage location.
    """
    found = []
    # JSONL dirs
    for cli in ("claude-code", "codex"):
        try:
            found.extend(_list_session_files(cli, cwd))
        except Exception:
            continue
    # SQLite caches (if any pre-exported by a prior run)
    for p in Path(tempfile.gettempdir()).glob("chat2k-*.jsonl"):
        found.append(p)
    return found


def _opencode_export_current(cwd: str) -> str:
    """Detect the active OpenCode session for `cwd` and export to a temp JSONL.

    Returns absolute path to the exported JSONL, or "" if no session found.
    Cached based on session_id + cwd; reused if the file already exists and
    is younger than 60 seconds (so re-runs don't re-query the DB).
    """
    db_path = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
    if not db_path.is_file():
        return ""

    session_id = os.environ.get("OPENCODE_SESSION_ID") or _opencode_active_session_id(
        db_path, cwd
    )
    if not session_id:
        return ""

    out_path = Path(tempfile.gettempdir()) / f"chat2k-opencode-{session_id}.jsonl"
    # Cache: skip re-export if the file is < 60s old
    if out_path.is_file() and (time.time() - out_path.stat().st_mtime) < 60:
        return str(out_path)

    try:
        _opencode_export_to_jsonl(db_path, session_id, out_path)
        return str(out_path)
    except sqlite3.Error as e:
        print(f"chat2k: opencode export failed: {e}", file=sys.stderr)
        return ""


def _opencode_active_session_id(db_path: Path, cwd: str) -> str:
    """Find the most recent OpenCode session matching the current cwd."""
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Most recent session where directory matches cwd
        c.execute(
            "SELECT id FROM session WHERE directory = ? ORDER BY time_created DESC LIMIT 1",
            (cwd,),
        )
        row = c.fetchone()
        if row:
            return row["id"]
        # Fallback: most recent session overall
        c.execute("SELECT id FROM session ORDER BY time_created DESC LIMIT 1")
        row = c.fetchone()
        return row["id"] if row else ""
    except sqlite3.Error:
        return ""
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _opencode_export_to_jsonl(db_path: Path, session_id: str, out_path: Path) -> None:
    """Open the OpenCode SQLite DB and write a JSONL transcript.

    One JSON object per line, matching the Claude Code envelope so the
    existing parser can read it:
      {"type":"user", "message":{"content":"..."}, "timestamp":"..."}
      {"type":"assistant", "message":{"content":"..."}, "timestamp":"..."}
    """
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    # Resolve session_id if not provided
    c.execute(
        "SELECT id, session_id, time_created, data FROM message "
        "WHERE session_id=? ORDER BY time_created ASC",
        (session_id,),
    )
    rows = c.fetchall()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for msg_id, sid, time_created_ms, data_json in rows:
            try:
                d = json.loads(data_json)
            except (json.JSONDecodeError, TypeError):
                continue
            role = d.get("role")
            if role not in ("user", "assistant"):
                continue

            # Fetch parts for this message, in order
            c.execute(
                "SELECT data FROM part WHERE message_id=? ORDER BY time_created ASC",
                (msg_id,),
            )
            part_rows = c.fetchall()
            text_chunks = []
            for (pdata,) in part_rows:
                try:
                    pd = json.loads(pdata)
                except (json.JSONDecodeError, TypeError):
                    continue
                # Concatenate text-type parts; skip metadata parts
                if pd.get("type") == "text" and pd.get("text"):
                    text_chunks.append(pd["text"])
                elif pd.get("type") == "reasoning" and pd.get("text"):
                    # Skip reasoning — not user-facing knowledge
                    continue

            if not text_chunks:
                continue

            # Convert time_created (ms epoch) to ISO 8601
            ts = (
                _epoch_ms_to_iso(time_created_ms) if time_created_ms else None
            )

            obj = {
                "type": role,
                "message": {"content": "\n".join(text_chunks)},
                "timestamp": ts,
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    conn.close()


def _epoch_ms_to_iso(ms) -> str:
    """Convert ms epoch to ISO 8601 UTC string."""
    try:
        from datetime import datetime, timezone

        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )
    except (ValueError, TypeError, OSError):
        return ""


def find_current_session(cli: str = None) -> str:
    """Path of the session currently running, or "" if it cannot be located.

    A user extracting knowledge mid-session wants *this* session, however short.
      - Claude Code: exact match on CLAUDE_CODE_SESSION_ID.
      - SQLite CLIs: exporter already targets the active session.
      - Otherwise: the most recently modified transcript for the cwd (the
        running session writes on every turn).
    """
    cli = cli or detect_cli()
    if cli == "claude-code":
        exact = _claude_current_session_file()
        if exact:
            return str(exact)

    handler = CLI_HANDLERS.get(cli, CLI_HANDLERS["unknown"])
    if handler["type"] == "sqlite":
        return handler["export"](os.getcwd())

    files = []
    for p in handler["list_files"](os.getcwd()):
        try:
            files.append((p.stat().st_mtime, p))
        except OSError:
            continue
    return str(max(files)[1]) if files else ""


def _term_pattern(term: str):
    """Whole-word, case-insensitive matcher that tolerates symbols (c++, next.js)."""
    return re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.IGNORECASE)


def filter_by_terms(messages: list, terms: list, context: int = 2) -> dict:
    """Keep messages mentioning any term, plus `context` neighbours on each side.

    Neighbours keep the question that led to an answer (and the follow-up that
    accepted it) even when they do not repeat the keyword. Each kept message
    carries its original `index` so the agent can reason about adjacency.
    When nothing matches, return an `outline` of user prompts so the agent can
    show the user which topics the session actually covers.
    """
    patterns = [_term_pattern(t) for t in terms]
    hits = [
        i for i, m in enumerate(messages)
        if any(p.search(m["text"]) for p in patterns)
    ]
    keep = sorted({
        j
        for i in hits
        for j in range(max(0, i - context), min(len(messages), i + context + 1))
    })
    result = {
        "messages": [dict(messages[j], index=j) for j in keep],
        "focus": {
            "terms": terms,
            "context": context,
            "hit_count": len(hits),
            "total_messages": len(messages),
        },
    }
    if not hits:
        result["outline"] = [
            {"index": i, "text": m["text"][:160]}
            for i, m in enumerate(messages)
            if m["role"] == "user"
        ]
    return result


def _split_single_arg(raw_args: list) -> list:
    """Re-split a whole argument string passed as one argv item.

    `parse-transcript.py "$ARGUMENTS"` collapses every flag into a single
    token; recover the intended argv. Unbalanced quotes (e.g. "what's") fall
    back to whitespace splitting.
    """
    if len(raw_args) != 1 or not any(ch.isspace() for ch in raw_args[0]):
        return raw_args
    try:
        return shlex.split(raw_args[0])
    except ValueError:
        return raw_args[0].split()


def default_out_dir() -> str:
    """Directory for the default note path: $JK_CHAT2K_OUT_DIR when set, else the working directory."""
    configured = os.environ.get(OUT_DIR_ENV, "").strip()
    return str(Path(configured).expanduser().resolve()) if configured else os.getcwd()


def resolve_args(raw_args: list) -> dict:
    """Resolve CLI flags into a parse spec.

    Any token that is not a flag is part of the free-text focus `query`
    (e.g. `extract knowledge of react`). `--terms` carries the agent-expanded
    keyword list used for deterministic pre-filtering.
    """
    raw_args = _split_single_arg(raw_args)
    spec = {
        "current": False,
        "from_path": None,
        "query": "",
        "terms": [],
        "context": 2,
        "out_path": None,
        "out_dir": default_out_dir(),
        "stdin": False,
        "warnings": [],
    }
    value_flags = {"--from", "--terms", "--context", "--out"}
    query_tokens = []
    i = 0
    while i < len(raw_args):
        a = raw_args[i]
        if a in value_flags:
            i += 1
            value = raw_args[i] if i < len(raw_args) else None
            if a == "--from":
                spec["from_path"] = value
            elif a == "--out":
                spec["out_path"] = value
            elif a == "--terms":
                spec["terms"] = [t.strip() for t in (value or "").split(",") if t.strip()]
            elif a == "--context":
                try:
                    spec["context"] = max(0, int(value))
                except (TypeError, ValueError):
                    spec["warnings"].append(f"invalid --context value: {value!r}")
        elif a == "--current":
            spec["current"] = True
        elif a == "--stdin":
            spec["stdin"] = True
        elif a.startswith("--"):
            spec["warnings"].append(f"unknown flag ignored: {a}")
        else:
            query_tokens.append(a)
        i += 1
    spec["query"] = " ".join(query_tokens)
    return spec


def _empty_result(**extra) -> dict:
    return {
        "source": None,
        "format": None,
        "messages": [],
        "session_meta": {
            "session_id": None,
            "started_at": None,
            "last_at": None,
            "msg_count": 0,
        },
        **extra,
    }


def emit(spec: dict) -> dict:
    """Resolve spec to a parsed transcript dict, focus-filtered when terms are given."""
    result = _load(spec)
    if spec.get("terms") and result.get("messages"):
        result.update(filter_by_terms(result["messages"], spec["terms"], spec["context"]))
    return result


def _load(spec: dict) -> dict:
    """Resolve the transcript source.

    Precedence: --stdin, --from, else the currently running session
    (default; --current is an explicit alias). Past sessions are read via --from.
    """
    if spec["stdin"]:
        # Read all stdin into a temp file, treat as markdown
        raw = sys.stdin.read()
        tmp = "/tmp/chat2k-stdin.md"
        Path(tmp).write_text(raw, encoding="utf-8")
        return parse_markdown(tmp)

    if spec["from_path"]:
        return detect_and_parse(spec["from_path"])

    path = find_current_session()
    if not path:
        return _empty_result(
            source="current",
            error="no current session transcript found; fall back to the in-context conversation",
        )
    return parse_jsonl(path)


if __name__ == "__main__":
    spec = resolve_args(sys.argv[1:])
    result = emit(spec)
    result["spec"] = spec
    print(json.dumps(result, ensure_ascii=False))
