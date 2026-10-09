# Tighten rules

Applies only to comments kept at tier 3 or matched by no tier. Tier 0, `--keep`, and `junk-catalog.md` Keep comments are never rewritten. User rules come first; the baseline fills the gaps.

## User rules

### Keep the why, drop the what
- **Rule:** when a kept comment mixes a description of what the code does with the reason behind it, cut the description and keep the reason. If nothing remains but a what, the comment was junk; leave the deletion decision to the tier flow and do not invent a reason.
- **Example:** `// Retry 3 times with backoff since the payment gateway drops ~1% of requests` → `// Payment gateway drops ~1% of requests`

## Baseline

Adapted from antislop-code "How It Should Read" ([anti-slop](https://github.com/miqdadbadjuber/anti-slop), MIT), with the issue-number and three-line rules relaxed.

- **Meaning is fixed.** Tightening removes words, never facts. If you cannot shorten a comment without losing a fact or nuance, leave it unchanged.
- **Every line carries a new fact.** Cut lines that restate the previous one, pad a one-line fact into a paragraph, or chain "because X, so Y, therefore Z". There is no fixed line cap.
- **Keep links that explain a workaround.** Issue, CVE, PR, and upstream bug links stay. Version history and narrative about how the bug was found go.
- **One comment per logical block.** When consecutive lines each carry a trivial comment, merge what has value into one comment above the block and drop the rest.
- **Keep the original language.** A Vietnamese comment stays Vietnamese; do not translate.
- **Plain developer voice.** Sentence case, no ALL CAPS shouting, no "This function is responsible for...".

Example:

```ts
// Before
// This is a workaround because Safari (see https://bugs.webkit.org/show_bug.cgi?id=123)
// does not fire the resize event when the keyboard opens, which caused issues
// in version 2.3 when we first noticed the layout breaking on iOS devices.

// After
// Safari skips resize when the keyboard opens: https://bugs.webkit.org/show_bug.cgi?id=123
```
