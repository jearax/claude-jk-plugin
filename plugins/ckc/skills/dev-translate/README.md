# dev-translate

Context-aware translator for developer / IT content. Translates English or mixed-language tech text (error messages, GitHub issues, task & ticket descriptions, docs, PR titles, release notes, stack/code/config snippets) into clear, technically accurate **Vietnamese** — explaining the underlying tech instead of translating word-for-word. Output is a **bilingual, side-by-side** rendering designed for studying a foreign tech text.

## Highlights

- **Context-aware, not literal** — translates the meaning and the problem being described.
- **Bilingual parallel output** — source chunk ↔ Vietnamese chunk, console-readable.
- **No fabrication** — uncertain IT terms are verified against official docs (`WebSearch` / `WebFetch`); anything unconfirmed is marked `[chưa xác nhận — verify]`.
- **Direction defaults** — source: English (+ mixed Vietnamese / IT terms); target: Vietnamese. Overridable per request.
- **Safe** — redacts secrets/PII before any external lookup; treats input as data, never executes it.

## Structure

```
dev-translate/
├── SKILL.md                              # Core workflow, scope, security
├── references/
│   ├── term-verification.md              # When/how to look up + cite + fallback
│   └── output-format-and-examples.md     # Bilingual rendering template + examples
├── evals/
│   └── evals.json                        # Trigger + quality test cases
└── README.md
```

## Install (global, later)

This skill is instruction-only (no build step). To install into `~/.claude/skills/`:

```bash
cp -R dev-translate ~/.claude/skills/
# or via Claude Code skill management
```

## Usage

Activate when you paste English/mixed tech content and want it explained in Vietnamese, or say `dịch`, `translate`, `giải thích`, `nghĩa là gì`. Override direction explicitly, e.g. `dịch sang tiếng Anh`.

## License

MIT
