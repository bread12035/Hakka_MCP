---
name: review-pass-yr
description: "One review round with Claude Code's built-ins, in this order: /code-review, then /security-review. Report first: list the problems, the user chooses what to fix, one pass each, no loops. Reviews the work branch against dev. Writes a report to openspec/reviews/. Use for /review-pass-yr, or as the review stage of a coding flow."
---

# Review pass (yr)

Run Claude Code's built-in review commands once each, in a fixed order, list what they find, and fix what the user accepts.

Order: `/code-review`, then `/security-review`. There is no `/simplify` step. One pass each. Do not loop. Re-run a step only when the user asks.

The result is written down in `openspec/reviews/<name>.md`, shaped by [`references/review-report-template.md`](references/review-report-template.md). The report is part of the job. Write it in English.

## Step 0. Scope and a green start

1. Read `openspec/changes/<name>/status.md` for the base (`dev`), the commands, and the Python path. If there is no status file, use `dev` and ask for the commands.
2. The review covers the work branch against `dev`: `git -C "<repo>" diff --name-only dev...HEAD`. You must be on the work branch. If you are on `dev`, stop and ask.
3. Tell the user the scope in one line: branch, base, number of changed files. Ignore `openspec/` files when you count code files.
4. Run the test command, and the lint and typecheck commands if they are set. If they fail, say so and stop. A review of a broken build wastes the round.
5. Create or extend the report. Read the template. If `openspec/reviews/<name>.md` exists, add a new round section instead of overwriting.

## Step 1. `/code-review`

Call the Skill tool with `code-review`. Pass the current branch name as the target and the effort level `high`. Do not pass `--fix` or `--comment`. If the Skill tool cannot run it, ask the user to type `/code-review high <branch>` and wait for the result.

Check the scope it actually reviewed. The command's documented targets are a pull request number, a branch or a path, and it is not documented how a branch is compared with `dev`. So compare the files in its findings with the list from Step 0:

- A finding in a file outside the `dev...HEAD` diff is out of scope. Put it in the report as "out of scope" and do not fix it.
- If the review says it saw nothing, or its scope is clearly wrong, say so, and offer a fallback: you review `git diff dev...HEAD` yourself for correctness bugs, and the report labels it "fallback, not the built-in review".

**List first.** Show the findings in a short table, most serious first: number, severity, location, problem. Then ask with `AskUserQuestion`: fix all / fix selected / skip. Fix only the accepted ones yourself, following **poteto-mode-yr**. Run the tests again. Commit the fixes as their own commit.

Record every finding in the report as one row: severity, location, what you did (fixed, left open with the reason, judged wrong with the reason, or out of scope), and the commit SHA.

## Step 2. `/security-review`

`/security-review` is a built-in command, so a skill may not be able to run it. It needs an `origin` remote. It compares the branch with the origin's default branch (`master` or `main`), not with `dev`. When `dev` is ahead of the default branch, it can also see commits that are on `dev` but not yet promoted.

1. Compare the two scopes: `git -C "<repo>" diff --name-only dev...HEAD` and `git -C "<repo>" diff --name-only origin/<default>...HEAD`. If the second list is longer, tell the user the built-in review will see more than this branch.
2. Ask with `AskUserQuestion` when the scopes differ:
   - **Run the built-in and filter (recommended).** Findings in files outside the `dev...HEAD` list are marked "out of scope" in the report and not fixed.
   - **Checklist on the dev diff.** You review `git diff dev...HEAD` with the checklist below. The report labels it "fallback, not the built-in review".
   - **Skip.** The report says skipped, and why.
   If the scopes are the same, just run the built-in.
3. To run the built-in: try the Skill tool with `security-review`. If that fails, ask the user to type `/security-review` and paste or confirm the findings. If there is no `origin` remote, use the checklist.

Checklist: injection (SQL, command, template), authentication and authorization gaps, secrets and credentials in code or config, unsafe deserialization, path traversal, SSRF, unvalidated input at boundaries, sensitive data in logs or responses, vulnerable or unpinned dependencies, missing rate limits on costly endpoints.

**List first**, as in Step 1. Fix only what the user accepts. Run the tests. Commit the fixes as their own commit.

## Step 3. Close

1. Run the tests, the lint and the typecheck once more. Record the result in the report.
2. Fill in the summary table and the list of open items.
3. Commit the report on its own: `docs: add review report for <name>`.
4. Do not push and do not open anything. Landing comes after the archive.
5. Tell the user the report path and show the summary table in your reply, in Traditional Chinese.
