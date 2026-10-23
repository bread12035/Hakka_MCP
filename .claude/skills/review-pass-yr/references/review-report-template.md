# Review report template

Copy this structure into `openspec/reviews/<name>.md`. Write it in English. Keep code identifiers, file paths and command names as they are.

`<name>` is the change name from the status file (the folder name under `openspec/changes/`). If there is none, use the branch name.

If the file already exists, this is a later round. Do not overwrite it. Add a new section `## Round N` below the last one, with the same structure from "Scope" down.

```markdown
# Review report: <name>

Proposal: <openspec/changes/... path, or "none">
Architecture: <path, or "none">

## Round 1 (<date>)

### Scope
- Base: <dev>
- Branch: <branch>   Changed code files: <n>
- Starting checks: tests <pass / fail>, lint <pass / fail / none>, typecheck <pass / fail / none> (command: <command>)

### Summary
| Step | Findings | Fixed | Left open | Notes |
|---|---|---|---|---|
| /code-review | | | | built-in / fallback (not the built-in review) |
| /security-review | | | | built-in / built-in, filtered / fallback checklist / skipped (reason) |

### 1. /code-review (correctness)
| # | Severity | Location | Problem | Result | Commit |
|---|---|---|---|---|---|
| 1 | high / medium / low | `path:line` | | fixed / left open (reason) / judged wrong (reason) / out of scope | <short SHA> |

### 2. /security-review
| # | Severity | Location | Problem | Result | Commit |
|---|---|---|---|---|---|

### Final checks
- tests <pass / fail>, lint <pass / fail / none>, typecheck <pass / fail / none>

### Open items
| # | Item | Why it was not fixed | Who decided |
|---|---|---|---|
```

Rules:

- Every finding gets one row, including the ones the user declined, you judged wrong, or were out of scope. State the reason.
- A fixed finding names the commit that fixed it.
- Write the report after each step, not only at the end, so an interrupted review still leaves a record.
- If a step could not run, say which step, why, and what was done instead.
