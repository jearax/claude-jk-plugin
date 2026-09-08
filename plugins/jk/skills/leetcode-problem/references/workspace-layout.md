# Workspace Layout

Where generated files go. Layouts and formats are HARDCODED here and in
`references/comment-block-templates.md` / `references/test-templates.md` —
do NOT read existing problem files to learn conventions.

## 1. Locate the practice repo

Resolve in order — stop at the first hit:

1. CWD is inside a repo containing `apps/*-leetcode/` (or `src/problems/`).
2. Default path: `~/Documents/jearax/leetcode`.
3. Otherwise `AskUserQuestion` for the repo path.

## 2. Language set — shallow scan only

One listing pass; stop as soon as the language set is known:

```bash
ls <repo>/apps
```

- Each `apps/<name>-leetcode/` directory = one programming-language app.
- Map name → language: `ts-*` → TypeScript, `java-*` → Java, `csharp-*` →
  C#, `python-*` → Python, `go-*` → Go, `rust-*` → Rust.
- Every app found gets the SAME full scaffold — no per-language
  differentiation.
- App not covered by the table below → ONE `ls` of that app's `src`/`test`
  tree to mirror its directory pattern; doc format from the
  Other-languages table in `comment-block-templates.md`. Never read file
  contents for conventions.

## 3. Hardcoded per-language layout (authoritative)

| | TypeScript | Java | C# |
|---|---|---|---|
| Problem dir | `src/problems/_0001_two_sum/` | `src/main/java/com/jjuidev/jsl/problems/_0001_two_sum/` | `src/Problems/_0001_TwoSum/` |
| Solution file | `solution.ts` | `Solution.java` | `Solution.cs` |
| Test file | `test/problems/_0001_two_sum/solution.test.ts` | `src/test/java/com/jjuidev/jsl/problems/_0001_two_sum/SolutionTest.java` | `test/Problems/_0001_TwoSum/SolutionTests.cs` |
| Unit shell | `export const solve = …` (arrow) | `public class Solution` | `namespace Leetcode.Problems._0001_TwoSum;` + `public class Solution` |
| Solve names | `solve`, `solve2` | `solve`, `solve2` | `Solve`, `Solve2` |
| Doc comments | JSDoc `/** */` | Javadoc `/** */` | XML `///` |
| Test import | `@/problems/<dir>/solution.js` | same package — no import | `using Leetcode.Problems.<dir>;` |
| Indent | tabs | 4 spaces | tabs |
| Run tests | `pnpm --filter ts-nodejs-leetcode test` | `pnpm --filter java-spring-leetcode test` | `pnpm --filter csharp-dotnet-leetcode test` |

Dir slug from the LeetCode slug (`two-sum`, id 1):

- TS / Java: `_` + 4-digit zero-padded id + `_` + snake_case → `_0001_two_sum`
- C#: `_` + 4-digit zero-padded id + `_` + Pascal segments → `_0001_TwoSum`

## 4. Collision policy

Target problem dir already exists → never silently overwrite. Show what is
there and ask: extend (add missing `solve2`/`solve3`/… variants or tests)
or regenerate.
