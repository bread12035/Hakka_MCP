### Feature

**You own the design. Plan, review, verify.** In single-agent mode (default) you write the code yourself. In multi-agent mode you delegate it and stay in the lead.

Inputs: the delta specs of the change (`openspec/changes/<name>/specs/<domain>/spec.md`) with their scenarios. For a new project, also the code skeleton and `architecture.md` from **architect-yr**. That skeleton is the contract.

1. Ground. Existing code: the graph read the flow already did is the grounding (**graph-yr** `read`). Run **how-yr** only for what the graph cannot show. New project: the proposal, the specs and the skeleton are the grounding.
2. Design. If **architect-yr** already produced `architecture.md`, it is the contract. If a rule of this playbook conflicts with it, the playbook wins (see Precedence in poteto-mode-yr), and you update the document. If the change crosses a function or module boundary and no design exists, run **architect-yr** in `design-only` mode first. Name the data shape and its organizing structure per **principle-model-the-domain-yr** before you write logic: a state machine over scattered booleans, a table or registry over branching, a typed model over repeated shape assumptions.
3. Ask the Step 0 options (TDD, multi-agent) if the user has not answered yet. Multi-agent only: write the throughput checkpoint as four todo items. A dimension that does not apply keeps its item with `n/a: <reason>`.
   - **Blocking first steps.** Gates that run before fan-out.
   - **Independent workstreams.** Disjoint files, services or layers parallelize. Shared writes serialize.
   - **Shared mutable state.** Default to splitting the target (**principle-separate-before-serializing-shared-state-yr**). Serialize only for real invariants.
   - **Smallest safe decomposition.** If one worker is best, name why.
4. Implement one verifiable unit at a time (**principle-sequence-verifiable-units-yr**), in the build order `architecture.md` gives if it gives one. Make one todo item per scenario.
   - **Single-agent (default).** Fill the skeleton or edit the code yourself. Surgical edits. Re-ground against the source for upstream-derived files. Bias to the smallest change (**principle-laziness-protocol-yr**). Commit liberally.
   - **TDD on.** For each unit, follow **tdd-yr** in feature mode: pick the seam, write the failing test, write the smallest code that passes, repeat. The test for a scenario is `test_<scenario name in snake_case>`. If the skeleton already has that test as a skip, replace the skip.
   - **Multi-agent on.** Delegate code-writing per poteto-mode-yr's multi-agent rules. Use **arena-yr** instead when the implementation admits several valid shapes.
   - **TDD off.** Still write a test for every scenario, named `test_<scenario name in snake_case>`, so **archive-yr** can match them. Write it after the code for that unit.
   - A deviation from the skeleton is a signal, not friction. Follow the "During implementation" rules in **architect-yr**.
5. Verify each scenario on the real surface. Mark every scenario pass or fail with the evidence. Also run the checks that `architecture.md` lists for the implementation (for example concurrency or shutdown checks), and report them the same way. "Inconclusive" or wrong-surface is not a pass. Flag it.
6. Turn the work into small, ordered commits (**principle-sequence-verifiable-units-yr**). Interactive rebase is not available here. If the history is messy, use `git reset --soft <base>` and recommit in slices.
7. Clean up the diff against `dev`: run **deslop-yr**, then **no-comments-yr**, and commit the result on its own. Then stop. The flow continues with review. Do not push and do not merge.

**Reply:** what you built, what you chose and why, the scenario coverage (each scenario with its evidence), open decisions. Tables for design alternatives.
