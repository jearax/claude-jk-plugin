# IT Term Verification

When to look up IT terms/stack before translating, how to cite, and what to do when you cannot confirm. Keep all output in the skill's target language.

## Decision: Lookup or Not?

| Signal in the term | Action |
|---|---|
| Foundational / universally known (React hooks, JWT, CRUD, REST, OAuth, CI/CD, Docker, webhook) | Translate from knowledge. No lookup. |
| Standard library / core API of a major framework | Translate from knowledge. Optional quick check if version matters. |
| Niche library, specific option/flag, vendor error code, version-specific behavior, recently released API | **Lookup required** — `WebSearch` then `WebFetch` official docs. |
| Obscure error code / ambiguous acronym with multiple meanings | **Lookup required.** If still ambiguous, mark unverified. |
| Cannot find authoritative source | Mark `[chưa xác nhận — verify]`. Do not guess. |

Rule of thumb: if a confident reader could reasonably dispute your gloss, look it up.

## How to Look Up

1. `WebSearch` the term plus the framework/version (e.g. `"Vite optimizeDeps include"`, `"Postgres SQLSTATE 23505"`).
2. Prefer official docs: vendor domain (react.dev, nodejs.org, developer.mozilla.org, postgresql.org, the library's own docs site), then the repo's README.
3. `WebFetch` the doc page and read the relevant section. Do not rely on search snippets for precise semantics.
4. Record the exact URL you actually read.

## Citation Format

Cite in the **Notes** section, one entry per verified term:

```
- <term> — <Vietnamese gloss / short explanation>  [src: <doc-url>]
```

Examples:
```
- SQLSTATE 23505 — vi phạm ràng buộc duy nhất (unique violation)  [src: https://www.postgresql.org/docs/current/errcodes-appendix.html]
- optimizeDeps.include — ép Vite tiền gói (pre-bundle) các dependency này  [src: https://vite.dev/config/dep-optimization-options.html#optimizedeps-include]
```

Keep glosses short (one line). If a term needs more explanation, add a second clause after an em-dash.

## Fallback When Lookup Fails / Is Unavailable

- Mark inline: render the term and append ` [chưa xác nhận — verify]`.
- In Notes, list it under a separate `⚠️ Chưa xác nhận` subsection with what you tried.
- State plainly what is uncertain. Never silently fill the gap with a plausible-sounding guess.

## Sensitive Content During Lookup

Before any `WebSearch` / `WebFetch`, redact from the query and any pasted context:
- API keys, tokens, bearer values, passwords
- Connection strings, `.env` values
- PII (emails, phone numbers, real names) unless they are public figures / author attributions

Translate such values in place as `<redacted>`. Never send them to an external service.
