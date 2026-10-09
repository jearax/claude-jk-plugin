"""Detect comments that only restate the code next to them ("what, not why").

Regexes cannot enumerate every way to narrate code ("Add the item to the total", "Optional className",
"render span"), so this compares the comment's content words with the identifiers of the code it
describes: the same line for a trailing comment, the next code line for a whole-line comment. A short
comment with no why-signal whose content words mostly appear in that code adds nothing the code does not
already say. Word lists and thresholds live under `echo` in references/patterns.json.
"""
import re

CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


class EchoConfig:
    def __init__(self, data):
        self.max_words = data["max_words"]
        self.min_overlap = data["min_overlap"]
        self.why = re.compile(data["why_regex"], re.I | re.U)
        self.neutral = {_norm(w) for w in data["neutral_words"]}
        self.stopwords = {_norm(w) for w in data["stopwords"]}


def _norm(word):
    word = word.lower()
    if len(word) > 4 and word.endswith("es") and word[-3] in "sxz":
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def tokens(text):
    out = []
    for raw in re.findall(r"[^\W_]+", text, re.U):
        out.extend(_norm(part) for part in CAMEL.split(raw) if part)
    return out


def _matches(word, code_tokens):
    return any(word == t or (min(len(word), len(t)) >= 4 and (word.startswith(t) or t.startswith(word)))
               for t in code_tokens)


def restates(comment, code, cfg):
    """True when `comment` says nothing beyond the identifiers in `code`."""
    if not code or not code.strip() or cfg.why.search(comment):
        return False
    words = tokens(comment)
    if not words or len(words) > cfg.max_words:
        return False
    content = [w for w in words if w not in cfg.stopwords and w not in cfg.neutral]
    if not content:
        return any(w in cfg.neutral for w in words)
    code_tokens = set(tokens(code))
    hits = sum(1 for w in content if _matches(w, code_tokens))
    return hits / len(content) >= cfg.min_overlap
