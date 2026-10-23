### Bug fix

**You own this task. Plan, review, verify.** In single-agent mode (default) you investigate and fix it yourself. In multi-agent mode you delegate the investigation and the fix, and stay in the lead.

Be scientific. Every shipped line traces to runtime evidence. A belt-and-suspenders change that "might help" is a hypothesis, not a fix, and it does not ship. When evidence refutes a hypothesis, revert what it motivated. The smallest change the evidence justifies ships, nothing more.

Start by getting the report straight: expected behavior, actual behavior, and the steps or input that trigger it. Ask the user only for what you cannot find yourself.

1. Reproduce it yourself on the matching surface (see Non-negotiables in poteto-mode-yr), even when a debug protocol says to ask the user to reproduce. Ask the user only with a stated, specific reason that you cannot reach the target, and only after driving it as far as it goes. If it will not reproduce, synthesize the trigger, tighten conditions, or instrument until it fires.
2. Binary-search the cause. Form candidate hypotheses, then rule them out until one survives. Seed them with the graph read the flow already did (callers, callees, the tests that cover the area), **how-yr** for runtime behavior the graph cannot show, and **why-yr** for regression history. Each pass, take the split that cuts the most remaining problem space, get runtime evidence, and eliminate. When program state is unclear, add instrumentation or logging and read it as the code runs. Do not guess. Confirm the surviving mechanism with runtime evidence before you plan the fix. If two fixes that share one premise fail the same gate, apply **principle-attack-the-premise-yr**.
3. **Approval stop.** This is the one place the workflow deliberately blocks on the human, as an exception to **principle-never-block-on-the-human-yr**, because the user wants to approve every fix. Do not change any code yet. Show the user, in Traditional Chinese: the root cause with its runtime evidence, the proposed fix (files, the change in a few lines, why it fixes the cause and not the symptom), the risk and the blast radius, and how you will verify. Ask with `AskUserQuestion`: Approve / Revise the fix / Stop. Record the approved root cause and fix as a line in the status file. Only after "Approve" go on.
4. Plan the fix. If it crosses a function or module boundary, run **architect-yr** in `design-only` mode first, and show the user the result as part of the approval. Then fix it:
   - **Single-agent (default).** Make the fix yourself, at the root cause (**principle-fix-root-causes-yr**).
   - **Multi-agent on.** Delegate the fix to `poteto-agent-yr` with a specific scope.
   - If the fix needs more than you approved, stop and ask again.
5. Verify on the same surface. The original repro now passes. "Inconclusive" or wrong-surface is not a pass. Flag it. Unit tests show branch behavior, not bug absence.
6. Stage the commits so the failing repro lands before the fix in git history. Use **tdd-yr** in bug-fix mode when TDD is on or the bug has a cheap local test path. Skip it when the test would be expensive, integration-heavy or unclear. This is the canonical case for **principle-sequence-verifiable-units-yr**: the failing test first, the fix on top.
7. Clean up the diff against `dev`: run **deslop-yr**, then **no-comments-yr**, and commit the result on its own. Then stop. The flow continues with review. Do not push and do not merge.

**Reply:** what was broken, the root cause, the fix, how you verified. Quote the decisive failing and passing output, trimmed to the assertion and the counts.
