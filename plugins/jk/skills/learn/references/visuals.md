# Visuals Reference

Which visual each mode uses, and how to write it. A visual earns its place only when it answers the mode's question faster than prose. No decorative diagrams.

## Syntax Follows the Output

| Output | Diagram syntax | Why |
|--------|----------------|-----|
| HTML (`html: true`) | Mermaid in a ` ```mermaid ` block | The renderer draws it as SVG |
| MD terminal (`html: false`) | ASCII / box-drawing in a ` ```text ` block, max 80 columns | Terminals cannot render Mermaid; raw Mermaid source is unreadable there |

Tables and code blocks work in both outputs.

## Per-Mode Mapping

| Mode | Primary visual | Diagram | Mermaid type |
|------|----------------|---------|--------------|
| `overview` | Comparison table | Optional: context map showing where the topic sits between what feeds it and what it feeds | `flowchart LR` |
| `usage` | Code blocks | Optional: only when a use case crosses parties (client ↔ server, app ↔ queue) | `sequenceDiagram` |
| `workflow` | Step flow | **Required**: the task's steps as a flow, with check or decision nodes. **Required** when data moves between 2+ parties: the data flow of the finished system | `flowchart TD` + `sequenceDiagram` |
| `internals` | Architecture + execution flow | **Required** with 3+ components: architecture with boundaries. **Required**: the main execution path. Add a state diagram when the topic has a lifecycle, and a data model when data shape is central | `flowchart` with `subgraph`, `sequenceDiagram`, `stateDiagram-v2`, `erDiagram` / `classDiagram` |
| `cheatsheet` | Dense tables | None. Exception: a decision tree when 3+ APIs overlap ("which one do I use?") | `flowchart TD` |
| `docs` | Ordered link lists | Optional: the reading path | `flowchart LR` |
| `eli` | Analogy mapping table | **Required**: the mechanism as one small flow with plain-language labels, max 6 nodes | `flowchart LR` |

With `--eli<N>` on another mode, keep that mode's diagrams but use plain-language labels.

## Diagram Rules

1. **Stable types only**: `flowchart`, `sequenceDiagram`, `stateDiagram-v2`, `classDiagram`, `erDiagram`, `timeline`, `mindmap`. Never use `-beta` types (`architecture-beta`, `block-beta`, `xychart-beta`, ...); their syntax still changes between releases.
2. **Match the prose**: node and participant names are the same names the text uses, and the diagram's steps are the text's steps, in the same order.
3. **Size**: at most 15 nodes or 8 participants. Split a bigger picture into two diagrams by question.
4. **Labels**: wrap labels with spaces or symbols in quotes (`A["POST /api/login"]`). Avoid characters Mermaid treats as syntax (`;`, unbalanced brackets) in unquoted labels.
5. **Facts only**: every arrow is a real call, message, or dependency from the sources. Never draw a connection the sources do not support.
6. **Syntax reference**: use the `ak:mermaidjs-v11` skill if registered, else the official docs at https://mermaid.js.org/intro/.
