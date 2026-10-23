---
name: yr-coding-skills
description: "Entry point for my coding workflow. Menu: 1 build from zero (ground-up), 2 add a feature, 3 debug, 4 refactor, 5 list the sub-skills and what each does. Routes to a flow, keeps a status file so work can resume, and lands the result on dev. Use for /yr-coding-skills."
disable-model-invocation: true
---

# yr-coding-skills

One entry. It routes to a flow. Each flow chains the same sub-skills in a fixed order, and every sub-skill also works alone.

Conventions for every flow:

- **Language.** Talk to the user in Traditional Chinese. Write every file in English: proposals, specs, architecture, review reports, commit messages, PR text.
- **Branches.** All work is based on `dev`. A flow works on `feat/<name>`, `fix/<name>` or `refactor/<name>`. The pack never commits to the default branch (`master` or `main`). Promotion from `dev` to it is a pull request the user makes by hand.
- **Folders.** Everything the workflow writes is under `openspec/`: `specs/` (what the system does now), `changes/<name>/` (one change in progress), `changes/archive/` (finished changes), `reviews/<name>.md`, `graph.md`.
- **Name.** `<name>` is the change name in kebab case. It is decided once and used for the change folder, the branch and the review report.
- **Shell.** The user is on Windows. Use `git` and `python` only. Never `activate` the venv. Use `git -C "<repo>"` and absolute paths. See **repo-setup-yr**.

## Step 1. Resume check, then the menu

If the current folder is not a git repo, look one level down for repos that have an open change (`*/openspec/changes/*/status.md`), and use that repo. Otherwise, if the current folder is inside a git repo, look for `openspec/changes/*/status.md` (not in `archive/`) whose `next:` is not `done`, and note the current branch. If you find one, show it and ask with `AskUserQuestion`: continue from its `next` step, or start something new. Continue means: read the status file, then run the flow's remaining steps from `next`. Also ask when the branch is `feat/*`, `fix/*` or `refactor/*`, is ahead of `dev`, and has no open change: the archive is done and only landing is left, so offer to run **Landing**.

Otherwise show this menu in Traditional Chinese, as plain numbered text. Do not use `AskUserQuestion`, because it holds only four options.

```
1. Build from zero (ground-up)
2. Add a feature to an existing codebase
3. Debug
4. Refactor
5. List the existing sub-skills and what each does
```

If the user's message already names the job, say which option you read it as and go.

Option 5: print [`references/skills-index.md`](references/skills-index.md) as a short table and stop. Ask whether they want to start one of the flows.

For options 1 to 4, open a task list from the flow below, tell the user the plan in one or two lines, and start.

## The status file

