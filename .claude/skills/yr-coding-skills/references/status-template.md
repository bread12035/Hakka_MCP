# Status file template

File: `openspec/changes/<name>/status.md`. English. Plain `key: value` lines, so it is easy to read and to edit.

```markdown
# Status: <name>

flow: ground-up | feature | debug | refactor
next: <step>
repo: <absolute path of the repo root>
branch: <current work branch>
base: dev
default-branch: <master or main>
python: <relative path of the venv python, for example .venv/Scripts/python.exe>
python-version: <x.y.z>
test: <command, or "to be decided">
lint: <command or none>
typecheck: <command or none>
tdd: yes | no | ask
subagents: yes | no | ask
proposal: openspec/changes/<name>/proposal.md | none
architecture: openspec/changes/<name>/architecture.md | none
codegraph: mcp | cli | none

## Log
- <YYYY-MM-DD> <step done>: <one line>
```

Values for `next`:

| Flow | Steps in order |
|---|---|
| ground-up | setup, propose, architect, land-design, branch, implement, review, graph, archive, land, done |
| feature | setup, branch, graph-read, propose, implement, review, graph, archive, land, done |
| debug | setup, branch, graph-read, implement, review, graph, archive, land, done |
| refactor | setup, branch, graph-read, implement, review, graph, archive, land, done |

Notes:

- `tdd` and `subagents` start as `ask`. **poteto-mode-yr** asks once and writes `yes` or `no`.
- A bug fix records the confirmed root cause and the approved fix as a log line.
- A refactor records the confirmed behavior contract (B1, B2, ...) under a `## Behavior contract` heading.
