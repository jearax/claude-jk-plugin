# Junk catalog (tier 2, user-owned)

The owner's own definition of a junk comment. It outranks `antislop.md`: a verdict here stops evaluation, so tier 3 never sees the comment. When a comment matches both sections, Keep wins. Keep comments are never tightened.

Entry format: **Pattern**, **Example** (a real line; it matters more than the description), **Fix** (only when it is not "delete").

Two principles drive every entry:

1. **A comment says why, not what.** The code already says what it does.
2. **The reader is a mid-level developer in this file's stack.** Judge "obvious" against that reader, not a beginner.

## Junk

### States what, not why
- **Pattern:** the comment only describes what the code does, or describes nothing concrete, with no reason, intent, or constraint. Applies at any complexity: trivial expressions, stack idioms, standard constructs, textbook algorithms, boilerplate and stubs, step-by-step walkthroughs of complex code.
- **Example:**
  - Trivial code: `// Sum a and b` above `sum(a + b)`; `// Check if list is empty` above `if (!list.length)`
  - Stack idioms: `// Use useEffect to fetch data on mount`; `// Create a new Express router` above `express.Router()`
  - Standard constructs: `// Iterate over the users` above `users.forEach(...)`; `// Filter active items` above `.filter(x => x.active)`
  - Textbook algorithms: `// Binary search: compare mid with target, move left or right`; `// Swap the two elements` above `[a[i], a[j]] = [a[j], a[i]]`
  - Boilerplate and stubs: `// Your code here`; `// Implement logic`; `// Constructor` above `constructor() {}`
  - Complex code: `// Map orders to DTOs and filter out cancelled ones` above `orders.map(toDto).filter(o => o.status !== 'cancelled')`
- **Fix:** delete. When a why is mixed into a what, keep only the why: `// Fetch user, then cache it for 5 minutes because the profile API is rate-limited` → `// Cached: the profile API is rate-limited`

## Keep

### Explains why, not what
- **Pattern:** a reason, constraint, or decision the code cannot show: business rule, domain invariant, workaround, platform quirk, non-obvious algorithm or data-structure choice. Keep it even above simple code. A comment that also narrates the what falls to *States what, not why* and keeps only its why.
- **Example:** `// Đơn hàng quá 30 ngày không được hoàn tiền`; `setTimeout(focus, 0) // Safari needs a tick before focus`; `// Lock order: account → wallet → ledger, otherwise concurrent transfers deadlock`

### Public API contract
- **Pattern:** a doc comment on an exported function, class, endpoint, or config stating its contract for callers who never read the body: units, ranges, return semantics, errors, side effects. A doc comment that only echoes the signature is still junk.
- **Example:** `/** Returns the price in cents; throws RangeError when qty < 1. */` above `export function quote(qty)`
