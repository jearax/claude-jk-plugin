#!/usr/bin/env python3
"""Fetch LeetCode problem metadata by numeric id, slug, or problem URL.

Stdlib-only (urllib). Resolution path:
  1. URL input        -> extract slug, query GraphQL directly.
  2. Bare slug input  -> query GraphQL directly.
  3. Numeric id input -> resolve slug via the /api/problems/all/ index
                         (cached 24h in $TMPDIR), fallback to a GraphQL
                         keyword search, then query GraphQL.

Output: one JSON object on stdout (UTF-8). Diagnostics on stderr.

Exit codes:
  0  ok — check the `paid_only` flag: premium problems have empty description
  1  usage error
  2  problem not found
  3  network / HTTP error
"""

import html as html_lib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

GRAPHQL_URL = "https://leetcode.com/graphql"
INDEX_URL = "https://leetcode.com/api/problems/all/"
INDEX_CACHE = os.path.join(os.environ.get("TMPDIR") or "/tmp", "jk-leetcode-index.json")
INDEX_TTL = 24 * 60 * 60  # seconds
HTTP_TIMEOUT = 15

# Code snippets worth keeping: canonical signatures straight from LeetCode.
WANTED_LANGS = {"typescript", "javascript", "java", "csharp", "python3", "go", "rust", "cpp"}

HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) jk-leetcode-problem/1.0",
}

QUESTION_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    questionFrontendId
    title
    titleSlug
    difficulty
    isPaidOnly
    content
    hints
    similarQuestions
    exampleTestcases
    topicTags { name slug }
    codeSnippets { lang langSlug code }
  }
}
"""

SEARCH_QUERY = """
query problemList($f: QuestionListFilterInput) {
  questionList(categorySlug: "all-code-essentials", limit: 10, filters: $f) {
    questions: data { questionFrontendId title titleSlug }
  }
}
"""


class SkillError(Exception):
    """Fatal error carrying its own exit code."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def die(code, message):
    raise SkillError(code, message)


def http_json(url, payload=None):
    """GET (payload=None) or POST a JSON body; return the parsed response."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        die(3, f"HTTP {exc.code} from {url}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        die(3, f"network error: {exc}")


def html_to_text(raw):
    """Convert the problem description HTML into readable plain text."""
    text = re.sub(r"<br\s*/?>", "\n", raw)
    text = re.sub(r"</p>", "\n\n", text)
    text = re.sub(r"<pre[^>]*>", "\n", text)
    text = re.sub(r"</pre>", "\n", text)
    text = re.sub(r"<li[^>]*>", "• ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def load_index():
    """Return the {frontend_id: slug} map, cached for INDEX_TTL seconds."""
    if os.path.exists(INDEX_CACHE) and time.time() - os.path.getmtime(INDEX_CACHE) < INDEX_TTL:
        with open(INDEX_CACHE, encoding="utf-8") as fh:
            return json.load(fh).get("pairs", {})

    doc = http_json(INDEX_URL)
    pairs = {}
    for entry in doc.get("stat_status_pairs", []):
        stat = entry.get("stat", {})
        frontend_id = stat.get("frontend_question_id")
        slug = stat.get("question__title_slug")
        if frontend_id is not None and slug:
            pairs[str(frontend_id)] = slug

    try:
        with open(INDEX_CACHE, "w", encoding="utf-8") as fh:
            json.dump({"pairs": pairs}, fh)
    except OSError:
        pass  # cache write is best-effort
    return pairs


def search_slug(keyword):
    """GraphQL keyword fallback when the problems index is unreachable."""
    doc = http_json(GRAPHQL_URL, {"query": SEARCH_QUERY, "variables": {"f": {"searchKeywords": keyword}}})
    questions = (doc.get("data") or {}).get("questionList", {}).get("questions") or []
    for question in questions:
        if str(question.get("questionFrontendId")) == keyword:
            return question.get("titleSlug")
    die(2, f"no LeetCode problem matches '{keyword}'")


def resolve_slug(raw):
    """Extract or resolve the title slug from any accepted input form."""
    url_match = re.search(r"leetcode\.(?:com|cn)/problems/([a-z0-9-]+)", raw)
    if url_match:
        return url_match.group(1)
    if raw.isdigit():
        try:
            pairs = load_index()
        except SkillError:
            return search_slug(raw)
        if raw in pairs:
            return pairs[raw]
        return search_slug(raw)
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", raw):
        return raw
    die(1, f"unrecognized problem reference: '{raw}' (want numeric id, slug, or leetcode.com URL)")


def fetch_question(slug):
    doc = http_json(GRAPHQL_URL, {"query": QUESTION_QUERY, "variables": {"titleSlug": slug}})
    question = (doc.get("data") or {}).get("question")
    if not question:
        die(2, f"LeetCode returned no problem for slug '{slug}'")

    try:
        similar = json.loads(question.get("similarQuestions") or "[]")
    except (TypeError, json.JSONDecodeError):
        similar = []

    snippets = {
        snippet["langSlug"]: snippet["code"]
        for snippet in question.get("codeSnippets") or []
        if snippet.get("langSlug") in WANTED_LANGS and snippet.get("code")
    }

    content = question.get("content") or ""
    return {
        "frontend_id": question.get("questionFrontendId"),
        "question_id": question.get("questionId"),
        "title": question.get("title"),
        "slug": question.get("titleSlug"),
        "url": f"https://leetcode.com/problems/{question.get('titleSlug')}/",
        "difficulty": question.get("difficulty"),
        "paid_only": bool(question.get("isPaidOnly")),
        "description": html_to_text(content) if content else "",
        "topic_tags": [tag["name"] for tag in question.get("topicTags") or []],
        "hints": question.get("hints") or [],
        "similar": [
            {"title": item.get("title"), "slug": item.get("titleSlug"), "difficulty": item.get("difficulty")}
            for item in similar
        ],
        "example_testcases": question.get("exampleTestcases") or "",
        "code_snippets": snippets,
    }


def main(argv):
    if len(argv) != 2:
        die(1, "usage: fetch_problem.py <numeric-id | slug | leetcode-url>")
    slug = resolve_slug(argv[1].strip())
    result = fetch_question(slug)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main(sys.argv)
    except SkillError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(exc.code)
