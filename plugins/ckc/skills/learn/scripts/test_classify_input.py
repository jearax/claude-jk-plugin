#!/usr/bin/env python3
"""Tests for classify-input.py - covers all input formats + output format logic."""
import unittest
import json
import subprocess
import sys

SCRIPT = "scripts/classify-input.py"
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

    # --- Default: bare topic → quick mode, MD terminal ---

    def test_bare_topic_is_quick_md(self):
        r = run_classify("zustand")
        self.assertEqual(r["mode"], "quick")
        self.assertFalse(r["html"])

    def test_bare_topic_react_hooks(self):
        r = run_classify("react hooks")
        self.assertEqual(r["mode"], "quick")
        self.assertFalse(r["html"])

    # --- Quick keywords → quick mode, MD ---

    def test_fast_keyword(self):
        r = run_classify("fast zustand")
        self.assertEqual(r["mode"], "quick")
        self.assertFalse(r["html"])

    def test_quick_keyword(self):
        r = run_classify("quick react hooks")
        self.assertEqual(r["mode"], "quick")
        self.assertFalse(r["html"])

    def test_brief_keyword(self):
        r = run_classify("brief tailwind")
        self.assertEqual(r["mode"], "quick")
        self.assertFalse(r["html"])

    def test_simple_keyword(self):
        r = run_classify("simple nextjs")
        self.assertEqual(r["mode"], "quick")
        self.assertFalse(r["html"])

    # --- Full keywords → full mode, HTML ---

    def test_full_keyword(self):
        r = run_classify("full zustand")
        self.assertEqual(r["mode"], "full")
        self.assertTrue(r["html"])

    def test_strict_keyword(self):
        r = run_classify("strict react")
        self.assertEqual(r["mode"], "full")
        self.assertTrue(r["html"])

    def test_hard_keyword(self):
        r = run_classify("hard tailwind")
        self.assertEqual(r["mode"], "full")
        self.assertTrue(r["html"])

    def test_comprehensive_keyword(self):
        r = run_classify("comprehensive nextjs")
        self.assertEqual(r["mode"], "full")
        self.assertTrue(r["html"])

    def test_thorough_keyword(self):
        r = run_classify("thorough svelte")
        self.assertEqual(r["mode"], "full")
        self.assertTrue(r["html"])

    # --- Natural language → quick mode ---

    def test_tell_me_about(self):
        r = run_classify("tell me about zustand")
        self.assertEqual(r["mode"], "quick")
        self.assertEqual(r["topic"], "zustand")
        self.assertFalse(r["html"])

    def test_about(self):
        r = run_classify("about zustand")
        self.assertEqual(r["mode"], "quick")
        self.assertEqual(r["topic"], "zustand")

    # --- Detail mode → HTML ---

    def test_detail_keyword(self):
        r = run_classify("detail zustand")
        self.assertEqual(r["mode"], "detail")
        self.assertEqual(r["topic"], "zustand")
        self.assertTrue(r["html"])

    def test_deep_dive(self):
        r = run_classify("deep dive react hooks")
        self.assertEqual(r["mode"], "detail")
        self.assertEqual(r["topic"], "react hooks")
        self.assertTrue(r["html"])

    # --- Overview → MD terminal ---

    def test_overview(self):
        r = run_classify("overview zustand")
        self.assertEqual(r["mode"], "overview")
        self.assertEqual(r["topic"], "zustand")
        self.assertFalse(r["html"])

    # --- Cheatsheet → HTML ---

    def test_cheatsheet(self):
        r = run_classify("cheatsheet zustand")
        self.assertEqual(r["mode"], "cheatsheet")
        self.assertEqual(r["topic"], "zustand")
        self.assertTrue(r["html"])

    def test_cheat_short(self):
        r = run_classify("cheat tailwind")
        self.assertEqual(r["mode"], "cheatsheet")
        self.assertEqual(r["topic"], "tailwind")
        self.assertTrue(r["html"])

    # --- URL handling → full mode by default, HTML ---

    def test_url_input(self):
        r = run_classify("https://zustand-demo.pmnd.rs/")
        self.assertEqual(r["mode"], "full")
        self.assertEqual(r["url"], "https://zustand-demo.pmnd.rs/")
        self.assertTrue(r["html"])

    def test_url_trailing_punctuation(self):
        r = run_classify("https://react.dev.")
        self.assertEqual(r["url"], "https://react.dev")

    def test_url_with_context(self):
        r = run_classify("check this https://react.dev for hooks")
        self.assertEqual(r["url"], "https://react.dev")
        self.assertEqual(r["topic"], "check this for hooks")

    # --- Edge cases ---

    def test_empty_input(self):
        r = run_classify("")
        self.assertEqual(r["mode"], "none")
        self.assertFalse(r["html"])
        self.assertIsNone(r["url"])

    def test_keyword_only_no_topic(self):
        r = run_classify("overview")
        self.assertEqual(r["mode"], "none")

    def test_detailed_not_match_detail(self):
        r = run_classify("detailed react")
        self.assertEqual(r["mode"], "quick")
        self.assertEqual(r["topic"], "detailed react")

    def test_about_inside_word(self):
        r = run_classify("what about react")
        self.assertEqual(r["mode"], "quick")
        self.assertEqual(r["topic"], "what react")

    # --- Flag overrides ---

    def test_md_flag_overrides_html_mode(self):
        r = run_classify("full zustand --md")
        self.assertEqual(r["mode"], "full")
        self.assertFalse(r["html"])

    def test_html_flag_overrides_quick_mode(self):
        r = run_classify("zustand --html")
        self.assertEqual(r["mode"], "quick")
        self.assertTrue(r["html"])


if __name__ == "__main__":
    unittest.main()
