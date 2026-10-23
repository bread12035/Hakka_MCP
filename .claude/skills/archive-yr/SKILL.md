---
name: archive-yr
description: "Finish an OpenSpec-style change. Check that every scenario has a test, record the outcome in the proposal, merge the delta specs into openspec/specs with a script, and move the change folder to the archive. Use for /archive-yr, or as the last bookkeeping step of a coding flow."
---

# Archive (yr)

Close a change. The deltas become part of the current specs, and the change folder moves to `openspec/changes/archive/<date>-<name>/`.

The merge is done by a script, `scripts/openspec_archive.py`, so the result does not depend on how carefully a model edits a file. Use the project's venv Python or any Python 3. The script uses only the standard library.

Run it from the repo root with the path of this skill's folder: `"<python>" "<this skill's folder>/scripts/openspec_archive.py" <command> ...`.

## Step 1. Which kind of change

- **With deltas** (`openspec/changes/<name>/specs/` exists): a feature or a new project. Do all steps.
- **Without deltas** (a bug fix or a refactor): skip Steps 2 and 3. Go to Step 4. The folder still moves, so the status and the notes stay in the history.

## Step 2. Reconcile the scenarios with the code

1. Validate the deltas: `validate openspec/changes/<name>`. Fix errors.
2. Check the tests: `check openspec/changes/<name> --tests tests` (add other test folders if the project has them). It reports scenarios with no `test_<scenario name>` and tests that still skip.
3. Show the user the report. For each missing or skipped scenario, choose with the user: write the test now, or keep the scenario and note why it has no test, or drop the scenario from the delta because the behavior changed. Do not archive a scenario you know is false.
4. If the implemented behavior differs from the delta, edit the delta so it describes what was built, and tell the user what changed. The spec must match the code.

## Step 3. Record the outcome

Append to `openspec/changes/<name>/proposal.md`:

```markdown
## Outcome
- Finished: <date>
- Branch: <branch>
- Review report: openspec/reviews/<name>.md
- Differences from the plan: <one to three lines, or "none">
- Scenarios without a test: <list with the reason, or "none">
```

## Step 4. Apply

1. Dry run: `apply openspec/changes/<name> --specs openspec/specs --archive openspec/changes/archive --dry-run`. Show the user which specs are created or updated.
2. Run the same command without `--dry-run`. It validates everything first and writes nothing on an error. An error such as "ADDED requirement already exists" means the name collides with the spec: change the delta to MODIFIED, or rename.
3. Commit: `docs: archive <name>`. Stage `openspec/` only.

## If a spec conflicts later

If landing hits a git conflict in a spec file, `remerge` replays the archived deltas onto the other side's spec without moving anything. See the Landing playbook of **poteto-mode-yr**.

## Step 5. Report

Say which specs changed, where the change folder went, and the scenario coverage. Hand back to the caller. The next step is landing the branch.
