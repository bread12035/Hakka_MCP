---
technique: model-routing
status: draft
source: Hakka vibe experiment 6 (plan first, then execute). No measured run yet.
---
# Model routing: strong model plans, small model executes

Use the strongest model only where judgment is needed.

## Rules

1. Plan with the main model: understand the request, decide the steps, and write each step so that it can be done without the planning context.
2. Give mechanical steps to a smaller, cheaper model when your environment lets you pick a model for a subagent or a step. Examples: search and summarize files, apply a planned edit to many files, reformat data, run commands and report results.
3. Keep on the strong model: the plan, design decisions, debugging an unclear failure, reviewing the result, anything about security or money.
4. Each delegated step gets a clear input, a clear output and a check. If a small model fails the check twice, do the step on the strong model.
5. Do not delegate a step that is shorter to do than to describe.
6. If your environment cannot choose models, still plan first and keep each execution step short and bounded.

## When to break the rules

The task is one short step. Do it directly.
