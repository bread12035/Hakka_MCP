---
name: graph-yr
description: "Code graph for a repo, with codegraph. sync: bring the index up to date. read: understand an area through the graph before changing it. snapshot: regenerate the readable openspec/graph.md and commit it. Skips cleanly when codegraph is not installed. Use for /graph-yr, or when a flow needs to read or refresh the graph."
---

# Graph (yr)

Two graphs exist. Keep them apart.

- **Live index**: `.codegraph/` in the repo, made by codegraph. Fast to query, not readable as a document, and ignored by git (a wildcard `.gitignore` inside it).
- **Snapshot**: `openspec/graph.md`, a readable file generated from the code. It is committed, so it travels with the proposal and the specs.

Modes: `sync`, `read`, `snapshot`. The caller says which one.

## Step 0. What is available

Check three things, once per session, and remember the answers:

1. **MCP tool.** Is a codegraph tool present, usually `codegraph_explore`? If tools are deferred, look for it with ToolSearch.
2. **CLI.** Run `codegraph --version`. Run `codegraph --help` once and trust it over the command names in this skill if they differ.
3. **Source files.** Does the repo have source code yet? A new project has none. Skip `sync` and `read` for it.

Write the result to `codegraph:` in the status file (`mcp`, `cli` or `none`; `mcp` if both exist) so later steps do not check again.

If neither the MCP tool nor the CLI exists, say so in one line, skip the codegraph steps and continue. `read` falls back to `openspec/graph.md` and **how-yr**. `snapshot` still works, because its script does not need codegraph.

Never run `codegraph install`. It edits the user's Claude settings and `CLAUDE.md`. Setup is the user's decision.

## sync

Run it at the start and at the end of any flow that touches code. The index does not update itself unless the codegraph MCP server watches this exact folder, and a freshly cloned repo may not be indexed at all.

1. `codegraph status`, run from the repo root with `(cd "<repo>" && codegraph status)`.
2. Not initialized: `codegraph init`, then `codegraph index` if `status` shows nothing indexed.
3. Initialized: `codegraph sync`.
4. If a command fails, show the error tail and continue without the graph. Do not retry in a loop.

## read

Understand an area before you change it. This replaces a broad exploration with **how-yr**.

1. Read `openspec/graph.md` if it exists. It is the cheap overview.
2. Ask the live graph about the area the task touches, in this order of preference: the MCP tool (`codegraph_explore` with a plain question about the symbol, file or behavior), then the CLI: `codegraph query <term>`, `codegraph node <symbol>`, `codegraph callers <symbol>`, `codegraph callees <symbol>`, `codegraph impact <symbol>`, `codegraph affected <files>` (the tests that cover a change), `codegraph context <task>`.
3. Read the files the graph points to. The graph says where to look. The code says what it does.
4. Give the user a short map, at most 30 lines: the modules involved, the entry points, who calls what, the tests that cover it, and anything surprising. Name the files and symbols.
5. Use **how-yr** only for what the graph cannot show: runtime behavior, data flow through many steps, or an area the index does not cover. Use **why-yr** only when the reason behind the code matters.

## snapshot

Regenerate `openspec/graph.md`. Run it near the end of every flow that changed code, after the review and before the archive.

1. Run the script. It reads the tracked Python files with `ast` and writes the file. It is deterministic: no dates, no hashes, sorted output.
   `"<venv-python>" "<this skill's folder>/scripts/graph_snapshot.py" --repo "<repo>" --out openspec/graph.md`
   Exit code 0 means written, 3 means nothing changed, 1 means an error.
2. If codegraph is available, refresh the notes block. Ask it for the structure that the script cannot show, such as the central symbols, the main call chains, and the cross-module links. Write at most 20 short lines in English between `<!-- codegraph:begin -->` and `<!-- codegraph:end -->`. Replace what was there. The script keeps this block on later runs.
3. Check the diff with `git -C "<repo>" diff --stat -- openspec/graph.md`. If the file is unchanged, do not commit.
4. Otherwise commit it alone: `docs: refresh code graph`.
5. Keep it small. The script caps the file at 300 lines. If the repo is big, the module table is cut and the codegraph notes carry the rest.

The snapshot is generated. If two branches change it and git reports a conflict, take either side and regenerate. Never merge it by hand.

For a repo that is not Python, the script lists files and finds no modules. Say that, and fill only the codegraph notes block.
