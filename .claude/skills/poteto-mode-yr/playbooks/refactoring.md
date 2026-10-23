### Refactoring

**You own the contract. The structure changes. The behavior does not.** Distinct from Feature, which adds behavior, and Bug fix, which corrects it.

If the cleanup reveals a missing feature or a real bug, split it out and ship the structural change first against the pinned contract. A redesign is allowed, but name it and route it to Feature. Large or cross-cutting structural work should be split into several refactors that each go through this playbook.

Inputs: the graph read the flow already did, the specs in `openspec/specs/` that cover the area, and the user's description of the problem. A refactor has no proposal. If a scenario in the specs would have to change, it is a feature: stop and tell the user.

0. **Behavior contract.** List what must not change, as B1, B2, ...: the public functions and their callers (`codegraph callers`, `impact` through **graph-yr**), the scenarios of the specs that touch the area, and the tests that cover it (`codegraph affected`). Write the list under `## Behavior contract` in the status file. Show it to the user in Traditional Chinese and ask with `AskUserQuestion`: Approve / Revise. Do not move any structure before it is approved.
1. Pin the behavior contract first. For each behavior in the contract, find what already checks it, or write a characterization test, snapshot, or equivalence script that captures current behavior. The pin must pass on the current code before any structure moves. Type check and lint are not a pin. If the area has no coverage, write the pin before touching structure.
   - **TDD on.** Write the pins with **tdd-yr** in refactor mode: tests at the public seam, on observable behavior, green on the current code.
   - **TDD off.** Use the lightest check that would catch a behavior change: existing tests, a snapshot, or a small script that diffs outputs.
2. Name the structure the code is missing per **principle-model-the-domain-yr**. Boring code stays when the shape is already clear and local. The reshape must delete branches or invalid states, not add indirection.
3. Name the target shape. State what the module layout, types and call graph should be if built today (**principle-foundational-thinking-yr**, **principle-redesign-from-first-principles-yr**). If the target crosses a function or module boundary, run **architect-yr** in `design-only` mode first. Its checkpoint offers an optional arena comparison, which suits a large reshape.
4. Subtract before you add. Delete dead code, collapse one-caller wrappers, drop redundant validators, and remove orphan references before you introduce the new shape (**principle-subtract-before-you-add-yr**). The smallest change that reaches the target shape ships (**principle-laziness-protocol-yr**). A speculative cleanup that "might help" gets reverted.
5. Move in small behavior-preserving steps, each keeping the pin green. For API reshapes, migrate every caller and delete the old API in the same wave (**principle-migrate-callers-then-delete-legacy-apis-yr**). No compatibility shims, no parallel old-and-new paths. Spot-check every rename against the actual files, because renames silently miss usages in strings, prose and back-references.
   - **Single-agent (default).** Make the edits yourself.
   - **Multi-agent on.** Delegate the mechanical edits to `poteto-agent-yr` with a specific scope: file paths, the names being moved, the behavior to hold.
6. Prove behavior is unchanged on the real artifact, not "it compiles" (**principle-prove-it-works-yr**). For larger reshapes, run an equivalence check: a script that diffs old and new outputs, a recorded baseline replayed against the new code, or a smoke run on the matching surface.
7. Confirm the change is worth keeping. The success measure is reduced reader load (**principle-minimize-reader-load-yr**). If the diff does not lower reader load somewhere, revert it.
8. Make small ordered commits (no interactive rebase here: use `git reset --soft <base>` and recommit in slices): a subtraction commit, then the reshape, then any follow-on cleanup. Shape them with **principle-sequence-verifiable-units-yr**, so each behavior-preserving slice stays green before the next.
9. Clean up the diff against `dev`: run **deslop-yr**, then **no-comments-yr**, and commit the result on its own. Then stop. The flow continues with review. Do not push and do not merge.

**Reply:** the structure that changed, the pin you held it against, the equivalence proof, the reader-load change, what shipped and what got reverted. No new behavior.
