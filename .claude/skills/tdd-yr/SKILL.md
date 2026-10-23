---
name: tdd-yr
description: "Test-first work in three modes: bug fix (failing regression test first), feature (red to green in small slices per requirement), refactor (characterization pins that stay green). Use when the user opted into TDD in poteto-mode-yr, or explicitly asks for TDD, a failing test or a regression test, or when a bug has an obvious cheap local test target. Skip when the test path is unclear, expensive, integration-heavy, or not requested."
---

# TDD (yr)

Three modes. The caller names the mode: **bug-fix**, **feature**, or **refactor**. The numbered workflow below is bug-fix mode. Feature and refactor modes are at the end.

When fixing a bug with a clear, cheap test path, make the broken behavior executable before changing production code. The goal is a focused regression test that fails before the fix and passes after it.

Do not force a test when it would be impractical. If the available test would require broad harness setup, brittle mocks, slow end-to-end infrastructure, production-only state, vague reproduction steps, or large unrelated fixture churn, skip adding a new test and use the closest useful verification instead.

## Workflow (bug-fix mode)

1. **Understand the bug.** Identify the intended behavior, current behavior, affected path, and smallest observable reproduction.
2. **Choose the narrowest executable check.** Prefer the closest unit, component, integration, or regression test already used for that codepath. If no practical test path is obvious, do not create one from scratch just to satisfy the workflow.
3. **Write the failing test first.** Add the smallest focused test that would have caught the bug. The test should encode intended behavior, not mirror the current implementation.
4. **Run the new test before fixing.** Confirm it fails for the intended reason. Quote the failure content, not the assertion line: an exception, an empty result against a literal, and the predicted mismatch all print red, and only the last one proves the test measures the bug. If it passes or fails for an unrelated reason, correct the test or reproduction before editing the implementation.
5. **Fix the bug.** Make the smallest production change that satisfies the intended behavior while preserving nearby contracts.
6. **Rerun the regression test.** Confirm the test now passes.

## If a Failing Test Is Impractical

Use the closest executable regression check instead: a targeted script, manual reproduction command, browser automation, snapshot comparison, log assertion, or focused integration check.

Prefer no new test over a bad test. A bad test is one that mostly tests mocks, encodes current implementation details, depends on timing or unrelated global state, needs expensive infrastructure for a small fix, or would be deleted immediately after proving the fix.

## Guardrails

- Do not change tests merely to match a wrong implementation.
- Do not weaken existing assertions unless the expected behavior has genuinely changed and the reason is clear.
- Keep the regression test focused on the bug. Avoid broad fixture churn or unrelated coverage expansion.
- If the bug is flaky, make the test deterministic where possible and document the signal being locked down.
- If the bug exposes a broader class of failures, first land the focused regression path, then consider additional sibling coverage.

## Final Response

Report the evidence, not just the outcome:

- Name the failing-before test or executable check and quote the failure it produced, trimmed to the diff.
- Name the passing-after test run and any nearby validation performed.
- If failing-before evidence could not be demonstrated, state why and describe the closest regression check used instead.

## Feature mode

Red to green in vertical slices, one scenario at a time.

1. **Agree the seams once.** A seam is the public boundary you test at: the interface where you observe behavior without reaching inside. Before the first test, state the seams under test in one line each (what it catches, what it misses) and confirm them with the user if they are not obvious. Do not write tests at an unconfirmed seam. You cannot test everything, so effort goes to the critical paths and the complex logic.
2. **One slice at a time.** Take one scenario from the change's delta spec. Name the test `test_<scenario name in snake_case>`, so **archive-yr** can match it. If the skeleton already has that test as a skip, replace the skip. Write one failing test whose expected value comes from the scenario's THEN lines. Run it and confirm it fails for the intended reason. Write the smallest code that passes it. Run it green. Repeat for the next slice.
3. **Do not write all the tests first.** Bulk tests verify imagined behavior and commit you to a test structure before you understand the implementation. Each test is a tracer bullet that responds to what the last cycle taught you.
4. **Refactoring is not part of the loop.** It belongs to clean-up after green (**deslop-yr**, review), not to the red-green cycle.

Anti-patterns to avoid:

- **Implementation-coupled tests.** Mocking internal collaborators, testing private methods, or checking through a side channel. The tell: the test breaks when you refactor but behavior has not changed (**principle-test-behavior-not-implementation-yr**).
- **Tautological tests.** The assertion recomputes the expected value the way the code does, so it passes by construction. Expected values come from an independent source: a literal, a worked example, the requirement.

## Refactor mode

Characterization pins. The goal is a test that stays green while the structure moves.

1. Take the behavior contract (B1, B2, ...) from the status file (`## Behavior contract`). For each behavior, prefer an existing test. Where there is none, write a test at the public seam that records what the code does now.
2. **Run every pin on the current code and see it pass before you touch any structure.** A pin that fails on the current code is wrong, or it found a bug. If it found a bug, record it as separate work and pin the current behavior or exclude that case from the contract, with the user's agreement.
3. Assert observable behavior only. Do not pin internals, call counts or private helpers, because those are exactly what the refactor is going to change.
4. After every refactoring step, run the pins. A red pin means the step changed behavior. Fix or revert the step. Never edit a pin to match new behavior unless the user agrees the contract changed.
5. Do not add tests for new behavior in a refactor.
