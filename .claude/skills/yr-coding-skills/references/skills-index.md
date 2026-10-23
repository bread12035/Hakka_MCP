# Sub-skills (yr pack)

Each one can also be run alone with `/<name>`. The entry is `/yr-coding-skills`.

## Flow skills

| Skill | What it does | Used in flow |
|---|---|---|
| `yr-coding-skills` | The entry. Menu, resume, the status file, and the order of the steps | all |
| `repo-setup-yr` | Git and Python setup. Full: ask which repo, clone or pull, check out `dev`, create `.venv`, install requirements. Light: verify them. Creates the work branch | 1, 2, 3, 4 |
| `propose-yr` | OpenSpec-style proposal: `proposal.md` plus a delta spec of requirements and GIVEN / WHEN / THEN scenarios. Interview with options and a recommendation. Modes: greenfield, feature | 1, 2 |
| `graph-yr` | codegraph: `sync` the index, `read` an area before changing it, `snapshot` the readable `openspec/graph.md`. Skips cleanly without codegraph | 1, 2, 3, 4 |
| `architect-yr` | Sketches types and modules, asks for sign-off, writes `architecture.md`. Ground-up also approves and installs packages, picks tooling, writes the skeleton. Arena comparison is optional. Has a reference architecture for event-driven micro-services (layout, ack and nack table, thread per event, layer test) | 1, and 2, 3, 4 when a change crosses a boundary |
| `poteto-mode-yr` | Implementation style and playbooks: Feature, Refactoring, Bug fix, Landing. Asks about TDD and sub-agents first | 1, 2, 3, 4 |
| `review-pass-yr` | One review round: `/code-review`, then `/security-review`. Lists the problems, you choose what to fix. Writes `openspec/reviews/<name>.md` | all |
| `archive-yr` | Checks that scenarios have tests, appends the outcome to the proposal, merges the delta specs into `openspec/specs/` with a script, and moves the change to the archive | all |

## Helper skills

| Skill | What it does |
|---|---|
| `how-yr` | Explains how a part of the code works. For what the graph cannot show |
| `why-yr` | Finds why code is the way it is, from git history, PRs, tickets and docs |
| `grilling-yr` | The interview method used by propose-yr: rounds of questions, each with options and a recommended solution |
| `tdd-yr` | Test-first in three modes: bug fix, feature, refactor |
| `arena-yr` | Optional. Runs several candidates on one task, picks a base, grafts the best parts |
| `deslop-yr` | Removes AI-style slop from a diff |
| `no-comments-yr` | Removes narrating comments and fixes the code they excuse |
| `technical-writing-yr` | Writing standard for docs, commit messages and PR text |
| `unslop-yr` | Cuts AI tells from any writing |

## Playbooks (inside `poteto-mode-yr`)

| Playbook | Use it for |
|---|---|
| Feature | New or changed behavior against the scenarios of a change |
| Refactoring | Behavior-preserving restructure, with a confirmed behavior contract |
| Bug fix | Reproduce, find the root cause, stop for your approval, then fix |
| Landing | Merge the work branch into `dev` and push. Offers the pull request text for the default branch |

## Principles

24 `principle-*-yr` skills. They are read on demand when a decision matches. The list with "when to apply" is in `poteto-mode-yr`.

## Agents

| Agent | Used by |
|---|---|
| `poteto-agent-yr` | poteto-mode-yr, multi-agent mode only |
| `comment-sicko-yr` | no-comments-yr, multi-agent mode only |

## Files the workflow writes

| Path | What |
|---|---|
| `openspec/specs/<domain>/spec.md` | What the system does now |
| `openspec/changes/<name>/` | A change in progress: `proposal.md`, `specs/`, `architecture.md`, `status.md` |
| `openspec/changes/archive/<date>-<name>/` | Finished changes |
| `openspec/reviews/<name>.md` | Review reports |
| `openspec/graph.md` | Readable code graph snapshot |

## Built-ins used (not part of this pack)

`/code-review`, `/security-review`, and the `codegraph` MCP server or CLI when installed.
