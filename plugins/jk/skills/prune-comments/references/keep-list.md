# Keep list (tier 0)

Comments that tools read. Deleting or rewording one changes lint, type, build, coverage, or legal behavior, so tier 0 keeps them untouched and never tightens them.

Override: when `--junk` names one of these patterns explicitly (for example `--junk "unused eslint-disable"`), delete only the matching comments and mark each row ⚠ in the summary. A vague `--junk` never overrides tier 0.

## Lint and type directives

`eslint-disable`, `eslint-disable-next-line`, `eslint-enable`, `/* eslint ... */` config, `/* global ... */`, `@ts-expect-error`, `@ts-ignore`, `@ts-nocheck`, `@ts-check`, `biome-ignore`, `prettier-ignore`, `stylelint-disable`, `# noqa`, `# type: ignore`, `# pyright:`, `# mypy:`, `# pylint:`, `# fmt: off` / `# fmt: on`, `# isort:`, `// nolint`, `//nolint`, `// NOSONAR`, `rubocop:disable`, `// swiftlint:`, `// @phpstan-`, `<!-- markdownlint-disable -->`.

## Build, compiler, and runtime

Shebang `#!`, `# -*- coding: ... -*-`, `//go:build`, `// +build`, `//go:generate`, `//go:embed`, `//go:linkname`, `/* webpackChunkName ... */` and other `webpack*` magic comments, `/* @vite-ignore */`, `/* @__PURE__ */`, `/** @jsx ... */`, `/** @jsxImportSource ... */`, `/// <reference ... />`, `// @flow`, `#region` / `#endregion`, `// language=...` (IDE injection).

## Coverage

`istanbul ignore`, `c8 ignore`, `v8 ignore`, `# pragma: no cover`, `// coverage:ignore`.

## Generated marker

`Code generated ... DO NOT EDIT.`, `@generated`. The checkpoint script already drops files whose first five lines carry one of these; any later occurrence is still kept.

## Doc contracts

- JSDoc with `{Type}` annotations in `.js`/`.mjs`/`.cjs` files: the type checker reads them.
- `@deprecated`, `@internal`, `@public`, `@alpha`, `@beta`: API tooling and editors read them.
- Go doc comment directly above an exported identifier: `golint`/`revive` require it.
- Rust `///` and `//!` on public items: they are the published docs.
- OpenAPI/Swagger annotations (`@swagger`, `@openapi`, `@route`).

Python docstrings are string literals, not comments, and stay out of scope.

## Legal

`SPDX-License-Identifier`, copyright lines, license headers.
