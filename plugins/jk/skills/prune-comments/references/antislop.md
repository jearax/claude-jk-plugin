# Antislop baseline (tier 3)

Adapted from the `antislop-code` skill in [miqdadbadjuber/anti-slop](https://github.com/miqdadbadjuber/anti-slop) (MIT). Upstream core references were removed and AI-specific patterns were added. This tier only sees comments that tiers 0–2 left undecided.

The test behind every pattern: if deleting the comment loses no information the code does not already show, it is junk.

## Junk

| Pattern | Example | Fix |
|---|---|---|
| Decorative separator | `// ========== AUTH ==========`, `/* ---- ROUTES ---- */` | Delete; keep a plain one-line label only if it names something the code does not |
| Restating the obvious | `// Initialize count` above `let count = 0`; `const age = 25; // age is 25` | Delete |
| Workflow narration | `// Step 1: Validate input`, `// First...`, `// Finally...` | Delete |
| Empty label | `// Main logic`, `// Helper function`, `// Error handling`, `// Note: this is important` | Delete |
| Vague TODO | `// TODO: improve this`, `// Add more validation` | Delete; keep a TODO that names a concrete task |
| Signature echo | `@param price The price.` / `@returns The total.` on `calcTotal(price)` | Delete the echoing tags; keep tags that add rules, units, edge cases, side effects |
| Decorative emoji | `// ✅ Validation`, `// 🚀 Fast path` | Delete the emoji; delete the line if nothing remains |
| End marker | `} // end if`, `# End of function` | Delete |
| Change-log about the edit | `// Updated to fix the bug`, `// Added new function`, `// Changed per request`, `// Fixed: now handles null` | Delete; history belongs in git |
| Placeholder or disclaimer | `// In a real app you would...`, `// This is a simplified implementation`, `// Replace with your actual logic` | Delete when the code is real; when the code really is a stub, keep one line saying what is missing |

## Keep

Comments that explain what the code cannot show stay at this tier, and may be tightened:

- business rules and intent
- architectural decisions
- security considerations
- performance trade-offs
- concurrency behavior
- protocol details and API contracts
- workarounds, with their issue/CVE/PR link
- edge cases and assumptions

Example that stays:

```js
// Stripe may retry webhook deliveries for up to three days.
// Ignore duplicate events using the event ID.
```
