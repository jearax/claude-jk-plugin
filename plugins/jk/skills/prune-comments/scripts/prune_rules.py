"""Shared loader for references/patterns.json, used by git-checkpoint.py.

Snake_case (unlike the CLI scripts) because it is imported, not executed.
"""
import fnmatch
import json
import os
import re

REFERENCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references")
PATTERNS_PATH = os.path.join(REFERENCES_DIR, "patterns.json")


class Rules:
    def __init__(self, path=PATTERNS_PATH):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        ignore = data["ignore"]
        self.ignore_dirs = set(ignore["dirs"])
        self.ignore_globs = tuple(ignore["globs"])
        self.generated_markers = tuple(m.encode() for m in ignore["generated_markers"])
        self.marker_by_ext = {ext: marker for marker, exts in data["comment_syntax"].items() for ext in exts}
        self.keep = [re.compile(p["regex"], re.I) for p in data["keep"]]
        self.junk = [(p["label"], re.compile(p["regex"], re.I)) for p in data["junk"]]

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
