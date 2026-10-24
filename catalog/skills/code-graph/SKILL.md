---
technique: code-graph
status: draft
source: Hakka vibe workflow (graph-yr, codegraph). No measured run yet.
---
# Code graph first

Find code through the structure, not by reading files end to end.

## Rules

1. Before you open files, ask the code graph: who defines this symbol, who calls it, what it imports, what a change would affect. Use the codegraph MCP tools or CLI if they exist in this project.
2. Open only the files and line ranges the graph points to. Read a function, not its whole module.
3. No graph available? Use the cheapest structural search the project has: a symbol search, `git grep -n` for the exact name, then the definition. Do not list and read directories to orient yourself.
4. Keep a short map of what you found (symbol, file, line, role) and reuse it. Do not re-read a file you already read unless it changed.
5. Before a change, list its callers from the graph. That list is the scope of the change and of the tests.
6. After a change that moves or renames code, refresh the graph index so the next lookup is right.

## When to break the rules

A file shorter than about 150 lines, or a file the task is entirely about, can be read whole.
