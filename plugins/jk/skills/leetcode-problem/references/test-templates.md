# Test File Templates

Tests are generated for EVERY language app — all apps get the identical
scaffold (problem header + stubs + tests). The ONLY case without a test
file: the user's notes explicitly exclude tests ("không cần test",
"no tests", "chỉ test ts", "bỏ test java"…).

## Shared rules

- Cover **every** solve variant (`solve`, `solve2`, …) with the SAME case
  set — registry iteration in TypeScript; mirrored test methods suffixed
  with the variant name in Java/C#.
- Cases: all official examples + edge cases derived from constraints
  (min size, duplicates, negatives…) + the guaranteed no-solution branch
  (expect the documented throw).
- Recompute every expected output by hand — never copy a value you cannot
  justify.
- These templates are authoritative — do not read existing repo test files
  for conventions.
- Tests are EXPECTED to fail right after generation — stubs throw by
  design. Never weaken a test to pass.

## TypeScript (Vitest) — registry over variants

```ts
import { describe, expect, it } from 'vitest'

import { solve, solve2 } from '@/problems/_0001_two_sum/solution.js'

const solves = { solve, solve2 } as const

describe('0001 two-sum', () => {
	for (const [name, solveFn] of Object.entries(solves)) {
		describe(name, () => {
			it('returns the indices that sum to the target', () => {
				expect(solveFn([2, 7, 11, 15], 9)).toEqual([0, 1])
				expect(solveFn([3, 2, 4], 6)).toEqual([1, 2])
				expect(solveFn([3, 3], 6)).toEqual([0, 1])
			})

			it('throws when no pair exists', () => {
				expect(() => solveFn([1, 2, 3], 100)).toThrow()
			})
		})
	}
})
```

## Java (JUnit 5) — mirror per variant

```java
package com.jjuidev.jsl.problems._0001_two_sum;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;

class SolutionTest {

  // Mirror the same case set for solve2/solve3 — prefix with the variant name.
  @Test
  void solveReturnsIndicesThatSumToTarget() {
    Solution solution = new Solution();

    assertArrayEquals(new int[] {0, 1}, solution.solve(new int[] {2, 7, 11, 15}, 9));
    assertArrayEquals(new int[] {1, 2}, solution.solve(new int[] {3, 2, 4}, 6));
    assertArrayEquals(new int[] {0, 1}, solution.solve(new int[] {3, 3}, 6));
  }

  @Test
  void solveThrowsWhenNoPairExists() {
    Solution solution = new Solution();

    assertThrows(
        IllegalArgumentException.class, () -> solution.solve(new int[] {1, 2, 3}, 100));
  }

  @Test
  void solve2ReturnsIndicesThatSumToTarget() {
    Solution solution = new Solution();

    assertArrayEquals(new int[] {0, 1}, solution.solve2(new int[] {2, 7, 11, 15}, 9));
  }
}
```

## C# (xUnit) — mirror per variant

```csharp
using Leetcode.Problems._0001_TwoSum;
using Xunit;

namespace Leetcode.Tests.Problems._0001_TwoSum;

public class SolutionTests
{
	// Mirror the same case set for Solve2/Solve3 — prefix with the variant name.
	[Fact]
	public void Solve_ReturnsIndicesThatSumToTarget()
	{
		var solution = new Solution();

		Assert.Equal(new[] { 0, 1 }, solution.Solve(new[] { 2, 7, 11, 15 }, 9));
		Assert.Equal(new[] { 1, 2 }, solution.Solve(new[] { 3, 2, 4 }, 6));
	}

	[Fact]
	public void Solve_ThrowsWhenNoPairExists()
	{
		Assert.Throws<ArgumentException>(() => new Solution().Solve(new[] { 1, 2, 3 }, 100));
	}

	[Fact]
	public void Solve2_ReturnsIndicesThatSumToTarget()
	{
		Assert.Equal(new[] { 0, 1 }, new Solution().Solve2(new[] { 2, 7, 11, 15 }, 9));
	}
}
```

Per-app test run commands: `references/workspace-layout.md` §3.
