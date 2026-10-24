---
technique: pass-by-reference
status: draft
source: Hakka vibe experiment 2 (DataRef). No measured run yet.
---
# Pass by reference

Large data stays where it lives. Only a preview enters the conversation.

The test is simple: does the full content of the data become characters in your context? If yes, it is pass by value, even when a query cut it down to ten rows.

## Rules

1. Never paste or read a whole large file, table, log or API response into the conversation. Large means more than about 200 lines or 20 KB.
2. Look first with a bounded preview: the first 20 lines, the column names and types, the row count, the file size.
3. Do the work with code that runs where the data is: a script, a query, a shell pipeline. Read back only the result: a count, a short table, the few matching lines.
4. Pass data between steps by path or name, not by content. Write intermediate results to a file and refer to the file.
5. When you hand work to a subagent, give it the path and the question, not the data.
6. A result you must show the user is also bounded: show the top rows and say how many there are in total.

## Examples

Bad: read a 50 MB CSV, then describe it.
Good: run a script that prints the shape, the columns and five sample rows, then answer.

Bad: copy a 3,000 line log into the reply to find an error.
Good: search the log for the error pattern and show the five lines around each hit.

## When to break the rules

The user asks to see the whole content, or the content is small enough that a preview would be most of it.
