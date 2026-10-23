---
name: grilling-yr
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question, give the user **options to choose from**, and give your **recommended solution**. Then wait for the user's answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <the question, with one to three sentences of context: what it decides and what depends on it>

- **A (recommended)** <option name>: <what it means in practice. Main benefit. Main cost.>
- **B** <option name>: <what it means in practice. Main benefit. Main cost.>
- **C** <option name>: <what it means in practice. Main benefit. Main cost.>
- **Other**: your own answer

➡️ I recommend **A**, because <one sentence tied to this user's situation>.

---

❓ **Q2** - ...
```

Rules for the options:

- **Two to four real options.** Each one is something a sensible person could choose. Do not pad with strawmen to make the recommendation look good. If only one answer is reasonable, give it as a proposed default and add the one alternative worth considering.
- **The recommendation comes first** and is marked `(recommended)`. It is a concrete solution, not "it depends". State the trade-off honestly: every option names its main cost.
- **Options differ in what they mean, not in wording.** Mutually exclusive unless you say "pick any".
- **Open questions get proposals.** When the answer is a name, a number, a date or a scope, propose a specific value and one or two alternatives. For "what is the goal?" style questions, offer the likely readings drawn from what you already know, and let the user correct them.
- **Facts you found, not asked.** If you already looked something up, say what you found inside the question and build the options on it.
- **Easy to accept.** Word each question so that "A", "yes" or "agree" accepts your recommendation. The user can also answer with a mix ("Q1 A, Q2 B, Q3 other: ...") or with free text.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one. Start each later round with one line listing what is now settled.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
