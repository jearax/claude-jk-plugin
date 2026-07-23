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
import sqlite3
import subprocess
import tempfile
from pathlib import Path

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

            if not role or not text or not str(text).strip():
                continue

            timestamp = obj.get("timestamp") or obj.get("createdAt")
            messages.append(
                {
                    "role": role,
                    "text": str(text).strip(),
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

    Handles both string content and array-of-blocks content (text/tool_use/tool_result).
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    name = block.get("name", "tool")
                    parts.append(f"[tool_use: {name}]")
                elif block.get("type") == "tool_result":
                    rc = block.get("content", "")
                    if isinstance(rc, list):
                        rc = " ".join(
                            b.get("text", "") for b in rc if isinstance(b, dict)
                        )
                    parts.append(f"[tool_result: {str(rc)[:200]}]")
        return "\n".join(parts)
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


def _quick_count(path: Path) -> int:
    """Count user/assistant messages in a jsonl without full parsing.

    Cheap heuristic to rank candidates by content richness.
    Matches both `"type":"user"` and `"type": "user"` (with space).
    """
    try:
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                # Cheap string check — no JSON parse needed
                if '"type": "user"' in line or '"type": "assistant"' in line:
                    count += 1
        return count
    except OSError:
        return 0


def _claude_session_dir(cwd: str) -> Path:
    """Claude Code: ~/.claude/projects/<encoded-cwd>/"""
    project_dir = cwd.replace("/", "-")
    if not project_dir.startswith("-"):
        project_dir = "-" + project_dir
    return Path.home() / ".claude" / "projects" / project_dir


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
        d = _claude_session_dir(cwd)
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


def find_best_session(
    min_messages: int = 5, top_n: int = 3, session_dir: Path = None, cli: str = None
) -> dict:
    """Pick the best session transcript to extract from across all CLIs.

    Returns {"path": str, "candidates": [(path, msg_count, mtime), ...], "cli": str}.

    Strategy:
      1. Detect the running CLI (env vars → fallback to dir scan).
      2. Look up the CLI's handler in `CLI_HANDLERS`.
      3. If the handler is SQLite-based → auto-export current session to a
         temp JSONL file, then use that.
      4. If the handler is JSONL-native → list existing files.
      5. If the CLI is unknown → fall back to generic scan of common dirs.
      6. Quick-count user/assistant messages per file.
      7. Drop files below `min_messages` (treat as empty / noise).
      8. Rank by (msg_count desc, mtime desc).
      9. If the top candidate has ≥ 2× the count of the runner-up → auto-resolve.
         Otherwise → return the top `top_n` so the caller can present a menu.

    The "current session" (currently being written) may show up as the
    most-recently-modified file but with very few messages — we skip
    those by the `min_messages` threshold.

    Args:
      session_dir: override for tests. Defaults to scanning the active CLI's
        session storage for the current cwd.
      cli: override for tests. Defaults to auto-detect.
    """
    cwd = os.getcwd()
    if cli is None:
        cli = detect_cli()

    # Single-dir override (legacy test mode)
    if session_dir is not None:
        files = list(session_dir.glob("*.jsonl")) if session_dir.is_dir() else []
        return _score_candidates(files, min_messages, top_n) | {"cli": cli}

    # Look up handler for this CLI
    handler = CLI_HANDLERS.get(cli, CLI_HANDLERS["unknown"])
    handler_type = handler["type"]

    # SQLite-based CLIs: auto-export current session to temp JSONL.
    if handler_type == "sqlite":
        exporter = handler["export"]
        exported = exporter(cwd)
        if exported:
            return {
                "path": exported,
                "candidates": [(Path(exported), 0, 0)],
                "cli": cli,
            }
        return {"path": "", "candidates": [], "cli": cli}

    # JSONL-native CLIs: list existing files
    if handler_type == "jsonl":
        files = handler["list_files"](cwd)
        if not files:
            return {"path": "", "candidates": [], "cli": cli}
        return _score_candidates(files, min_messages, top_n) | {"cli": cli}

    # Generic fallback: scan ALL known JSONL dirs + SQLite caches
    if handler_type == "generic":
        files = handler["list_files"](cwd)
        if not files:
            return {"path": "", "candidates": [], "cli": cli}
        return _score_candidates(files, min_messages, top_n) | {"cli": cli}

    return {"path": "", "candidates": [], "cli": cli}


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


def _score_candidates(files: list, min_messages: int, top_n: int) -> dict:
    """Score a list of session files; return clear winner or shortlist."""
    if not files:
        return {"path": "", "candidates": []}

    scored = []
    for p in files:
        msg_count = _quick_count(p)
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        scored.append((p, msg_count, mtime))

    # Filter out near-empty sessions
    rich = [s for s in scored if s[1] >= min_messages]
    if not rich:
        # Fall back to most-recently-modified, even if short
        scored.sort(key=lambda x: x[2], reverse=True)
        return {"path": str(scored[0][0]), "candidates": scored[:top_n]}

    # Rank by (msg_count desc, mtime desc)
    rich.sort(key=lambda x: (x[1], x[2]), reverse=True)
    top, runner = rich[0], rich[1] if len(rich) > 1 else None

    # If runner-up is close in count, surface as menu
    if runner and top[1] < runner[1] * 2:
        return {"path": "", "candidates": rich[:top_n]}

    # Clear winner — auto-resolve
    return {"path": str(top[0]), "candidates": rich[:top_n]}


def find_current_session() -> str:
    """Backward-compat wrapper: best session path, or empty string."""
    return find_best_session()["path"]


def resolve_args(raw_args: list) -> dict:
    """Resolve CLI flags into a parse spec."""
    spec = {
        "current": False,
        "from_path": None,
        "marks": [],
        "out_path": None,
        "stdin": False,
    }
    i = 0
    while i < len(raw_args):
        a = raw_args[i]
        if a == "--current":
            spec["current"] = True
        elif a == "--from":
            i += 1
            spec["from_path"] = raw_args[i] if i < len(raw_args) else None
        elif a == "--marks":
            i += 1
            marks = raw_args[i] if i < len(raw_args) else ""
            spec["marks"] = [m.strip() for m in marks.split(",") if m.strip()]
        elif a == "--out":
            i += 1
            spec["out_path"] = raw_args[i] if i < len(raw_args) else None
        elif a == "--stdin":
            spec["stdin"] = True
        i += 1
    return spec


def emit(spec: dict) -> dict:
    """Resolve spec to a parsed transcript dict."""
    if spec["stdin"]:
        # Read all stdin into a temp file, treat as markdown
        raw = sys.stdin.read()
        tmp = "/tmp/chat2k-stdin.md"
        Path(tmp).write_text(raw, encoding="utf-8")
        return parse_markdown(tmp)

    if spec["from_path"]:
        return detect_and_parse(spec["from_path"])

    if spec["current"]:
        path = find_current_session()
        if not path:
            return {
                "source": "current",
                "format": "unknown",
                "messages": [],
                "session_meta": {
                    "session_id": None,
                    "started_at": None,
                    "last_at": None,
                    "msg_count": 0,
                },
                "error": "no current session found",
            }
        return parse_jsonl(path)

    # No flags — auto-resolve via find_best_session().
    # Returns either a clear winner or a list of candidates for the agent to ask.
    best = find_best_session()
    if best["path"]:
        return parse_jsonl(best["path"])
    if best["candidates"]:
        # Ambiguous — ask the user
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
            "needs_resolution": True,
            "candidates": [
                {
                    "path": str(c[0]),
                    "msg_count": c[1],
                    "mtime": c[2],
                }
                for c in best["candidates"]
            ],
        }

    # Truly nothing — empty resolution
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
        "needs_resolution": True,
    }


if __name__ == "__main__":
    spec = resolve_args(sys.argv[1:])
    result = emit(spec)
    result["spec"] = spec
    print(json.dumps(result, ensure_ascii=False))
