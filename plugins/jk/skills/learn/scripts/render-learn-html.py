#!/usr/bin/env python3
"""Render a /jk:learn Markdown note into one self-contained HTML page.

Deterministic and fast: the agent writes Markdown only; this script wraps it in
a fixed HTML shell with per-mode layout. Markdown is rendered in the browser by
marked + DOMPurify, code by highlight.js, diagrams by mermaid (loaded only when
a mermaid block exists). If the CDN is unreachable, the raw Markdown is shown.

Usage:
  render-learn-html.py --in note.md --out ./zod-learn.html --mode cheatsheet \
      [--title "Zod - Cheat Sheet"] [--lang vi] [--open]
"""
import argparse
import html
import json
import sys
import webbrowser
from pathlib import Path

MODES = {"overview", "usage", "workflow", "internals", "cheatsheet", "docs", "eli"}
CDN = "https://cdn.jsdelivr.net/npm"

PAGE = """<!doctype html>
<html lang="{lang}" data-mode="{mode}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{cdn}/highlight.js@11/styles/github.min.css" media="(prefers-color-scheme: light)">
<link rel="stylesheet" href="{cdn}/highlight.js@11/styles/github-dark.min.css" media="(prefers-color-scheme: dark)">
<style>
:root {{ --bg:#fff; --fg:#1f2328; --muted:#59636e; --line:#d1d9e0; --soft:#f6f8fa; --accent:#0969da; --ok:#1a7f37; --warn:#9a6700; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#0d1117; --fg:#e6edf3; --muted:#9198a1; --line:#3d444d; --soft:#151b23; --accent:#4493f8; --ok:#3fb950; --warn:#d29922; }}
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans",sans-serif; }}
.layout {{ display:grid; grid-template-columns:minmax(0,1fr); max-width:1180px; margin:0 auto; padding:24px 16px 64px; gap:32px; }}
.has-toc .layout {{ grid-template-columns:220px minmax(0,1fr); }}
nav.toc {{ display:none; }}
.has-toc nav.toc {{ display:block; position:sticky; top:16px; align-self:start; max-height:calc(100vh - 32px); overflow:auto; font-size:14px; }}
nav.toc a {{ display:block; padding:3px 0 3px 10px; color:var(--muted); text-decoration:none; border-left:2px solid var(--line); }}
nav.toc a.h3 {{ padding-left:22px; }}
nav.toc a:hover {{ color:var(--accent); border-color:var(--accent); }}
main {{ min-width:0; }}
h1 {{ font-size:2em; margin:0 0 .6em; line-height:1.25; }}
h2 {{ margin-top:2em; padding-bottom:.3em; border-bottom:1px solid var(--line); }}
a {{ color:var(--accent); }}
code {{ font:0.88em ui-monospace,SFMono-Regular,Menlo,monospace; background:var(--soft); padding:.15em .35em; border-radius:6px; }}
pre {{ position:relative; background:var(--soft); border:1px solid var(--line); border-radius:8px; padding:14px; overflow:auto; }}
pre code {{ background:none; padding:0; }}
pre .copy {{ position:absolute; top:8px; right:8px; font-size:12px; padding:2px 8px; border:1px solid var(--line); border-radius:6px; background:var(--bg); color:var(--muted); cursor:pointer; }}
table {{ border-collapse:collapse; width:100%; display:block; overflow:auto; margin:1em 0; }}
th, td {{ border:1px solid var(--line); padding:6px 12px; text-align:left; vertical-align:top; }}
th {{ background:var(--soft); }}
blockquote {{ margin:1em 0; padding:8px 16px; border-left:4px solid var(--accent); background:var(--soft); border-radius:0 8px 8px 0; }}
details {{ border:1px solid var(--line); border-radius:8px; padding:8px 14px; }}
summary {{ cursor:pointer; font-weight:600; }}
.mermaid {{ text-align:center; background:var(--soft); border-radius:8px; padding:12px; }}
pre.raw {{ white-space:pre-wrap; }}
/* workflow: steps as a timeline, blockquotes are step checks */
[data-mode="workflow"] h2 {{ border:none; border-left:4px solid var(--accent); padding:4px 0 4px 14px; }}
[data-mode="workflow"] blockquote {{ border-left-color:var(--ok); }}
/* internals: emphasize diagrams and trade-off tables */
[data-mode="internals"] .mermaid {{ padding:20px; }}
/* cheatsheet: dense, filterable */
[data-mode="cheatsheet"] body {{ font-size:14px; }}
[data-mode="cheatsheet"] .layout {{ max-width:1400px; }}
[data-mode="cheatsheet"] h2 {{ margin-top:1.4em; }}
[data-mode="cheatsheet"] td, [data-mode="cheatsheet"] th {{ padding:4px 8px; }}
.filter {{ display:none; }}
[data-mode="cheatsheet"] .filter {{ display:block; position:sticky; top:0; z-index:1; background:var(--bg); padding:8px 0; }}
.filter input {{ width:100%; padding:8px 12px; font-size:15px; border:1px solid var(--line); border-radius:8px; background:var(--soft); color:var(--fg); }}
@media (max-width: 860px) {{ .has-toc .layout {{ grid-template-columns:minmax(0,1fr); }} .has-toc nav.toc {{ display:none; }} }}
</style>
</head>
<body>
<div class="layout">
<nav class="toc" aria-label="Table of contents"></nav>
<main>
<div class="filter"><input type="search" placeholder="Filter…" aria-label="Filter rows"></div>
<article id="content"><pre class="raw">{raw}</pre></article>
</main>
</div>
<script src="{cdn}/marked@15/marked.min.js"></script>
<script src="{cdn}/dompurify@3/dist/purify.min.js"></script>
<script src="{cdn}/@highlightjs/cdn-assets@11/highlight.min.js"></script>
<script>
(function () {{
  var md = {md_json};
  var mode = document.documentElement.dataset.mode;
  var root = document.getElementById("content");
  if (!window.marked || !window.DOMPurify) return; // CDN unreachable: raw Markdown stays visible

  root.innerHTML = DOMPurify.sanitize(marked.parse(md));

  root.querySelectorAll("pre code").forEach(function (el) {{
    if (el.classList.contains("language-mermaid")) return;
    if (window.hljs) hljs.highlightElement(el);
    var btn = document.createElement("button");
    btn.className = "copy"; btn.type = "button"; btn.textContent = "Copy";
    btn.onclick = function () {{
      navigator.clipboard.writeText(el.innerText).then(function () {{
        btn.textContent = "Copied"; setTimeout(function () {{ btn.textContent = "Copy"; }}, 1200);
      }});
    }};
    el.parentElement.appendChild(btn);
  }});

  var diagrams = root.querySelectorAll("pre code.language-mermaid");
  if (diagrams.length) {{
    diagrams.forEach(function (el) {{
      var div = document.createElement("div");
      div.className = "mermaid"; div.textContent = el.textContent;
      el.parentElement.replaceWith(div);
    }});
    var s = document.createElement("script");
    s.src = "{cdn}/mermaid@11/dist/mermaid.min.js";
    s.onload = function () {{
      var dark = matchMedia("(prefers-color-scheme: dark)").matches;
      mermaid.initialize({{ startOnLoad: false, theme: dark ? "dark" : "default", securityLevel: "strict" }});
      mermaid.run({{ querySelector: ".mermaid" }});
    }};
    document.body.appendChild(s);
  }}

  if (["usage", "workflow", "internals"].indexOf(mode) !== -1) {{
    var heads = root.querySelectorAll("h2, h3");
    if (heads.length > 3) {{
      var nav = document.querySelector("nav.toc");
      heads.forEach(function (h, i) {{
        h.id = h.id || "s" + i;
        var a = document.createElement("a");
        a.href = "#" + h.id; a.textContent = h.textContent; a.className = h.tagName.toLowerCase();
        nav.appendChild(a);
      }});
      document.body.classList.add("has-toc");
    }}
  }}

  if (mode === "cheatsheet") {{
    document.querySelector(".filter input").addEventListener("input", function (e) {{
      var q = e.target.value.toLowerCase();
      root.querySelectorAll("tbody tr, li").forEach(function (row) {{
        row.style.display = !q || row.textContent.toLowerCase().indexOf(q) !== -1 ? "" : "none";
      }});
    }});
  }}
}})();
</script>
</body>
</html>
"""


