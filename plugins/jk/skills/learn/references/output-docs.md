# Output Template: Docs Mode

Use this template when `mode: docs`. Answers one question: **"What should I read in the official documentation, and in what order?"** A reading map of the official sources, not a summary of them.

## Template Structure

```markdown
# {Topic} - Documentation Map

## Official Sources
| Source | URL | Use it for |
|--------|-----|------------|
| Docs site | {url} | {purpose} |
| Repository | {url} | {README, examples, issues} |
| Changelog / releases | {url} | {tracking breaking changes} |
| {API reference / spec / llms.txt} | {url} | {purpose} |

**Current version:** {version} ({release date}) — the docs below apply to this version.

## Reading Order

### 1. Start here
- [{Page title}]({url}) — {what you get from it} (~{minutes} min)
- [{Page title}]({url}) — {what you get from it}

### 2. Core concepts
- [{Page title}]({url}) — {what you get from it}

### 3. When you build
- [{Page title}]({url}) — {read when you need X}

### 4. Reference (look up, do not read end to end)
- [{Page title}]({url}) — {what to look up here}

## Safe to Skip at First
- [{Page title}]({url}) — {why it can wait}

## Docs Pitfalls
- {Outdated or version-specific pages, confusing naming, legacy APIs that still appear in search results}
```

## Section Guidelines

- **Verified links only**: open every URL (`WebFetch`) before listing it. Drop any link that fails or redirects to an unrelated page. Never construct a URL from a guessed path.
- **Official first**: list only official docs, repos, specs, and changelogs. Community material appears only when the official docs lack a topic, and is labeled as community.
- **Version**: state the current version from the releases page or changelog, and flag pages that cover a different major version.
- **Each link has a reason**: one line on what the reader gets from it or when to read it.
- **Visuals**: follow `visuals.md`; a reading-path diagram is optional.
- **Order by learning need**: start → concepts → building → reference. Reference pages are for lookup, so say so.

## Not in This Mode

- No summary of the page contents → the other modes cover the content itself
- No code → `usage` / `workflow`
