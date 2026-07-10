#!/usr/bin/env python3
"""Classify /learn command input into mode, topic, flags.

Deterministic parser - zero external deps, zero token overhead.
Output: JSON to stdout with {mode, topic, html, url}.

Default mode: quick (MD terminal, lightweight).
Full mode: requires explicit keywords (full, strict, hard, ...).
"""
import sys
import re
import json

INTENT_MAP = {
    # Full/comprehensive keywords → full mode + HTML
    "comprehensive": "full",
    "thorough": "full",
    "strict": "full",
    "full": "full",
    "hard": "full",
    # Vietnamese: full
    "đầy đủ": "full",
    "toàn bộ": "full",
    "kỹ lưỡng": "full",
    # Detail keywords → detail mode + HTML
    "deep dive": "detail",
    "detail": "detail",
    "deep": "detail",
    # Vietnamese: detail
    "chi tiết": "detail",
    "sâu": "detail",
    "kỹ": "detail",
    # Overview → overview mode (MD terminal)
    "overview": "overview",
    # Vietnamese: overview
    "tổng quan": "overview",
    # Cheatsheet → cheatsheet mode + HTML
    "cheatsheet": "cheatsheet",
    "cheat": "cheatsheet",
    # Vietnamese: cheatsheet
    "tóm tắt": "cheatsheet",
    # Natural language → quick mode
    "tell me about": "quick",
    "tell me": "quick",
    "about": "quick",
}

# Keywords that force quick mode (MD terminal, lightweight)
# Includes Vietnamese: nhanh, gọn, ngắn
QUICK_KEYWORDS = {"fast", "quick", "brief", "simple", "short", "nhanh", "gọn", "ngắn"}

# Modes that default to HTML output
HTML_MODES = {"full", "detail", "cheatsheet"}

URL_PATTERN = re.compile(r'https?://[^\s]+')


def classify(raw_input: str) -> dict:
    """Parse raw input string into structured classification."""
    text = raw_input.strip()
    if not text:
        return {"mode": "none", "topic": "", "html": False, "url": None}

    # Detect --md flag → force MD output
    md_flag = bool(re.search(r'\B--md\b', text))
    text = re.sub(r'\s*\B--md\b\s*', ' ', text).strip()

    # Detect --html flag → force HTML output
    html_flag = bool(re.search(r'\B--html\b', text))
    text = re.sub(r'\s*\B--html\b\s*', ' ', text).strip()

    # Detect URL (strip trailing punctuation)
    url_match = URL_PATTERN.search(text)
    if url_match:
        url = url_match.group(0).rstrip('.,;:!?)')
        text = re.sub(r'\s+', ' ', text.replace(url_match.group(0), " ")).strip()
        mode = _resolve_mode(text)
        html = _resolve_html(mode, text, md_flag, html_flag)
        return {"mode": mode, "topic": text or url, "html": html, "url": url}

    # Detect intent keywords (word boundaries, longest match first)
    for keyword, mode in sorted(INTENT_MAP.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        if pattern.search(text):
            topic = re.sub(r'\s+', ' ', pattern.sub("", text, count=1)).strip()
            if not topic:
                return {"mode": "none", "topic": "", "html": False, "url": None}
            html = _resolve_html(mode, topic, md_flag, html_flag)
            return {"mode": mode, "topic": topic, "html": html, "url": None}

    # Default: bare topic → quick mode, MD terminal
    html = _resolve_html("quick", text, md_flag, html_flag)
    return {"mode": "quick", "topic": text, "html": html, "url": None}


def _resolve_mode(text: str) -> str:
    """Resolve mode from text. Checks INTENT_MAP first, then QUICK_KEYWORDS, else full."""
    # Check INTENT_MAP keywords (longest match first) — preserves detail/overview/cheatsheet intent
    for keyword, mode in sorted(INTENT_MAP.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        if pattern.search(text):
            return mode
    # Fallback: quick keywords → quick, else full
    words = set(text.lower().split())
    if words & QUICK_KEYWORDS:
        return "quick"
    return "full"


def _resolve_html(mode: str, text: str, md_flag: bool, html_flag: bool) -> bool:
    """Determine output format. Explicit flags override mode defaults."""
    if html_flag:
        return True
    if md_flag:
        return False
    # Mode-based default: full/detail/cheatsheet → HTML, quick/overview → MD
    return mode in HTML_MODES


if __name__ == "__main__":
    raw = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    print(json.dumps(classify(raw), ensure_ascii=False))
