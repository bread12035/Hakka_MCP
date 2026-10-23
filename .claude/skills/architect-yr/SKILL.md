---
name: architect-yr
description: "Design before code. Reads the proposal and specs, grounds in the existing code through the graph, sketches types, signatures and module structure in one pass, gets the user's sign-off, then writes architecture.md. Ground-up mode also approves and installs the packages, picks the tooling and writes the code skeleton. Single-agent by default, arena comparison optional. Use for /architect-yr, 'architect this', or non-trivial work where jumping to code would lock in the wrong shape."
---

# Architect (yr)

Sketch types, function signatures, and module boundaries first. Implementation happens later in **poteto-mode-yr**, against this design.

This is the slim version of pstack's `architect`. It runs in one agent. It does not spawn subagents and does not run `arena-yr` unless the user opts in at Phase C.

## Modes

| Mode | When | Output |
|---|---|---|
| `ground-up` | A new project. | `architecture.md`, approved and installed packages, tooling, and the code skeleton. |
| `design-only` | An existing codebase: a feature, a refactor or a bug fix that crosses a function or module boundary. | `architecture.md` only. **No skeleton and no stub code**, because an empty function in live code breaks builds and tests, and a stub of the target shape beside the old code is a parallel path. Types and signatures live in the document. The implementer writes them into the real files. |

The caller says which. If it does not, ask once.

## Inputs and outputs

Inputs:

- The change folder `openspec/changes/<name>/`: `proposal.md` and the delta specs. For a refactor or a bug fix there is no proposal. Use the behavior contract and the notes in `status.md`.
- The current specs in `openspec/specs/`, and the graph (`openspec/graph.md`, plus **graph-yr** `read` for existing code).
- The language and stack from the proposal's Scope. This pack's environment setup assumes Python. If the proposal needs another stack, tell the user before going on.

Output: `openspec/changes/<name>/architecture.md`, shaped by [`references/architecture-template.md`](references/architecture-template.md).

If the sketch shows that a requirement is wrong or missing, stop and go back to **propose-yr**. Do not edit the requirements to fit the design.

## Start

Open a task list with one entry per phase: Ground, Sketch, Agree, then (ground-up only) Packages, Skeleton, then Hand off.

## Phase A: Ground

- **Ground-up**: skip this phase.
- **Existing code**: read the graph with **graph-yr** `read` over every subsystem the change touches. Naming a file is not grounding. Use **how-yr** only for what the graph cannot show, such as runtime behavior. If the design changes ownership or layering, also run **why-yr** on the existing shape, so the old rationale becomes a constraint and not a guess.

## Phase B: Sketch (one pass, you do it)

1. **Usage first.** Write the caller's view: a short quickstart and two or three realistic call sites. The usage is the spec. The types serve it.
2. **Data structures first.** Pick the core types. Trace each dominant access pattern through them. "We will add a map or cache later" means the structure is wrong. Follow **principle-model-the-domain-yr**, **principle-foundational-thinking-yr** and **principle-type-system-discipline-yr**.
3. **Design it twice.** Write two structurally distinct candidate shapes, each a short sketch of types, signatures and module map. Whole-shape alternatives, not point fixes (**principle-exhaust-the-design-space-yr**). Do this yourself, in this one agent.
4. **Screen** each candidate against [`references/design-red-flags.md`](references/design-red-flags.md). Assume the next contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Prefer the design where a change that looks right from one file is right for the whole repo.
5. **Compare on interface depth.** Prefer the design that hides more complexity behind a smaller public surface.
6. **Pick one** and write `architecture.md`. Put the loser in "Alternatives considered" with one line on why it lost. Leave the "Synthesis decision" section empty unless arena runs.

7. **Reference architectures.** If the proposal describes an event-driven service that consumes events, read [`references/micro-service-architecture.md`](references/micro-service-architecture.md) before you sketch. It is the author's usual layout and rules for such a service. Use it as a starting point for the candidates. Adopt, adapt or reject it, and record which and why in `architecture.md`. The same applies to any similar shape that the reference fits.

Principles that apply here: **principle-boundary-discipline-yr**, **principle-separate-before-serializing-shared-state-yr**, **principle-make-operations-idempotent-yr**, **principle-laziness-protocol-yr**.

## Phase C: Agree (checkpoint, on by default)

Stop and show the user a short summary in Traditional Chinese: the usage sketch, the module map, the key types, the chosen shape against the rejected one, and the open questions. Then ask with `AskUserQuestion`:

