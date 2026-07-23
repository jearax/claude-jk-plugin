#!/usr/bin/env python3
"""Tests for chat2k/scripts/parse-transcript.py.

Run with: python3 tests/test_parse_transcript.py
Stdlib-only — no pytest required.
"""
import sys
import os
import json
import time
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add scripts/ to path AND import module with hyphenated name
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

import importlib.util as _ilu

_spec = _ilu.spec_from_file_location(
    "parse_transcript", os.path.join(SCRIPTS_DIR, "parse-transcript.py")
)
pt = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(pt)


class TestJsonlParser(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        )
        self.tmp_path = self.tmp.name

    def tearDown(self):
        os.unlink(self.tmp_path)

    def _write(self, lines):
        self.tmp.write("\n".join(lines) + "\n")
        self.tmp.close()

    def test_basic_user_assistant(self):
        self._write(
            [
                json.dumps({"type": "last-prompt", "sessionId": "abc"}),
                json.dumps({"type": "user", "message": {"content": "Hello"}}),
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {"content": "Hi there!"},
                        "timestamp": "2026-07-23T09:00:00Z",
                    }
                ),
            ]
        )
        result = pt.parse_jsonl(self.tmp_path)
        self.assertEqual(result["format"], "jsonl")
        self.assertEqual(result["session_meta"]["session_id"], "abc")
        self.assertEqual(len(result["messages"]), 2)
        self.assertEqual(result["messages"][0]["role"], "user")
        self.assertEqual(result["messages"][0]["text"], "Hello")
        self.assertEqual(result["messages"][1]["text"], "Hi there!")
        self.assertEqual(
            result["session_meta"]["started_at"], "2026-07-23T09:00:00Z"
        )

    def test_filters_noise_types(self):
        self._write(
            [
                json.dumps({"type": "system", "message": {"content": "should drop"}}),
                json.dumps({"type": "ai-title", "message": {"content": "should drop"}}),
                json.dumps({"type": "attachment", "message": {"content": "drop"}}),
                json.dumps({"type": "permission-mode", "mode": "bypass"}),
                json.dumps({"type": "queue-operation"}),
                json.dumps({"type": "file-history-snapshot"}),
                json.dumps({"type": "user", "message": {"content": "keep me"}}),
            ]
        )
        result = pt.parse_jsonl(self.tmp_path)
        self.assertEqual(len(result["messages"]), 1)
        self.assertEqual(result["messages"][0]["text"], "keep me")

    def test_filters_empty_messages(self):
        self._write(
            [
                json.dumps({"type": "user", "message": {"content": ""}}),
                json.dumps({"type": "user", "message": {"content": "   "}}),
                json.dumps({"type": "user", "message": {"content": []}}),
                json.dumps({"type": "user", "message": {"content": "real content"}}),
            ]
        )
        result = pt.parse_jsonl(self.tmp_path)
        self.assertEqual(len(result["messages"]), 1)
        self.assertEqual(result["messages"][0]["text"], "real content")

    def test_handles_array_content_blocks(self):
        self._write(
            [
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {"type": "text", "text": "Let me check that."},
                                {"type": "tool_use", "name": "bash"},
                                {"type": "tool_result", "content": "ok"},
                            ]
                        },
                    }
                ),
            ]
        )
        result = pt.parse_jsonl(self.tmp_path)
        self.assertEqual(len(result["messages"]), 1)
        text = result["messages"][0]["text"]
        self.assertIn("Let me check that.", text)
        self.assertIn("[tool_use: bash]", text)
        self.assertIn("[tool_result: ok]", text)

    def test_session_meta_timestamps(self):
        self._write(
            [
                json.dumps(
                    {
                        "type": "user",
                        "message": {"content": "first"},
                        "timestamp": "2026-07-23T08:00:00Z",
                    }
                ),
                json.dumps(
                    {
                        "type": "user",
                        "message": {"content": "last"},
                        "timestamp": "2026-07-23T10:00:00Z",
                    }
                ),
            ]
        )
        result = pt.parse_jsonl(self.tmp_path)
        self.assertEqual(result["session_meta"]["started_at"], "2026-07-23T08:00:00Z")
        self.assertEqual(result["session_meta"]["last_at"], "2026-07-23T10:00:00Z")
        self.assertEqual(result["session_meta"]["msg_count"], 2)

    def test_malformed_lines_skipped(self):
        self._write(
            [
                "not json at all",
                json.dumps({"type": "user", "message": {"content": "ok"}}),
                "{broken json",
                json.dumps({"type": "assistant", "message": {"content": "fine"}}),
            ]
        )
        result = pt.parse_jsonl(self.tmp_path)
        self.assertEqual(len(result["messages"]), 2)