`openspec/changes/<name>/status.md` is the memory of the flow. Create it from [`references/status-template.md`](references/status-template.md) as soon as `<name>` is known. After every step, set `next:` to the step that runs next, add one line to the log, and keep the facts current (repo, branch, Python path, commands, the user's choices). Read it first after a context reset. It is committed with the next commit, so it also travels with the branch.

## Flow 1. Build from zero

1. **Repo and environment.** Run **repo-setup-yr** in `full` mode. It asks which repo, clones or pulls it, checks out `dev`, creates `.venv` and installs the requirements.
2. **Name.** Ask for the change name. Suggest `initial-<project>` and one alternative. Create the status file.
3. **Proposal.** Run **propose-yr** in `greenfield` mode. Result: `proposal.md` and the delta specs. Wait for the user to approve.
4. **Architecture.** Run **architect-yr** in `ground-up` mode. Result: `architecture.md`, the package list in `requirements.txt` installed in `.venv`, the tooling, and the code skeleton. Its checkpoint asks the user to approve, compare with arena, or revise. The commands (test, lint, typecheck) go into the status file.
5. **Land the design.** All of this is committed on `dev`, and the user has approved the design but has not yet seen the skeleton. Show the skeleton in a few lines: the file tree and one or two stub signatures. Ask with `AskUserQuestion`: push now (recommended) / let me look first, wait. On push: `git -C "<repo>" push -u origin dev`. `dev` is not protected. If the push fails, show the error and stop.
6. **Work branch.** Run **repo-setup-yr** `branch feat/<name>`.
7. **Implement.** Run **poteto-mode-yr** against the skeleton. Use the Feature playbook. It asks the TDD and sub-agent options first.
8. **Review.** Run **review-pass-yr**. It lists the problems, the user chooses what to fix, and it writes `openspec/reviews/<name>.md`.
9. **Graph.** Run **graph-yr** `sync`, then `snapshot`. The codegraph index is created now, because there was no code before.
10. **Archive.** Set `next: land` in the status file, then run **archive-yr**.
11. **Land.** Run the Landing playbook of **poteto-mode-yr**.

## Flow 2. Add a feature

1. **Repo and environment.** Run **repo-setup-yr** in `light` mode.
2. **Requirement.** Ask the user to state the requirement in their own words. Then decide `<name>` with them (one suggestion, one alternative).
3. **Branch and status.** Run **repo-setup-yr** `branch feat/<name>`. Create the status file.
4. **Graph.** Run **graph-yr** `sync`, then `read` over the area the feature touches.
5. **Proposal.** Run **propose-yr** in `feature` mode. It reads the graph and the current specs, drafts the scenarios, and the user confirms them once. The proposal and the delta spec are written now.
6. **Implement.** Run **poteto-mode-yr** with the Feature playbook. The playbook runs **architect-yr** in design-only mode when the change crosses a function or module boundary. It asks the TDD and sub-agent options first.
7. **Review.** Run **review-pass-yr**.
8. **Graph.** Run **graph-yr** `sync`, then `snapshot`.
9. **Archive.** Set `next: land`, then run **archive-yr**. It checks the scenarios against the tests, appends the outcome to the proposal and merges the delta into `openspec/specs/`.
10. **Land.** Run the Landing playbook.

## Flow 3. Debug

No proposal. The change folder holds the status file and nothing else.

1. **Repo and environment.** Run **repo-setup-yr** in `light` mode.
2. **Report.** Ask the user to describe the bug: expected, actual, and how to trigger it. Decide `<name>` with them.
3. **Branch and status.** Run **repo-setup-yr** `branch fix/<name>`. Create the status file.
4. **Graph.** Run **graph-yr** `sync`, then `read` over the affected area.
5. **Fix.** Run **poteto-mode-yr** with the Bug fix playbook. It reproduces the bug and finds the root cause. **It then stops and lists the root cause and the proposed fix, and waits for the user's approval before it changes any code.** It asks the TDD and sub-agent options first.
6. **Review.** Run **review-pass-yr**.
7. **Graph.** Run **graph-yr** `sync`, then `snapshot`. It commits only if the structure changed.
8. **Archive.** Set `next: land`, then run **archive-yr**. There are no deltas, so the folder just moves.
9. **Land.** Run the Landing playbook.

## Flow 4. Refactor

No proposal. A refactor changes no requirement. If a scenario in `openspec/specs/` would have to change, it is a feature: say so and switch to Flow 2.

1. **Repo and environment.** Run **repo-setup-yr** in `light` mode.
2. **Problem.** Ask the user to describe what is wrong with the current structure and what they want. Decide `<name>` with them.
3. **Branch and status.** Run **repo-setup-yr** `branch refactor/<name>`. Create the status file.
4. **Graph.** Run **graph-yr** `sync`, then `read` over the code to restructure.
5. **Refactor.** Run **poteto-mode-yr** with the Refactoring playbook. Its first step lists the behavior contract from the graph (callers, impact, covering tests) and the specs, and the user confirms it. Pins are written with **tdd-yr** if the user chose TDD. When the target shape crosses a function or module boundary, the playbook runs **architect-yr** in design-only mode, and its checkpoint offers an arena comparison.
6. **Review.** Run **review-pass-yr**.
7. **Graph.** Run **graph-yr** `sync`, then `snapshot`.
8. **Archive.** Set `next: land`, then run **archive-yr**.
9. **Land.** Run the Landing playbook.

## Rules for every flow

- Load each sub-skill with the Skill tool. If it will not load, read its `SKILL.md` from the `skills/` folder and follow it.
- Do not skip a step silently. A skipped step stays in the task list with `skip: <reason>`.
- Hand the next skill what the last one made: the paths, the options the user chose, the commands. Read them from the status file. Do not make the user repeat themselves.
- Stop at each "wait for the user" point. Never start design or code before the proposal is approved.
- The test, lint and typecheck commands come from the status file. Always call the venv's Python by path.
- If the user changes the job midway (a feature turns out to be a refactor), say so, update the status file, and switch to that flow's remaining steps.
- Finish with a short report in Traditional Chinese: what was produced (paths, commits), where the branch stands, what the review found, what is open.
