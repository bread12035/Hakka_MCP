---
name: no-comments-yr
description: "Remove comments that narrate code, turn workaround comments into real fixes, and offer encodings for claimed constraints. Runs in the main agent by default. Spawns the comment-sicko-yr subagent only when multi-agent mode is on."
---

# No comments (yr)

Find the comments that should not exist, fix the code they excuse, and keep only the comments that earn their place.

## Scope

Use the caller's files or diff. Otherwise use the current diff against the base branch (`dev`, or `base:` in the status file), including the working tree.

## Steps

1. **Review the comments.**
   - **Single-agent mode (default).** Read the `comment-sicko-yr` agent definition in the `agents/` folder next to `skills/`. Apply its rules yourself over the scope. Use its rules, not its voice.
   - **Multi-agent mode.** Spawn `Agent` with `subagent_type: "comment-sicko-yr"` and pass the scope. Do not set `model`.
2. **Check the findings.** Reject application-code edits, scope escapes, exception-protected deletions, misstated `MUST KILL` reasons, and flags that treat intentional kept code as guilty. A keep survives only with proof it is about something we cannot change. Before you accept a thin `IMPORTANT` or `do not remove` kill or keep, run **how-yr** or **why-yr** on its symbol. If a kill is ambiguous, do not restore it. If a keep is refuted or still ambiguous, delete it. Audit missed lint and TypeScript suppressions. Correctness or safety suppressions stay actionable `MUST KILL`s.
3. **Fix trivial accepted flags directly.** Delete the dead path, drop the parameter, use the real API. If a fix needs a new shape, run **architect-yr** once for the accepted set and stop at the sketch. Then implement it in step 4.
4. **Fix the root cause** with the smallest in-scope change. Remove every named workaround. If the root cause is out of scope, land the smallest in-scope fix and report the rest as open. **principle-fix-root-causes-yr** and **principle-redesign-from-first-principles-yr** guide intent only. They do not widen the scope. Never bolt on symptom guards.
5. **Constraint comments** say `do not remove`, `do not change wording`, or `talk to X before changing`. Leave keeps about things we cannot change. For the rest, offer the cheapest in-scope type, runtime, test, or CI lint that encodes the constraint, and wait for the user's approval. If approved, encode it and delete the comment. If not, delete the comment, report the constraint as open, and sketch the out-of-scope work.
6. **Report:** deletion count, restored comments, architect sketch if any, fixes, encoding offers, encodings made, unenforced constraints, and other open work.