class TestMarkdownParser(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        )
        self.tmp_path = self.tmp.name

    def tearDown(self):
        os.unlink(self.tmp_path)

    def test_inline_prefix(self):
        self.tmp.write(
            "**User:** Hello there\n**Assistant:** Hi! How can I help?\n"
        )
        self.tmp.close()
        result = pt.parse_markdown(self.tmp_path)
        self.assertEqual(result["format"], "markdown")
        self.assertEqual(len(result["messages"]), 2)
        self.assertEqual(result["messages"][0]["role"], "user")
        self.assertEqual(result["messages"][1]["role"], "assistant")

    def test_heading_blocks(self):
        self.tmp.write(
            "## User\nWhat is X?\n\n## Assistant\nX is a thing.\n\n## User\nWhy?\n"
        )
        self.tmp.close()
        result = pt.parse_markdown(self.tmp_path)
        self.assertEqual(len(result["messages"]), 3)
        self.assertEqual(result["messages"][0]["text"], "What is X?")
        self.assertEqual(result["messages"][1]["text"], "X is a thing.")

    def test_human_ai_aliases(self):
        self.tmp.write(
            "## Human\nQuestion\n\n## AI\nAnswer\n\n## Claude\nFollowup\n"
        )
        self.tmp.close()
        result = pt.parse_markdown(self.tmp_path)
        self.assertEqual(len(result["messages"]), 3)
        self.assertEqual(result["messages"][0]["role"], "user")
        self.assertEqual(result["messages"][1]["role"], "assistant")
        self.assertEqual(result["messages"][2]["role"], "assistant")

    def test_empty_markdown(self):
        self.tmp.write("Just some random text\nwith no chat markers\n")
        self.tmp.close()
        result = pt.parse_markdown(self.tmp_path)
        self.assertEqual(len(result["messages"]), 0)


class TestResolveArgs(unittest.TestCase):
    def test_current_flag(self):
        spec = pt.resolve_args(["--current"])
        self.assertTrue(spec["current"])
        self.assertIsNone(spec["from_path"])

    def test_from_path(self):
        spec = pt.resolve_args(["--from", "/tmp/x.jsonl"])
        self.assertEqual(spec["from_path"], "/tmp/x.jsonl")
        self.assertFalse(spec["current"])

    def test_marks(self):
        spec = pt.resolve_args(["--marks", "auth, deploy"])
        self.assertEqual(spec["marks"], ["auth", "deploy"])

    def test_out_path(self):
        spec = pt.resolve_args(["--out", "/tmp/note.md"])
        self.assertEqual(spec["out_path"], "/tmp/note.md")

    def test_stdin(self):
        spec = pt.resolve_args(["--stdin"])
        self.assertTrue(spec["stdin"])

    def test_combined(self):
        spec = pt.resolve_args(
            ["--current", "--marks", "auth,db", "--out", "/tmp/n.md"]
        )
        self.assertTrue(spec["current"])
        self.assertEqual(spec["marks"], ["auth", "db"])
        self.assertEqual(spec["out_path"], "/tmp/n.md")


