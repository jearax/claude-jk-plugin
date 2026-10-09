#!/usr/bin/env python3
"""PostToolUse hook: flag obvious junk comments in text the AI just wrote.

Reads the hook payload on stdin. Scans only the new text (Write `content`, Edit `new_string`,
MultiEdit `edits[].new_string`) in tier order: T0 keep (patterns.json), T2 keep and junk (Regex lines
of junk-catalog.md), then T3 junk (patterns.json), then the echo check (comment_echo.py) for comments
that only restate the code they describe. Matches go out as `additionalContext` so Claude can remove
them itself. Never edits files, never blocks, and exits 0 silently on any internal error.

Disable with plugin option prune_comments_hook=false (env CLAUDE_PLUGIN_OPTION_PRUNE_COMMENTS_HOOK).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comment_echo import restates  # noqa: E402
from prune_rules import Rules  # noqa: E402

TOGGLE_ENV = "CLAUDE_PLUGIN_OPTION_PRUNE_COMMENTS_HOOK"
MAX_FINDINGS = 30
ECHO_LABEL = "your rule: states what, not why"
DOC_PREFIXES = {"//": ("///", "//!"), "#": ("#!",), "--": ()}
BLOCK_LINE = re.compile(r"^(?:/\*\*?|\*(?=\s|/|$))(?!/)\s?(.*?)\s*(?:\*/)?$")


def enabled(env):
    return env.get(TOGGLE_ENV, "true").strip().lower() not in {"false", "0", "no", "off"}


def _quotes_balanced(code):
    code = code.replace("\\\\", "").replace('\\"', "").replace("\\'", "")
    return all(code.count(q) % 2 == 0 for q in ('"', "'", "`"))


def extract_comment(line, marker):
    """Return (body, code) for a comment line, code being None for a whole-line comment; None for code only."""
    stripped = line.strip()
    if stripped.startswith(marker):
        if stripped.startswith(DOC_PREFIXES[marker]):
            return "", None
        return stripped[len(marker):].strip(), None
    if marker == "//" and BLOCK_LINE.match(stripped):
        return BLOCK_LINE.match(stripped).group(1).strip(), None
    idx = line.find(" " + marker)
    while idx != -1:
        code = line[:idx]
        if code.strip() and _quotes_balanced(code):
            return line[idx + 1 + len(marker):].strip(), code
        idx = line.find(" " + marker, idx + 1)
    return None


def _described_code(lines, parsed, offset):
    """The code a whole-line comment sits above: the next non-blank line that is not itself a comment."""
    for line, hit in zip(lines[offset + 1:], parsed[offset + 1:]):
        if not line.strip() or (hit and hit[1] is None):
            continue
        return hit[1] if hit else line
    return None


def _junk_label(body, rules):
    for label, pattern in rules.user_junk + rules.junk:
        if pattern.search(body):
            return label
    return None


def scan(text, marker, rules, first_line):
    lines = text.splitlines()
    parsed = [extract_comment(line, marker) for line in lines]
    findings = []
    for offset, (line, hit) in enumerate(zip(lines, parsed)):
        if not hit or not hit[0]:
            continue
        body, code = hit
        if any(k.search(body) for k in rules.keep + rules.user_keep):
            continue
        label = _junk_label(body, rules)
        if not label:
            described = code if code is not None else _described_code(lines, parsed, offset)
            label = ECHO_LABEL if restates(body, described, rules.echo) else None
        if label:
            findings.append((first_line + offset if first_line else None, line.strip(), label))
    return findings


def _new_texts(tool_name, tool_input):
    if tool_name == "Write":
        return [tool_input.get("content") or ""]
    if tool_name == "Edit":
        return [tool_input.get("new_string") or ""]
    if tool_name == "MultiEdit":
        return [e.get("new_string") or "" for e in tool_input.get("edits") or [] if isinstance(e, dict)]
    return []


def _display_path(file_path, cwd):
    rel = os.path.relpath(file_path, cwd) if cwd else file_path
    return file_path if rel.startswith("..") else rel


def analyze(payload, env=None, rules=None):
    env = os.environ if env is None else env
    if not enabled(env):
        return None
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path")
    if not file_path:
        return None
    rules = rules or Rules()
    marker = rules.marker_by_ext.get(os.path.splitext(file_path)[1].lower())
    shown = _display_path(file_path, payload.get("cwd"))
    if not marker or rules.is_ignored(shown):
        return None

    try:
        with open(file_path, encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except OSError:
        content = ""
    if content and rules.is_generated_or_binary(content[:8192].encode("utf-8", "replace")):
        return None

    findings = []
    for text in _new_texts(payload.get("tool_name"), tool_input):
        if not text:
            continue
        idx = content.find(text) if content else -1
        first_line = content.count("\n", 0, idx) + 1 if idx >= 0 else None
        findings.extend(scan(text, marker, rules, first_line))
    if not findings:
        return None

    lines = [
        f"- {'L' + str(ln) + ' ' if ln else ''}`{src[:100]}` ({label})"
        for ln, src, label in findings[:MAX_FINDINGS]
    ]
    if len(findings) > MAX_FINDINGS:
        lines.append(f"- +{len(findings) - MAX_FINDINGS} more")
    message = (
        f"jk:prune-comments: likely junk comments in what you just wrote to {shown}. "
        "Remove each one unless it carries information the code does not already show; "
        "change nothing else.\n" + "\n".join(lines)
    )
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": message}}


def main():
    try:
        result = analyze(json.load(sys.stdin))
        if result:
            print(json.dumps(result, ensure_ascii=False))
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
