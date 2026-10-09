"""Shared loader for references/patterns.json and the optional Regex lines of references/junk-catalog.md,
used by git-checkpoint.py and comment-lint-hook.py.

Snake_case (unlike the CLI scripts) because it is imported, not executed.
"""
import fnmatch
import json
import os
import re

REFERENCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references")
PATTERNS_PATH = os.path.join(REFERENCES_DIR, "patterns.json")
CATALOG_PATH = os.path.join(REFERENCES_DIR, "junk-catalog.md")
REGEX_LINE = re.compile(r"^\s*-\s*\*\*Regex:\*\*\s*`(.+)`\s*$")


def parse_catalog(path):
    """Return (keep, junk) regexes from the `## Keep` / `## Junk` sections; junk carries its ### heading."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = re.sub(r"<!--.*?-->", "", fh.read(), flags=re.S)
    except OSError:
        return [], []
    keep, junk, section, heading = [], [], None, ""
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
        elif line.startswith("### "):
            heading = line[4:].strip()
        else:
            match = REGEX_LINE.match(line)
            if not match or section not in {"keep", "junk"}:
                continue
            try:
                pattern = re.compile(match.group(1), re.I)
            except re.error:
                continue
            if section == "keep":
                keep.append(pattern)
            else:
                junk.append((f"your rule: {heading.lower()}", pattern))
    return keep, junk


class Rules:
    def __init__(self, path=PATTERNS_PATH, catalog_path=CATALOG_PATH):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        ignore = data["ignore"]
        self.ignore_dirs = set(ignore["dirs"])
        self.ignore_globs = tuple(ignore["globs"])
        self.generated_markers = tuple(m.encode() for m in ignore["generated_markers"])
        self.marker_by_ext = {ext: marker for marker, exts in data["comment_syntax"].items() for ext in exts}
        self.keep = [re.compile(p["regex"], re.I) for p in data["keep"]]
        self.junk = [(p["label"], re.compile(p["regex"], re.I)) for p in data["junk"]]
        self.user_keep, self.user_junk = parse_catalog(catalog_path)

    def is_ignored(self, rel_path):
        parts = rel_path.replace(os.sep, "/").split("/")
        if any(part in self.ignore_dirs for part in parts[:-1]):
            return True
        return any(fnmatch.fnmatch(parts[-1], glob) for glob in self.ignore_globs)

    def is_generated_or_binary(self, head_bytes):
        if b"\0" in head_bytes:
            return True
        first_lines = b"\n".join(head_bytes.splitlines()[:5])
        return any(marker in first_lines for marker in self.generated_markers)