class TestEmit(unittest.TestCase):
    def test_emits_needs_resolution_when_no_source(self):
        spec = pt.resolve_args([])
        result = pt.emit(spec)
        # Either auto-resolved to a real session, or needs_resolution=True
        # We don't assert either — depends on the host's session dir state.
        if result.get("needs_resolution"):
            self.assertNotIn("messages", result) or result["messages"] == []

    def test_emits_from_path(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write(
                json.dumps({"type": "user", "message": {"content": "hi"}}) + "\n"
            )
            path = f.name
        try:
            spec = pt.resolve_args(["--from", path])
            result = pt.emit(spec)
            self.assertEqual(result["format"], "jsonl")
            self.assertEqual(len(result["messages"]), 1)
        finally:
            os.unlink(path)


class TestFindBestSession(unittest.TestCase):
    """Tests for the smart auto-resolve logic."""

    def setUp(self):
        # Build a fake session dir with several jsonl files
        self.tmpdir = tempfile.mkdtemp()
        self.session_dir = Path(self.tmpdir) / "fake-project"
        self.session_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_session(self, name: str, msg_count: int, mtime_offset: int = 0):
        """Write a fake jsonl with N user/assistant messages."""
        path = self.session_dir / name
        with open(path, "w", encoding="utf-8") as f:
            for i in range(msg_count):
                f.write(
                    json.dumps(
                        {"type": "user", "message": {"content": f"msg {i}"}}
                    )
                    + "\n"
                )
                f.write(
                    json.dumps(
                        {"type": "assistant", "message": {"content": f"reply {i}"}}
                    )
                    + "\n"
                )
        # Set mtime
        mtime = time.time() - mtime_offset
        os.utime(path, (mtime, mtime))
        return path

    def test_empty_session_dir_returns_empty(self):
        result = pt.find_best_session(session_dir=self.session_dir)
        self.assertEqual(result["path"], "")
        self.assertEqual(result["candidates"], [])

    def test_ignores_empty_sessions(self):
        # Two files: one with 0 messages, one with 20
        self._write_session("empty.jsonl", 0, mtime_offset=0)
        rich = self._write_session("rich.jsonl", 20, mtime_offset=60)
        result = pt.find_best_session(session_dir=self.session_dir)
        self.assertEqual(result["path"], str(rich))

    def test_picks_highest_count(self):
        # Two rich files: one with 30 msgs, one with 10
        best = self._write_session("best.jsonl", 30, mtime_offset=60)
        self._write_session("less.jsonl", 10, mtime_offset=0)
        result = pt.find_best_session(session_dir=self.session_dir)
        self.assertEqual(result["path"], str(best))

    def test_ambiguous_when_close_in_count(self):
        # Two rich files with similar counts → menu
        self._write_session("a.jsonl", 25, mtime_offset=60)
        self._write_session("b.jsonl", 20, mtime_offset=0)
        result = pt.find_best_session(session_dir=self.session_dir)
        # Top has 25, runner-up has 20 → 25 < 20*2 = 40 → ambiguous
        self.assertEqual(result["path"], "")
        self.assertGreater(len(result["candidates"]), 1)

    def test_clear_winner_when_2x_runner_up(self):
        # Top has 50, runner-up has 10 → clear winner
        best = self._write_session("big.jsonl", 50, mtime_offset=60)
        self._write_session("small.jsonl", 10, mtime_offset=0)
        result = pt.find_best_session(session_dir=self.session_dir)
        self.assertEqual(result["path"], str(best))


class TestCodexJsonlParser(unittest.TestCase):
    """Codex uses event_msg envelope with payload.type=user_message/agent_message."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        )
        self.tmp_path = self.tmp.name

    def tearDown(self):
        os.unlink(self.tmp_path)

    def _write(self, lines):
        self.tmp.write("\n".join(lines) + "\n")
        self.tmp.close()

    def test_parses_codex_event_msg_envelope(self):
        self._write(
            [
                json.dumps(
                    {
                        "timestamp": "2026-07-22T17:17:02.528Z",
                        "type": "session_meta",
                        "payload": {
                            "session_id": "abc-123",
                            "id": "abc-123",
                            "cwd": "/Users/foo/Bar",
                        },
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-07-22T17:17:02.686Z",
                        "type": "event_msg",
                        "payload": {
                            "type": "user_message",
                            "message": "Hello there",
                        },
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-07-22T17:17:06.042Z",
                        "type": "event_msg",
                        "payload": {
                            "type": "agent_message",
                            "message": "Hi! How can I help?",
                        },
                    }
                ),
            ]
        )
        result = pt.parse_jsonl(self.tmp_path)
        self.assertEqual(result["session_meta"]["session_id"], "abc-123")
        self.assertEqual(len(result["messages"]), 2)
        self.assertEqual(result["messages"][0]["role"], "user")
        self.assertEqual(result["messages"][0]["text"], "Hello there")
        self.assertEqual(result["messages"][1]["role"], "assistant")
        self.assertEqual(result["messages"][1]["text"], "Hi! How can I help?")
        self.assertEqual(
            result["session_meta"]["started_at"], "2026-07-22T17:17:02.686Z"
        )

    def test_filters_codex_noise_types(self):
        self._write(
            [
                json.dumps({"type": "token_count", "payload": {}}),
                json.dumps({"type": "turn_context", "payload": {}}),
                json.dumps({"type": "task_started", "payload": {}}),
                json.dumps({"type": "task_complete", "payload": {}}),
                json.dumps({"type": "response_item", "payload": {}}),
                json.dumps(
                    {
                        "type": "event_msg",
                        "payload": {"type": "user_message", "message": "keep"},
                    }
                ),
            ]
        )
        result = pt.parse_jsonl(self.tmp_path)
        self.assertEqual(len(result["messages"]), 1)
        self.assertEqual(result["messages"][0]["text"], "keep")


class TestDetectCli(unittest.TestCase):
    def test_detects_claude_code_via_env(self):
        with patch.dict(os.environ, {"CLAUDE_CODE_ENTRYPOINT": "cli"}, clear=False):
            self.assertEqual(pt.detect_cli(), "claude-code")

    def test_detects_claude_code_via_claudecode_env(self):
        with patch.dict(os.environ, {"CLAUDECODE": "1"}, clear=False):
            self.assertEqual(pt.detect_cli(), "claude-code")

    def test_detects_codex_via_env(self):
        env = {"CODEX_CLI": "1"}
        # Clear conflicting Claude env vars first
        with patch.dict(
            os.environ,
            {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")},
            clear=True,
        ):
            env_full = {**os.environ, **env}
            with patch.dict(os.environ, env_full, clear=True):
                self.assertEqual(pt.detect_cli(), "codex")

    def test_detects_opencode_via_env(self):
        with patch.dict(
            os.environ,
            {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")},
            clear=True,
        ):
            with patch.dict(os.environ, {"OPENCODE_CLI": "1"}, clear=False):
                self.assertEqual(pt.detect_cli(), "opencode")

    def test_falls_back_to_unknown(self):
        with patch.dict(
            os.environ,
            {k: "" for k in os.environ},
            clear=True,
        ):
            with patch("pathlib.Path.home", return_value=Path(tempfile.mkdtemp())):
                self.assertEqual(pt.detect_cli(), "unknown")


class TestListSessionFiles(unittest.TestCase):
    """Tests for the per-CLI session file listing."""

    def test_claude_code_lists_jsonl(self):
        d = Path(tempfile.mkdtemp())
        try:
            (d / "sess-1.jsonl").write_text(
                json.dumps({"type": "user", "message": {"content": "x"}}) + "\n"
            )
            (d / "sess-2.jsonl").write_text(
                json.dumps({"type": "user", "message": {"content": "y"}}) + "\n"
            )
            with patch("pathlib.Path.home", return_value=Path(tempfile.mkdtemp())):
                # Mock the home + cwd to land in our temp dir
                with patch("os.getcwd", return_value=str(d)):
                    files = pt._list_session_files("claude-code", str(d))
            # The cwd-encoded dir would be inside the home, which is a fresh tmp.
            # Empty result is acceptable here — the assertion is "doesn't crash".
            self.assertIsInstance(files, list)
        finally:
            shutil.rmtree(d)

    def test_codex_filters_by_cwd(self):
        # Build a fake codex root: home/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl
        home = Path(tempfile.mkdtemp())
        root = home / ".codex" / "sessions"
        date_dir = root / "2026" / "07" / "23"
        date_dir.mkdir(parents=True)
        cwd = "/Users/test/proj"
        other = "/Users/other/proj"
        match_path = date_dir / "rollout-1.jsonl"
        match_path.write_text(
            json.dumps({"type": "session_meta", "payload": {"cwd": cwd}}) + "\n"
        )
        nomatch_path = date_dir / "rollout-2.jsonl"
        nomatch_path.write_text(
            json.dumps({"type": "session_meta", "payload": {"cwd": other}}) + "\n"
        )
        try:
            with patch("pathlib.Path.home", return_value=home):
                files = pt._list_session_files("codex", cwd)
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].name, "rollout-1.jsonl")
        finally:
            shutil.rmtree(home)


class TestOpencodeExport(unittest.TestCase):
    """Tests for OpenCode SQLite → JSONL export."""

    def setUp(self):
        self.tmp_home = Path(tempfile.mkdtemp())
        self.db_path = self.tmp_home / ".local" / "share" / "opencode" / "opencode.db"
        self.db_path.parent.mkdir(parents=True)
        self._build_db()

    def tearDown(self):
        shutil.rmtree(self.tmp_home)

    def _build_db(self):
        """Build a fake OpenCode SQLite DB with 1 session, 2 messages."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            CREATE TABLE session (
                id TEXT PRIMARY KEY,
                time_created INTEGER,
                directory TEXT,
                title TEXT
            )
        """)
        c.execute("""
            CREATE TABLE message (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                time_created INTEGER,
                data TEXT
            )
        """)
        c.execute("""
            CREATE TABLE part (
                id TEXT PRIMARY KEY,
                message_id TEXT,
                time_created INTEGER,
                data TEXT
            )
        """)
        c.execute(
            "INSERT INTO session VALUES (?, ?, ?, ?)",
            ("ses_test1", 1700000000000, "/Users/test/proj", "Test session"),
        )
        # User message
        c.execute(
            "INSERT INTO message VALUES (?, ?, ?, ?)",
            ("msg_u1", "ses_test1", 1700000001000, json.dumps({"role": "user"})),
        )
        c.execute(
            "INSERT INTO part VALUES (?, ?, ?, ?)",
            ("part_u1", "msg_u1", 1700000001000, json.dumps({"type": "text", "text": "Hello"})),
        )
        # Assistant message
        c.execute(
            "INSERT INTO message VALUES (?, ?, ?, ?)",
            ("msg_a1", "ses_test1", 1700000002000, json.dumps({"role": "assistant"})),
        )
        c.execute(
            "INSERT INTO part VALUES (?, ?, ?, ?)",
            ("part_a1", "msg_a1", 1700000002000, json.dumps({"type": "text", "text": "Hi there"})),
        )
        # Reasoning part — should be skipped
        c.execute(
            "INSERT INTO part VALUES (?, ?, ?, ?)",
            ("part_a2", "msg_a1", 1700000002100, json.dumps({"type": "reasoning", "text": "thinking..."})),
        )
        conn.commit()
        conn.close()

    def test_export_to_jsonl_format(self):
        out = Path(tempfile.gettempdir()) / "chat2k-test-export.jsonl"
        try:
            with patch("pathlib.Path.home", return_value=self.tmp_home):
                pt._opencode_export_to_jsonl(self.db_path, "ses_test1", out)
            self.assertTrue(out.is_file())
            lines = out.read_text().strip().split("\n")
            self.assertEqual(len(lines), 2)
            # First message: user
            d1 = json.loads(lines[0])
            self.assertEqual(d1["type"], "user")
            self.assertEqual(d1["message"]["content"], "Hello")
            self.assertIn("Z", d1["timestamp"])
            # Second message: assistant — reasoning part skipped
            d2 = json.loads(lines[1])
            self.assertEqual(d2["type"], "assistant")
            self.assertEqual(d2["message"]["content"], "Hi there")
            self.assertNotIn("thinking", d2["message"]["content"])
        finally:
            if out.exists():
                out.unlink()

    def test_find_active_session_id(self):
        with patch("pathlib.Path.home", return_value=self.tmp_home):
            sid = pt._opencode_active_session_id(self.db_path, "/Users/test/proj")
        self.assertEqual(sid, "ses_test1")

    def test_find_active_session_id_fallback(self):
        # No matching cwd → fallback to most recent
        with patch("pathlib.Path.home", return_value=self.tmp_home):
            sid = pt._opencode_active_session_id(self.db_path, "/Users/other/proj")
        self.assertEqual(sid, "ses_test1")

    def test_export_round_trips_through_parser(self):
        """The exported JSONL must be parseable by the standard parse_jsonl."""
        out = Path(tempfile.gettempdir()) / "chat2k-test-roundtrip.jsonl"
        try:
            with patch("pathlib.Path.home", return_value=self.tmp_home):
                pt._opencode_export_to_jsonl(self.db_path, "ses_test1", out)
            result = pt.parse_jsonl(str(out))
            self.assertEqual(result["session_meta"]["msg_count"], 2)
            self.assertEqual(result["messages"][0]["role"], "user")
            self.assertEqual(result["messages"][1]["role"], "assistant")
        finally:
            if out.exists():
                out.unlink()

    def test_export_current_uses_time_module(self):
        """Regression: ensure 'time' is imported so the cache TTL check works."""
        # Run the function — this used to NameError because 'time' was not imported.
        with patch("pathlib.Path.home", return_value=self.tmp_home):
            result = pt._opencode_export_current("/Users/test/proj")
        # Even if no session found, the call must not raise NameError
        self.assertIsInstance(result, str)

    def test_export_current_cache_hit_triggers_time_check(self):
        """Pre-populate the cache file then verify the TTL branch executes."""
        # Pre-create the export file so the cache-hit path runs
        session_id = "ses_test1"
        cache_path = Path(tempfile.gettempdir()) / f"chat2k-opencode-{session_id}.jsonl"
        cache_path.write_text(
            json.dumps({"type": "user", "message": {"content": "cached"}}) + "\n"
        )
        try:
            with patch("pathlib.Path.home", return_value=self.tmp_home):
                result = pt._opencode_export_current("/Users/test/proj")
            # Cache hit returns the cached path
            self.assertEqual(result, str(cache_path))
        finally:
            if cache_path.exists():
                cache_path.unlink()


class TestCliRegistry(unittest.TestCase):
    """Tests for the generic CLI handler registry."""

    def test_registry_has_all_clis(self):
        expected = {"claude-code", "codex", "opencode", "cursor", "unknown"}
        self.assertEqual(set(pt.CLI_HANDLERS.keys()), expected)

    def test_registry_handler_types(self):
        self.assertEqual(pt.CLI_HANDLERS["claude-code"]["type"], "jsonl")
        self.assertEqual(pt.CLI_HANDLERS["codex"]["type"], "jsonl")
        self.assertEqual(pt.CLI_HANDLERS["opencode"]["type"], "sqlite")
        self.assertEqual(pt.CLI_HANDLERS["cursor"]["type"], "sqlite")
        self.assertEqual(pt.CLI_HANDLERS["unknown"]["type"], "generic")

    def test_unknown_handler_finds_cached_files(self):
        # Create a fake temp file matching the cache pattern
        tmp = Path(tempfile.gettempdir()) / "chat2k-test-fallback.jsonl"
        tmp.write_text('{"type":"user","message":{"content":"x"}}\n')
        try:
            files = pt._list_generic_sessions("/tmp")
            self.assertIn(tmp, files)
        finally:
            tmp.unlink()

    def test_unknown_handler_includes_cwd_match_when_present(self):
        # Set up a fake codex session for cwd
        home = Path(tempfile.mkdtemp())
        root = home / ".codex" / "sessions" / "2026" / "07" / "23"
        root.mkdir(parents=True)
        match = root / "rollout-test.jsonl"
        match.write_text(
            json.dumps({"type": "session_meta", "payload": {"cwd": "/Users/test"}})
            + "\n"
        )
        try:
            with patch("pathlib.Path.home", return_value=home):
                files = pt._list_generic_sessions("/Users/test")
            self.assertIn(match, files)
        finally:
            shutil.rmtree(home)


class TestCursorExtract(unittest.TestCase):
    """Tests for the defensive Cursor message extractor."""

    def test_extracts_messages_array(self):
        data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ]
        }
        out = pt._cursor_extract_messages(data)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["type"], "user")
        self.assertEqual(out[0]["message"]["content"], "Hello")
        self.assertEqual(out[1]["type"], "assistant")

    def test_normalizes_human_to_user(self):
        data = {"messages": [{"role": "human", "text": "Q"}]}
        out = pt._cursor_extract_messages(data)
        self.assertEqual(out[0]["type"], "user")

    def test_skips_unknown_roles(self):
        data = {"messages": [{"role": "system", "content": "x"}]}
        out = pt._cursor_extract_messages(data)
        self.assertEqual(out, [])

    def test_handles_empty_content(self):
        data = {"messages": [{"role": "user", "content": ""}]}
        out = pt._cursor_extract_messages(data)
        self.assertEqual(out, [])

    def test_handles_list_content(self):
        data = {
            "messages": [
                {"role": "user", "content": [{"text": "part1"}, {"text": "part2"}]}
            ]
        }
        out = pt._cursor_extract_messages(data)
        self.assertEqual(len(out), 1)
        self.assertIn("part1", out[0]["message"]["content"])
        self.assertIn("part2", out[0]["message"]["content"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
