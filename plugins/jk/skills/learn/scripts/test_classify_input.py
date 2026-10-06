#!/usr/bin/env python3
"""Tests for classify-input.py - covers all input formats + output format logic."""
import unittest
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent / "classify-input.py")
PYTHON = sys.executable


def run_classify(args: str) -> dict:
    """Run classify script with given args, return parsed JSON."""
    result = subprocess.run(
        [PYTHON, SCRIPT] + (args.split() if args else []),
        capture_output=True, text=True, timeout=5
    )
    return json.loads(result.stdout)


class TestClassifyInput(unittest.TestCase):
    """Test mode detection and output format logic."""

    # --- Default: bare topic → overview, MD ---

    def test_bare_topic_is_overview_md(self):
        r = run_classify("zustand")
        self.assertEqual(r["mode"], "overview")
        self.assertEqual(r["topic"], "zustand")
        self.assertFalse(r["html"])
        self.assertIsNone(r["eli"])

    def test_multi_word_topic(self):
        r = run_classify("react hooks")
        self.assertEqual(r["mode"], "overview")
        self.assertEqual(r["topic"], "react hooks")

    # --- Mode words (first word only, exact name) ---

    def test_overview_mode(self):
        r = run_classify("overview zustand")
        self.assertEqual(r["mode"], "overview")
        self.assertEqual(r["topic"], "zustand")
        self.assertFalse(r["html"])

    def test_usage_mode(self):
        r = run_classify("usage tanstack router")
        self.assertEqual(r["mode"], "usage")
        self.assertEqual(r["topic"], "tanstack router")
        self.assertTrue(r["html"])

    def test_internals_mode(self):
        r = run_classify("internals react hooks")
        self.assertEqual(r["mode"], "internals")
        self.assertEqual(r["topic"], "react hooks")
        self.assertTrue(r["html"])

    def test_cheatsheet_mode(self):
        r = run_classify("cheatsheet zod")
        self.assertEqual(r["mode"], "cheatsheet")
        self.assertEqual(r["topic"], "zod")
        self.assertTrue(r["html"])

    def test_workflow_mode(self):
        r = run_classify("workflow auth with better-auth")
        self.assertEqual(r["mode"], "workflow")
        self.assertEqual(r["topic"], "auth with better-auth")
        self.assertTrue(r["html"])

    def test_docs_mode(self):
        r = run_classify("docs nextjs")
        self.assertEqual(r["mode"], "docs")
        self.assertEqual(r["topic"], "nextjs")
        self.assertFalse(r["html"])

    def test_mode_word_case_insensitive(self):
        r = run_classify("Usage zod")
        self.assertEqual(r["mode"], "usage")
        self.assertEqual(r["topic"], "zod")

    def test_mode_word_not_first_stays_topic(self):
        r = run_classify("memory usage")
        self.assertEqual(r["mode"], "overview")
        self.assertEqual(r["topic"], "memory usage")

    def test_removed_modes_are_topic_text(self):
        for word in ("quick", "full", "detail", "deep", "cheat"):
            r = run_classify(f"{word} zustand")
            self.assertEqual(r["mode"], "overview", word)
            self.assertEqual(r["topic"], f"{word} zustand", word)

    # --- URL input ---

    def test_url_input_defaults_to_overview(self):
        r = run_classify("https://zustand-demo.pmnd.rs/")
        self.assertEqual(r["mode"], "overview")
        self.assertEqual(r["url"], "https://zustand-demo.pmnd.rs/")
        self.assertEqual(r["topic"], "https://zustand-demo.pmnd.rs/")
        self.assertFalse(r["html"])

    def test_url_trailing_punctuation(self):
        r = run_classify("https://react.dev.")
        self.assertEqual(r["url"], "https://react.dev")

    def test_url_with_mode(self):
        r = run_classify("usage https://orm.drizzle.team/docs/overview")
        self.assertEqual(r["mode"], "usage")
        self.assertEqual(r["url"], "https://orm.drizzle.team/docs/overview")
        self.assertTrue(r["html"])

    def test_url_with_context(self):
        r = run_classify("check this for hooks https://react.dev")
        self.assertEqual(r["url"], "https://react.dev")
        self.assertEqual(r["topic"], "check this for hooks")

    # --- ELI modifier ---

    def test_eli_without_mode_selects_eli_template(self):
        r = run_classify("event loop --eli5")
        self.assertEqual(r["mode"], "eli")
        self.assertEqual(r["eli"], 5)
        self.assertEqual(r["topic"], "event loop")
        self.assertFalse(r["html"])

    def test_eli_combines_with_each_mode(self):
        for mode, html in (("overview", False), ("usage", True),
                           ("workflow", True), ("internals", True),
                           ("cheatsheet", True), ("docs", False)):
            r = run_classify(f"{mode} react --eli10")
            self.assertEqual(r["mode"], mode)
            self.assertEqual(r["eli"], 10)
            self.assertEqual(r["topic"], "react")
            self.assertEqual(r["html"], html, mode)

    def test_eli_position_anywhere(self):
        r = run_classify("--eli15 usage zod")
        self.assertEqual(r["mode"], "usage")
        self.assertEqual(r["eli"], 15)
        self.assertEqual(r["topic"], "zod")

    def test_eli_with_url(self):
        r = run_classify("https://react.dev --eli5")
        self.assertEqual(r["mode"], "eli")
        self.assertEqual(r["eli"], 5)
        self.assertEqual(r["url"], "https://react.dev")

    def test_eli_word_without_dashes_is_topic(self):
        r = run_classify("eli5 dns")
        self.assertEqual(r["mode"], "overview")
        self.assertEqual(r["topic"], "eli5 dns")
        self.assertIsNone(r["eli"])

    def test_eli_zero_is_not_a_flag(self):
        r = run_classify("dns --eli0")
        self.assertIsNone(r["eli"])
        self.assertEqual(r["topic"], "dns --eli0")

    # --- Empty / missing topic ---

    def test_empty_input(self):
        r = run_classify("")
        self.assertEqual(r["mode"], "none")
        self.assertFalse(r["html"])
        self.assertIsNone(r["url"])

    def test_mode_only_no_topic(self):
        r = run_classify("usage")
        self.assertEqual(r["mode"], "none")

    def test_flags_only_no_topic(self):
        r = run_classify("--eli5 --html")
        self.assertEqual(r["mode"], "none")

    # --- Output format flags ---

    def test_md_flag_overrides_html_mode(self):
        r = run_classify("usage zustand --md")
        self.assertEqual(r["mode"], "usage")
        self.assertFalse(r["html"])

    def test_html_flag_overrides_md_mode(self):
        r = run_classify("zustand --html")
        self.assertEqual(r["mode"], "overview")
        self.assertTrue(r["html"])

    def test_html_flag_with_eli(self):
        r = run_classify("dns --eli5 --html")
        self.assertEqual(r["mode"], "eli")
        self.assertTrue(r["html"])

    def test_flag_inside_word_not_matched(self):
        r = run_classify("foo--md")
        self.assertEqual(r["topic"], "foo--md")
        self.assertFalse(r["html"])


if __name__ == "__main__":
    unittest.main()
