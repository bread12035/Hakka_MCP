---
technique: skill-state
status: draft
source: Maintainer description. Handoff through a status file. No measured run yet.
---
# Skill state: hand off through a status file

When work passes to a subagent or to a later step, pass a small status file, not the conversation.

## Rules

1. At the start of the task, create `status.json` in the working folder from the template in this route result. Keep its keys. Fill in what you know.
2. Keep it current: after each step, update the fields that changed. Short values: paths, ids, decisions, one-line facts. No pasted file content or logs.
3. A subagent gets the path to `status.json` and one task. It reads that file and only the files it names. It does not get the conversation history.
4. A subagent writes its result back into `status.json`: what it did, what it found, what is next. Its reply to you is one or two lines.
5. After a context reset or a new session, read `status.json` first and continue from its next step.
6. If the user gave you their own template, use it as is.

## When to break the rules

A task small enough to finish in one step needs no status file.