def render(markdown: str, mode: str, title: str, lang: str) -> str:
    """Build the HTML page. Markdown is embedded as a JSON string, so it can
    never close the surrounding <script> tag."""
    md_json = json.dumps(markdown, ensure_ascii=False).replace("</", "<\\/")
    return PAGE.format(
        lang=html.escape(lang, quote=True),
        mode=mode,
        title=html.escape(title),
        raw=html.escape(markdown),
        md_json=md_json,
        cdn=CDN,
    )


def _title_from(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render a /jk:learn Markdown note to HTML.")
    parser.add_argument("--in", dest="src", required=True, help="Markdown file to render")
    parser.add_argument("--out", required=True, help="HTML file to write")
    parser.add_argument("--mode", required=True, choices=sorted(MODES))
    parser.add_argument("--title", help="Page title (default: first '# ' heading)")
    parser.add_argument("--lang", default="en", help="HTML lang attribute, e.g. vi")
    parser.add_argument("--open", action="store_true", help="Open the page in the default browser")
    args = parser.parse_args(argv)

    src = Path(args.src)
    if not src.is_file():
        print(f"error: input not found: {src}", file=sys.stderr)
        return 1
    markdown = src.read_text(encoding="utf-8")
    title = args.title or _title_from(markdown, src.stem)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(markdown, args.mode, title, args.lang), encoding="utf-8")
    print(str(out.resolve()))

    if args.open:
        webbrowser.open(out.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
