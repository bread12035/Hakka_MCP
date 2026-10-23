# Proposal template

File: `openspec/changes/<name>/proposal.md`. English. Short. A reader should understand the change in one minute.

```markdown
# Proposal: <Title>

## Intent
<Why this change exists. The problem or need, for whom, in two to four sentences. No solution yet.>

## Scope
In scope:
- <capability or behavior, one line each. Link to the requirement names in the delta spec>

Out of scope:
- <what this change does not do, and why when it is not obvious>

Constraints:
- <language, platform, existing systems, company rules. Delete the line if none>

## Approach
<Three to six lines. The shape of the solution in plain words. Point to `architecture.md` for the design once it exists. Do not design here.>

## Open questions
- <question> (owner: <who>)
```

Notes:

- Delete `Open questions` when it is empty.
- For a micro-service, say so in Scope, for example "An event-driven service that consumes `order.created` events."
- After the change is finished, **archive-yr** appends an `## Outcome` section.
