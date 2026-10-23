---
name: propose-yr
description: "Clarify requirements and write an OpenSpec-style change proposal: proposal.md plus a delta spec of testable requirements and scenarios. Two modes: greenfield (full interview) and feature (short, graph-aware). No design or tasks file. Use for /propose-yr, or when a flow needs requirements settled before design or code."
---

# Propose (yr)

Pin the requirements down and record them as an OpenSpec-style change. The interview method is **grilling-yr**. The result is two files in the change folder, `openspec/changes/<name>/`:

- `proposal.md`: why, scope, and the approach in a few lines.
- `specs/<domain>/spec.md`: the delta spec. Requirements and scenarios. These are the testable part.

There is no `design.md` and no `tasks.md`. The design is **architect-yr**'s `architecture.md`. The task list is the todo list of the implementation.

Language: talk to the user in Traditional Chinese. Write every file in English. Keep code identifiers and the user's domain terms exactly.

## Inputs from the caller

- `<name>`: the change name in kebab case, already decided by the entry skill.
- The mode: `greenfield` or `feature`.
- `<repo>` and the current branch.

## Step 1. Load the method

Call the Skill tool for **grilling-yr**. If it will not load, read its `SKILL.md` from the `skills/` folder. Follow it: rounds, options with a recommended solution for each question.

Read the templates: [`references/proposal-template.md`](references/proposal-template.md) and [`references/delta-spec-template.md`](references/delta-spec-template.md).

## Step 2. Read what exists

- `openspec/specs/*/spec.md` if present. These are the current requirements. A feature extends or changes them.
- `openspec/graph.md` and, in `feature` mode, the result of **graph-yr** `read` for the area the feature touches.
- Facts about the code are your job to find, never the user's. Ask the user only for decisions.

## Step 3. The interview

These rules keep the interview about requirements and not about solutions.

1. **Need before solution.** When the user names a solution ("use Redis", "add a queue"), ask what need it serves. Record the solution as a constraint only when it is a real one, such as an existing system or a company rule.
2. **Every requirement is testable.** A requirement is one sentence with SHALL or MUST. It has one or more scenarios in GIVEN / WHEN / THEN form. A requirement with no scenario is not finished.
3. **Ask for out-of-scope items.** Ask what is not part of this change. Write it down in the proposal.
4. **Chase vague words.** "Fast", "simple", "secure", "scalable", "later": ask for a number, an example or a date.
5. **Walk edge cases.** Empty input, failure halfway, two users at once, a huge input. Each answer becomes a scenario or an out-of-scope line.
6. **No design here.** Types, modules and code shape belong to **architect-yr**. Technical constraints (language, platform, existing systems, company rules) go in the proposal under Scope.

**Names matter.** A requirement name is unique in its domain. A scenario name is unique in the change, and its test is `test_<scenario name in snake_case>`. Names are used to match MODIFIED and REMOVED later, so pick them once and keep them.

### `greenfield` mode

Run the full interview until the frontier of the design tree is empty. Cover: the goal and who it is for, the capabilities (each becomes a domain, usually 1 to 5), each requirement with scenarios, out of scope, constraints (language, platform, deployment, company rules), and open questions. Group the requirements by domain. If the user describes an event-driven service, note it in the proposal's Scope, because **architect-yr** has a reference architecture for it.

### `feature` mode

The user has already stated the requirement. Keep it short: one or two rounds.

1. Restate the requirement in one or two sentences, and name the domain(s) it touches from `openspec/specs/`. A new capability gets a new domain.
2. Draft 2 to 5 scenarios yourself from the requirement, the existing spec and the graph. Include at least one edge or failure case.
3. Ask in one round: the scenarios (confirm, change, add), out of scope, and anything you could not find out from the code. Give your recommendation for each question.

If the feature changes an existing requirement, write it as MODIFIED with the whole requirement and all its scenarios. If it removes one, write REMOVED with a reason.

## Step 4. Write the files

1. Create `openspec/changes/<name>/proposal.md` from the template.
2. Create `openspec/changes/<name>/specs/<domain>/spec.md` for each domain from the template.
3. Validate the delta: run `python "<skill folder>/../archive-yr/scripts/openspec_archive.py" validate openspec/changes/<name>` with the project's venv Python or any Python 3. Fix every error. A warning about SHALL or MUST means the requirement is weak: fix it.
4. Never overwrite an existing change folder. If `openspec/changes/<name>/` already has a proposal, read it and update it.

## Step 5. Confirm and commit

1. Read the result back in a short summary, in Traditional Chinese: intent, scope and out of scope, each requirement with its scenario names, constraints, open questions.
2. Ask with `AskUserQuestion`: Approve / Revise. Revise until approved. Open questions need an owner and must not block approval unless they change a requirement.
3. Commit the change folder on the current branch: `docs: propose <name>`. Do not start design or code.
4. Report the paths and name the next step to the caller.
