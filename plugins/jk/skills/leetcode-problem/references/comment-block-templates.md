# Comment Block Templates

Exact format for generated problem files. Load this file whenever generating
or editing problem files. Templates below use Vietnamese (the default user
language) — translate the human labels when the session's user language
differs. Emoji markers, section order, and layout are FIXED.

## Layout rules (all languages)

- One **shared header block** at the top of the solution file, one
  **solve doc block** above each `solve` stub.
- Separate the header block, each solve block, and each function by **one
  blank line** so the file breathes.
- Header box width: 72 `═` characters. Do not resize per language.
- Section labels are UPPERCASE in the user language, e.g. `TÓM TẮT`,
  `VÍ DỤ`, `KEYWORDS / KỸ THUẬT`.
- Problem title, URL, complexity classes, and keywords stay in **English**
  (canonical industry terms).
- **Variant naming**: `solve`, `solve2`, `solve3`, … — no underscores, digits
  appended directly, case follows each language's linter convention
  (camelCase for TS/Java, PascalCase for C#). Underscored names like
  `solve_2` trip Checkstyle's `MethodName` pattern in Java and other
  naming linters — never generate them.

## Header block — required sections, fixed order

| # | Marker | Section | Content |
|---|--------|---------|---------|
| 1 | 🧩 | Title line | `LEETCODE #<4-digit-id> · <UPPERCASE TITLE> · <Difficulty>` (+ `🔒 PREMIUM` when paid) |
| 2 | 🔗 | URL | `https://leetcode.com/problems/<slug>/` |
| 3 | 📋 | Summary | 2–4 lines, own words, short + easy to understand. No copy-paste of the statement |
| 4 | 📥📤 | Input / Output | One line per param (`name: type — role`), then `→ return type — meaning` |
| 5 | 💡 | Example (happy case) | `Input : …` / `Output: …` / `← vì …` (why, one line). ONE example only |
| 6 | ⏱ | Complexity ladder | Every viable Time complexity class, one row per class — ordering rule below |
| 7 | 🔑 | Keywords / techniques | English canonical terms, `·` separated. Source: LeetCode topic tags + approach |
| 8 | ⚠️ | Notable constraints | Only constraints that change the approach choice, each with a short implication note |

**Complexity ladder rules** (section 6):

- List every distinct Time complexity class the problem can be solved with,
  one row per class: `O(n²) — brute force: duyệt mọi cặp (i, j)`.
- Order rows **slowest → fastest** so the ladder reads as a progression to
  climb. Mark the optimal (target) class with `⭐`.
- One-line hint per row naming the technique — never full solution steps.

## Solve doc block — required fields

```
🧠 Cách <n> — <Approach Name (English)>     ← matches ladder row n
Ý tưởng: 1–2 lines, the core move only
⏱ Time: O(...) · 💾 Space: O(...)
Native doc tags (@param/@returns or <param>/<returns>) in user language
```

## TypeScript (vitest) — full example

```ts
/* ═══════════════════════════════════════════════════════════════════════
 * 🧩 LEETCODE #0001 · TWO SUM · Easy
 * 🔗 https://leetcode.com/problems/two-sum/
 * ═══════════════════════════════════════════════════════════════════════
 *
 * 📋 TÓM TẮT
 * Cho mảng số nguyên `nums` và số nguyên `target`, trả về chỉ số của hai
 * số cộng lại đúng bằng `target`. Luôn tồn tại đúng một đáp án, mỗi phần
 * tử chỉ được dùng một lần.
 *
 * 📥 INPUT → 📤 OUTPUT
 *   nums   : number[]   — mảng số nguyên đầu vào
 *   target : number     — tổng cần tìm
 *   → [number, number]  — chỉ số [i, j] của hai số hợp lệ
 *
 * 💡 VÍ DỤ
 *   Input : nums = [2, 7, 11, 15], target = 9
 *   Output: [0, 1]
 *   ← vì nums[0] + nums[1] = 2 + 7 = 9
 *
 * ⏱ COMPLEXITY LADDER (các mức Time O() có thể giải được)
 *   1. O(n²)      — brute force: duyệt mọi cặp (i, j)
 *   2. O(n·log n) — sort + two pointers (mất thứ tự gốc, phải lưu index)
 *   3. O(n)       — hash table một lượt duyệt: tra complement   ⭐ tối ưu
 *
 * 🔑 KEYWORDS / KỸ THUẬT
 *   Array · Hash Table · One-Pass Hash Map
 *
 * ⚠️ RÀNG BUỘC ĐÁNG CHÚ Ý
 *   2 ≤ nums.length ≤ 10⁴      — O(n²) vẫn AC được nhưng chậm
 *   Chỉ tồn tại một đáp án      — được phép throw nếu không tìm thấy
 * ═══════════════════════════════════════════════════════════════════════ */

/**
 * 🧠 Cách 1 — Brute Force
 *
 * Ý tưởng: duyệt mọi cặp chỉ số (i, j) với i < j, trả về cặp đầu tiên
 * có nums[i] + nums[j] === target.
 *
 * ⏱ Time: O(n²) · 💾 Space: O(1)
 *
 * @param nums   — mảng số nguyên đầu vào
 * @param target — tổng cần tìm
 * @returns chỉ số [i, j] của hai phần tử cộng lại bằng target
 * @throws Error khi không tồn tại cặp nào hợp lệ
 */
export const solve = (nums: number[], target: number): [number, number] => {
	throw new Error('chưa giải — implement tại đây')
}

/**
 * 🧠 Cách 2 — Hash Table (một lượt duyệt)
 *
 * Ý tưởng: với mỗi nums[i], tra complement = target - nums[i] trong map;
 * chưa có thì lưu nums[i] → i vào map rồi đi tiếp.
 *
 * ⏱ Time: O(n) · 💾 Space: O(n)
 *
 * @param nums   — mảng số nguyên đầu vào
 * @param target — tổng cần tìm
 * @returns chỉ số [i, j] của hai phần tử cộng lại bằng target
 * @throws Error khi không tồn tại cặp nào hợp lệ
 */
export const solve2 = (nums: number[], target: number): [number, number] => {
	throw new Error('chưa giải — implement tại đây')
}
```

- Indentation: tabs (repo `.editorconfig` for web languages).
- Stub body: **empty per the skill contract** — but TypeScript's return type
  requires a value, so the single `throw` line above is the canonical
  placeholder. Never write partial logic.

## Java (JUnit 5) — fragments

Header: same box, but plain block comment `/* ═══ */ … */`. Each solve uses
Javadoc. Class skeleton:

```java
package com.jjuidev.jsl.problems._0001_two_sum;

/* ═══ header block — same sections as TypeScript ═══ */

/**
 * 🧠 Cách 1 — Brute Force.
 *
 * Ý tưởng: duyệt mọi cặp (i, j) với i &lt; j.
 *
 * ⏱ Time: O(n²) · 💾 Space: O(1)
 *
 * @param nums   mảng số nguyên đầu vào
 * @param target tổng cần tìm
 * @return chỉ số [i, j] của hai phần tử cộng lại bằng target
 * @throws IllegalArgumentException khi không tồn tại cặp hợp lệ
 */
public int[] solve(int[] nums, int target) {
    throw new IllegalArgumentException("chưa giải — implement tại đây");
}
```

- Indentation: 4 spaces. Escapes in Javadoc: `<` `>` `&` → `&lt;` `&gt;` `&amp;`.
- Methods: `solve`, `solve2`, `solve3` — camelCase, no underscores
  (complies with the app's Checkstyle `MethodName` pattern).

## C# (xUnit) — fragments

Header: same box in a `/* */` block. Each solve uses XML doc comments.

```csharp
namespace Leetcode.Problems._0001_TwoSum;

/* ═══ header block — same sections as TypeScript ═══ */

/// <summary>
/// 🧠 Cách 1 — Brute Force.
///
/// Ý tưởng: duyệt mọi cặp (i, j) với i &lt; j.
///
/// ⏱ Time: O(n²) · 💾 Space: O(1).
/// </summary>
/// <param name="nums">Mảng số nguyên đầu vào.</param>
/// <param name="target">Tổng cần tìm.</param>
/// <returns>Chỉ số [i, j] của hai phần tử cộng lại bằng target.</returns>
/// <exception cref="ArgumentException">Khi không tồn tại cặp hợp lệ.</exception>
public int[] Solve(int[] nums, int target)
{
	throw new NotImplementedException("chưa giải — implement tại đây");
}
```

- Indentation: tabs. Methods: `Solve`, `Solve2`, `Solve3` (PascalCase per
  repo convention).
- XML doc: `<` `>` `&` must be escaped.

## Other languages (future apps)

| Language | Doc format | Header block | Indent |
|----------|-----------|--------------|--------|
| Python   | docstring `"""…"""` | `# ═══` box lines | 4 spaces |
| Go       | `//` doc comment | `// ═══` box lines | tabs |
| Rust     | `///` doc comment | `// ═══` box lines | 4 spaces |

## Identical scaffold — every language

Every language app gets the SAME output shape — duplication across
languages is accepted and intended. Only the syntax differs (JSDoc vs
Javadoc vs XML doc, indentation, shell); the CONTENT is identical: same
header sections, same solve count/order, same doc-block fields, same test
case set. Derive each language's signature types from the fetched
`code_snippets` for that language.

## Test files

Every generated language gets a test file — see
`references/test-templates.md` for the shared rules and the TypeScript /
Java / C# patterns.
