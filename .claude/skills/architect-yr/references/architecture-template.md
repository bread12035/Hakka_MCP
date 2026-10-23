# Architecture template

File: `openspec/changes/<name>/architecture.md`. English. The design and its rationale, with the type sketch. One page. Sentence-case headings, no boilerplate. Replace the italic notes with actual content.

## Problem

*One paragraph. What we're trying to do, and what about the existing system or constraints makes the shape non-obvious. If [Phase A](../SKILL.md) surfaced constraints the design must honor (existing types to interop with, callers we can't break, invariants that crossed our boundary), name them here so the reader sees the same constraints you saw.*

## Usage (caller's view)

*Write this first, before the type sketch. Show the README or quickstart the consumer reads, plus two or three realistic call sites in their own code. What they import, what they call, what comes back. The type sketch in [Shape](#shape) is derived from this. The two must agree. When they diverge, reconcile the sketch to the usage, not the reverse. The caller's experience is the spec. The types serve it.*

## Shape

*The recommended architecture. Data structures first. Then how data flows through the signatures. Name the load-bearing decisions. State which invariants are encoded in types, where validation lives, and what the system deliberately does not do. Judge interface depth explicitly. State what complexity the public surface hides, what remains exposed to callers, and why the interface is no larger than needed. Cite the principle behind each decision (e.g., `per boundary-discipline`). Don't restate it.*

## Synthesis decision

*Filled in by [arena](../../arena-yr/SKILL.md). Records which candidate became the base and why, what was adapted from each of the others, and what was rejected and why.*

## Tradeoffs accepted

*One bullet per tradeoff the chosen shape makes. Form: "we accept X in exchange for Y." Name anything a future reader might mistake for an oversight, including things that look like premature optimization or premature simplification.*

## Alternatives considered

*Required. Name at least one concrete alternative shape, with one line on why it lost. Judge each alternative on interface depth, not implementation simplicity alone. Name the complexity it exposes to callers and the complexity it hides. Two or three alternatives belong here when the design space had real contenders. One is fine when the constraints forced the answer, with the conclusion phrased as "this was the only viable shape because..." Avoid listing flavors of the same shape. This section covers design alternatives the chosen shape considered and rejected, not other runner candidates.*

## Implementation reconciliation

*During implementation, record accepted deviations and their acceptance sources here, and update the affected usage, outcome contracts, signatures, and ownership in this design. Record why local deviations leave the shared contract valid. Keep unaccepted changes unresolved. Reconcile before closing a unit or handing its contract to the next worker.*

## Open questions and risks

*Things you noticed during the sketch that the human needs to weigh in on, and risks worth flagging before implementation starts. Phrase as questions, not assertions, so the human's answer is the resolution rather than a comment.*

## Packages (new project only)

*A table: package, what it is for, which module uses it, why the standard library is not enough, alternative considered. Written before anything is installed, and approved by the user.*

## Tooling (new project only)

*The Python version found in the environment, the test command, and the lint and type-check commands if any. These go into the status file too.*

## Service contract (only when a reference architecture for an event-driven service is used)

*The event types and their models, the disposition table (outcome to ack or nack, with the retry bound), the idempotency key, the thread pool size, the broker prefetch and the shutdown limit, and what is async and what is threaded. See `micro-service-architecture.md`.*

## Next implementation step

*The first thing to build against the sketch. One sentence. What you'd start writing immediately after synthesis (or after Phase D sign-off, if a checkpoint was opted into).*
