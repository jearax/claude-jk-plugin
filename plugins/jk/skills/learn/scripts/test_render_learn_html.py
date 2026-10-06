#!/usr/bin/env python3
"""Tests for render-learn-html.py - output shape, escaping, and CLI errors."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent / "render-learn-html.py")
PYTHON = sys.executable


def run_render(markdown: str, *args: str):
    """Write markdown to a temp file, render it, return (result, html_text)."""
    tmp = Path(tempfile.mkdtemp())
    src, out = tmp / "note.md", tmp / "out" / "note.html"
    src.write_text(markdown, encoding="utf-8")
    result = subprocess.run(
        [PYTHON, SCRIPT, "--in", str(src), "--out", str(out), *args],
        capture_output=True, text=True, timeout=10,
    )
    return result, (out.read_text(encoding="utf-8") if out.exists() else "")


def embedded_markdown(page: str) -> str:
    """Decode the Markdown JSON string embedded in the page script."""
    raw = re.search(r'var md = (".*?");\n', page, re.S).group(1)
    return json.loads(raw.replace("<\\/", "</"))


class TestRenderLearnHtml(unittest.TestCase):

    def test_writes_page_with_mode_and_lang(self):
        result, page = run_render("# Zod - Cheat Sheet\n\n| a | b |\n|---|---|\n| 1 | 2 |\n",
                                  "--mode", "cheatsheet", "--lang", "vi")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('<html lang="vi" data-mode="cheatsheet">', page)
        self.assertIn('<meta charset="UTF-8">', page)
        self.assertIn("<title>Zod - Cheat Sheet</title>", page)

    def test_title_override(self):
        _, page = run_render("# Heading\n", "--mode", "usage", "--title", "Custom")
        self.assertIn("<title>Custom</title>", page)

    def test_title_falls_back_to_file_stem(self):
        _, page = run_render("no heading here\n", "--mode", "usage")
        self.assertIn("<title>note</title>", page)

    def test_markdown_round_trips_exactly(self):
        md = "# Tiêu đề\n\n```js\nconst a = `x`;\n```\n\n\"quotes\" & <tags>\n"
        _, page = run_render(md, "--mode", "usage")
        self.assertEqual(embedded_markdown(page), md)

    def test_script_close_tag_cannot_break_out(self):
        md = "# T\n\n</script><script>alert(1)</script>\n"
        _, page = run_render(md, "--mode", "internals")
        script = page.split("var md = ", 1)[1].split(";\n", 1)[0]
        self.assertNotIn("</script>", script)
        self.assertEqual(embedded_markdown(page), md)

    def test_raw_fallback_is_escaped(self):
        _, page = run_render("# T\n\n<img src=x onerror=alert(1)>\n", "--mode", "usage")
        raw = page.split('<pre class="raw">', 1)[1].split("</pre>", 1)[0]
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", raw)
        self.assertNotIn("<img", raw)

    def test_output_is_sanitized_in_browser(self):
        _, page = run_render("# T\n", "--mode", "usage")
        self.assertIn("DOMPurify.sanitize(marked.parse(md))", page)

    def test_title_is_escaped(self):
        _, page = run_render("# A <b>& B\n", "--mode", "usage")
        self.assertIn("<title>A &lt;b&gt;&amp; B</title>", page)

    def test_every_mode_is_accepted(self):
        for mode in ("overview", "usage", "workflow", "internals", "cheatsheet", "docs", "eli"):
            result, page = run_render("# T\n", "--mode", mode)
            self.assertEqual(result.returncode, 0, mode)
            self.assertIn(f'data-mode="{mode}"', page)

    def test_unknown_mode_is_rejected(self):
        result, page = run_render("# T\n", "--mode", "full")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(page, "")

    def test_missing_input_is_an_error(self):
        result = subprocess.run(
            [PYTHON, SCRIPT, "--in", "/nonexistent/note.md", "--out", "/tmp/x.html", "--mode", "usage"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("input not found", result.stderr)

    def test_prints_output_path(self):
        result, _ = run_render("# T\n", "--mode", "usage")
        self.assertTrue(result.stdout.strip().endswith("note.html"))


if __name__ == "__main__":
    unittest.main()