- **Approve.** Go on.
- **Compare with arena.** Run **arena-yr** on this design task with [`references/runner-prompt.md`](references/runner-prompt.md) as each runner's prompt, and the proposal plus the Phase A artifacts as shared grounding. Replace the sketch with the synthesized design, fill in "Synthesis decision", then ask again. This is the optional multi-agent path.
- **Revise.** Take the user's comments as new evidence. Re-run Phase B. Do not write code yet.

If the user said at the start "no checkpoint", skip the question.

In `design-only` mode, commit `architecture.md` now: `docs: add architecture for <name>`. Then go to Phase F.

## Phase D: Packages (ground-up only)

1. List every third-party package the design needs, in a table: package, what it is for, the module that uses it, why the standard library is not enough, and the alternative you considered. Prefer fewer packages. Add test and tooling packages to a second table.
2. Ask the user to approve with `AskUserQuestion`: approve the list, or edit it. Ask which tooling to use as a multi-select: pytest (recommended), ruff, mypy.
3. After approval, install into the venv with the venv's Python by path: `"<venv-python>" -m pip install <packages>`. If one fails, report the package and the Python version. The cause is often a newest Python with no prebuilt wheel. Let the user pick: another package, or a lower Python for the project.
4. Write the packages with their installed versions into `requirements.txt` as `name==version`, top-level packages only. Tooling goes into `requirements-dev.txt` the same way, after its `-r requirements.txt` line. Read the versions with `"<venv-python>" -m pip freeze` or `-m pip show <name>`.
5. Record in `architecture.md` the "Packages" and "Tooling" sections, and in `status.md` the `test`, `lint` and `typecheck` commands and the Python version.

## Phase E: Skeleton (ground-up only)

Write the skeleton so it is the contract for implementation:

- Real files in the real layout: types, signatures, module boundaries, entry points, minimal package and test config.
- Stub bodies that raise `NotImplementedError`. Pseudocode comments only for tricky logic. Doc comments state intent and invariants, not narration.
- One test function per scenario in the delta specs, named `test_<scenario name in snake_case>`, whose body is `pytest.skip("not implemented")`. This is the implementation checklist, and **archive-yr** checks it later. Skip this when the user did not choose pytest. If you adopted a reference architecture, add what its "For the skeleton" section lists.
- Boundaries are visible: a reader can trace data from input to output by reading types and signatures alone.

Then run the build check: the type checker if the user chose one, otherwise `"<venv-python>" -m compileall -q <source folder>`. The skeleton must build. Run the test command: all tests must pass or skip.

Commit it as its own commit, "scaffold first" (**principle-foundational-thinking-yr**): `chore: scaffold <name>`. Commit `architecture.md`, `requirements.txt` and the status file in their own commits before it.

## Phase F: Hand off

Report in a few sentences: where `architecture.md` is, the chosen shape, the packages, open questions. The next step is the work branch and **poteto-mode-yr**.

## During implementation (rules the implementer follows)

The design is the contract. A deviation is a signal to surface, not friction to absorb.

- If a function needs a parameter the sketch did not anticipate, ask whether the sketch was wrong, a requirement was missed, or the implementation is overreaching.
- Before closing a unit, compare accepted deviations with the saved contracts. Once the user or the review accepts a change, update `architecture.md` ("Implementation reconciliation") and the affected signatures. Record who accepted it. Keep unaccepted changes visible.
- A local deviation that leaves the shared contract intact needs one line saying why the design still holds.
- One deviation needs no approval: where a playbook of **poteto-mode-yr** conflicts with this document, the playbook wins. The implementer records it in "Implementation reconciliation" and updates this document to match.

## When the architecture is wrong (scrap)

If implementation keeps producing friction the sketch cannot absorb, throw the sketch out. Do not bolt fixes onto a wrong design (**principle-redesign-from-first-principles-yr**, **principle-fix-root-causes-yr**).

The signal is a pattern, not one instance:

- The same workaround shape appears repeatedly in unrelated code.
- Several unrelated edge cases each need a special-case branch.
- Types need escape hatches (`Any`, casts, optional fields always set in practice) to compile.
- The "we need a lock" reflex shows up where the sketch said state was not shared.
- Callers must know the abstraction's internal rules to use it.
- Two or more independent deviations have the same shape.

A few edge cases do not condemn an architecture. When you scrap: re-read the graph over what is built, redesign as if the new constraints were day-one assumptions, subtract before adding (**principle-subtract-before-you-add-yr**), and return to Phase B. Tell the user before you do.
