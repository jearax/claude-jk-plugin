# Junk catalog (tier 2, user-owned)

The owner's own definition of a junk comment. It outranks `antislop.md`: a verdict here stops evaluation, so tier 3 never sees the comment. When a comment matches both sections, Keep wins.

Keep verdicts here also block tightening: the comment stays exactly as written.

Entry format: **Pattern** (how to recognize it), **Example** (a real line; it matters more than the description), **Fix** (only when it is not "delete"), **Regex** (optional, single backticked regex matched case-insensitively against the comment text without its marker; the realtime hook uses it, so add one only when it cannot misfire on a valuable comment).

These definitions are relative, not absolute. Two principles drive every entry:

1. **A comment says why, not what.** The code already says what it does; a comment earns its place only by giving the reason, intent, or constraint behind it.
2. **The reference reader is a mid-level developer in this file's stack.** Judge "obvious" against that reader, not a beginner. Comments are reserved for complex logic and business logic, and even there they explain why.

## Junk

### States what, not why
- **Pattern:** a comment whose content is only a description of what the code does, with no reason, intent, or constraint, whatever the complexity of the code under it. Applies to step-by-step walkthroughs of complex code too.
- **Example:** `// Map orders to DTOs and filter out cancelled ones` above `orders.map(toDto).filter(o => o.status !== 'cancelled')`; `// Get the token from the header, decode it, and attach the user to the request` above an auth middleware
- **Fix:** delete. When a why is mixed into a what, keep only the why: `// Fetch user, then cache it for 5 minutes because the profile API is rate-limited` → `// Cached: the profile API is rate-limited`

### Narrates trivial code
- **Pattern:** a comment describing what an ordinary expression or statement does: arithmetic, assignment, a return, a simple condition, a standard library call.
- **Example:** `// Sum a and b` above `sum(a + b)`; `// Return the user` above `return user`; `// Check if list is empty` above `if (!list.length)`
- **Regex:** `^(add|sum|increment|decrement|multiply|subtract|divide)\s+\w+(\s+(and|by|to|from|with)\s+\w+)?\W*$`

### Explains code a mid-level dev already reads
- **Pattern:** a comment that paraphrases code a mid-level developer in this stack reads at a glance: framework idioms, common hooks, routine CRUD, standard error handling, typical config. Judge against the stack, not against a beginner.
- **Example:** `// Use useEffect to fetch data on mount` above a standard `useEffect`; `// Create a new Express router` above `express.Router()`; `// Catch errors and log them` above `catch (e) { logger.error(e) }`

### Describes placeholder, skeleton, or boilerplate code
- **Pattern:** comments on scaffolding: stub bodies, generated skeletons, framework boilerplate, "fill this in" markers that describe no concrete task.
- **Example:** `// Your code here`; `// Implement logic`; `// Add your implementation here`; `// Default export` above `export default App`; `// Constructor` above `constructor() {}`
- **Regex:** `^(todo:?\s*)?(implement( me| this| logic)?|(your|add( your)?)\s+(code|logic|implementation)\s+here)\W*$`

### Narrates an industry-standard construct
- **Pattern:** a comment explaining a construct every developer knows: index loops, iteration over a collection, early return, null checks, try/catch, map/filter/reduce.
- **Example:** `// Loop from 0 to length, and handle elements` above `for (let i = 0; i < a.length; i++)`; `// Iterate over the users` above `users.forEach(...)`; `// Filter active items` above `.filter(x => x.active)`
- **Regex:** `^(loop|iterate)\s+(from\s+\d+\s+to\b|(through|over)\s+(the\s+|each\s+|all\s+)?\w+\W*$)`

### Explains a textbook algorithm
- **Pattern:** a comment that names or walks through a standard algorithm (search, sort, swap, two pointers, BFS/DFS, binary search) step by step.
- **Example:** `// Binary search: compare mid with target, move left or right` above a plain binary search; `// Swap the two elements` above `[a[i], a[j]] = [a[j], a[i]]`; `// Bubble sort the array`

## Keep

### Explains why, not what
- **Pattern:** a comment that consists of a reason, constraint, or decision the code cannot show: a business rule, a domain invariant, a workaround, a platform quirk, a non-obvious choice of algorithm or data structure. Keep it even when the code under it is simple. A comment that also narrates what the code does is not a pure why: it falls to *States what, not why*, whose Fix keeps only the why part.
- **Example:** `// Đơn hàng quá 30 ngày không được hoàn tiền`; `setTimeout(focus, 0) // Safari needs a tick before focus`; `// Binary search is safe here: rows come sorted by createdAt from the index`; `// Lock order: account → wallet → ledger, otherwise concurrent transfers deadlock`

### Public API contract
- **Pattern:** a doc comment on an exported function, class, endpoint, or config that states its contract for callers who never read the body: units, accepted ranges, return semantics, errors thrown, side effects, thread-safety. This is the one place a "what" stays, because the reader is the caller, not the maintainer. A doc comment that only echoes the signature is still junk (antislop signature echo).
- **Example:** `/** Returns the price in cents; throws RangeError when qty < 1. */` above `export function quote(qty)`
