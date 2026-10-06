#!/usr/bin/env python3
"""Classify /learn command input into mode, topic, flags.

Deterministic parser - zero external deps, zero token overhead.
Output: JSON to stdout with {mode, topic, html, url, eli}.

Mode: the FIRST word, only when it is exactly a mode name
(overview, usage, workflow, internals, cheatsheet, docs). No aliases.
Otherwise overview.
ELI: --eli<N> flag (--eli5, --eli10, ...), N = reader level. A modifier on any
mode; with no mode word it selects the dedicated eli template.
Flags (--eli<N>, --md, --html) may appear anywhere.
"""
import sys
import re
import json

MODES = {"overview", "usage", "workflow", "internals", "cheatsheet", "docs"}
DEFAULT_MODE = "overview"

# Modes that default to HTML output (long or table-heavy content)
HTML_MODES = {"usage", "workflow", "internals", "cheatsheet"}

URL_PATTERN = re.compile(r'https?://[^\s]+')
ELI_PATTERN = re.compile(r'(?<!\S)--eli([1-9]\d?)(?!\S)')
NONE_RESULT = {"mode": "none", "topic": "", "html": False, "url": None, "eli": None}


def _squeeze(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def _pop_flag(text: str, flag: str) -> tuple:
    """Remove a standalone flag from text. Returns (found, remaining_text)."""
    pattern = re.compile(r'(?<!\S)' + re.escape(flag) + r'(?!\S)')
    return bool(pattern.search(text)), _squeeze(pattern.sub(' ', text))


def classify(raw_input: str) -> dict:
    """Parse raw input string into structured classification."""
    text = _squeeze(raw_input)

    eli_match = ELI_PATTERN.search(text)
    eli = int(eli_match.group(1)) if eli_match else None
    text = _squeeze(ELI_PATTERN.sub(' ', text))
    md_flag, text = _pop_flag(text, "--md")
    html_flag, text = _pop_flag(text, "--html")

    # URL (strip trailing punctuation); remaining text stays as context
    url = None
    url_match = URL_PATTERN.search(text)
    if url_match:
        url = url_match.group(0).rstrip('.,;:!?)')
        text = _squeeze(text.replace(url_match.group(0), " "))

    # Mode word must come first, so topics like "memory usage" stay intact
    mode = None
    first, _, rest = text.partition(" ")
    if first.lower() in MODES:
        mode = first.lower()
        text = rest.strip()

    topic = text or url
    if not topic:
        return dict(NONE_RESULT)
    if mode is None:
        mode = "eli" if eli else DEFAULT_MODE

    if html_flag:
        html = True
    elif md_flag:
        html = False
    else:
        html = mode in HTML_MODES
    return {"mode": mode, "topic": topic, "html": html, "url": url, "eli": eli}


if __name__ == "__main__":
    raw = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    print(json.dumps(classify(raw), ensure_ascii=False))
