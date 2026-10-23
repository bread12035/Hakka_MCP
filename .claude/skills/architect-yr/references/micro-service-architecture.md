# Reference architecture: event-driven micro-service (Python)

A proven shape for a service that consumes events from a broker, may expose an API, and runs each event on its own thread. It is the author's usual layout. It is a **reference**, not a rule. Use it when the proposal describes a service of this kind, or something close. Adopt it, adapt it, or reject it, and record the choice in `architecture.md` (under "Shape", with the reason, and under "Alternatives considered" if you reject it).

Read it fully before you sketch. Then write a `## Service contract` section in `architecture.md` (see the end of this file).

## Layout

Each file has one job. Imports point one way only: down this list.

| Layer | Owns | Must not |
|---|---|---|
| `main.py` | Composition root. Loads config, builds the clients and the worker, starts them, handles signals and shutdown. | Hold any business logic or a `try/except` for events. |
| `worker.py` | The flow for one event: parse, call helpers, map the outcome to ack or nack. All exception handling for events. The only file that touches the broker's ack and nack. | Hold domain rules. Those go to `helper.py`. |
| `helper.py` | Internal logic. Pure functions and small classes that take models and injected clients, and return results or raise typed errors. | Import `worker` or `main`. Ack or nack. Read environment variables. |
| `models.py` | Data shapes: event payloads, results, domain types. | Import any other file of this service. |
| `common/` | Shared tools with no domain knowledge: logging setup, retry and backoff, the error types, small utilities. | Know about events or the broker's payloads. |
| `config/` | Typed settings, loaded once at startup from the environment or a file, then injected. | Be read from anywhere except `main.py`. |

Import direction: `main` → `worker` → `helper` → `models`. `common` and `config` are leaves that any layer above may import. Nothing imports upward.

Grow by splitting inside a layer (`helper/` as a package, one file per capability), never by adding a new layer. Keep `common/` honest: a utility moves in only when two or more modules use it (**principle-laziness-protocol-yr**, **principle-minimize-reader-load-yr**).

## Design rules

1. **Data shapes first.** Name the event payloads and results in `models.py` before any logic. Use typed models, and make invalid states unrepresentable (**principle-model-the-domain-yr**, **principle-type-system-discipline-yr**).
2. **Parse at the boundary.** `worker.py` parses the raw message into a model once. A message that does not parse is a permanent error, and it is never retried. Everything below trusts the types (**principle-boundary-discipline-yr**).
3. **Config is injected.** `config/` builds one frozen settings object at startup and fails fast on a missing or invalid value. `main.py` passes it, or the clients built from it, into the worker and helpers. Nothing else reads `os.environ`. Never log secrets (**principle-boundary-discipline-yr**).
4. **Business logic stays pure.** `helper.py` gets its inputs as arguments, so it tests without a broker (**principle-boundary-discipline-yr**, **principle-test-behavior-not-implementation-yr**).
5. **The outcome of an event is a decision, and it is made once.** Define an error taxonomy in `common/` (for example `TransientError` and `PermanentError`) and a disposition table in `worker.py`:

   | Outcome | Disposition |
   |---|---|
   | Success | ack |
   | Permanent error (bad payload, rule violation) | nack without requeue, to the dead-letter path when the broker has one |
   | Transient error (timeout, dependency down) | nack with requeue, with a bounded retry count |
   | Unexpected exception | treat as transient up to the retry bound, then as permanent, and log it with the event id |

   Every event ends in exactly one ack or nack, including when the handler raises (**principle-model-the-domain-yr**).
6. **Handlers are idempotent.** A nack with requeue, a crash before the ack and a broker redelivery all run the handler again with the same event. Pick the idempotency key (usually the event id) and make a second run converge to the same end state (**principle-make-operations-idempotent-yr**).
7. **One event, one thread, nothing shared.** Each event runs on its own thread, and everything it mutates is created inside that thread's call. No mutable module-level state. Shared objects are limited to clients that are documented thread-safe, or each thread builds its own. Eliminate sharing before you reach for a lock (**principle-separate-before-serializing-shared-state-yr**).
   - **Bound it.** One thread per event still needs a cap. Run the threads in a pool sized from config, and tie the broker prefetch to the same number, so a burst of events cannot create unlimited threads (**principle-foundational-thinking-yr**).
   - **Ack from the right thread.** Many broker clients are not thread-safe. Check the client's documentation. If the ack or nack must run on the connection's thread, hand it back through the library's thread-safe call or a queue. Do not call it from the event thread by default.
   - **Shut down cleanly.** On a stop signal, stop taking new events, let the in-flight threads finish within a time limit from config, nack what did not finish so the broker redelivers it, then close the clients.
8. **API flows are async.** Handlers and outbound HTTP calls use `async def` and an async client. A blocking call inside a coroutine stalls the whole loop, so a blocking library goes through `run_in_executor` or a thread. Event threads are synchronous by default. If an event thread must call an async function, run it with `asyncio.run` inside that thread. Never start a second loop on a thread that already has one. If the design needs the event threads and the API to share one loop, say so in `architecture.md` and get the user's agreement.
9. **Every log line carries the event id.** Set it once at the top of the event thread, in `worker.py`. Log the disposition and the duration at the end of each event.
10. **Encode the layering.** Add `tests/test_layers.py` from [`micro-service-layer-test.py`](micro-service-layer-test.py) and set its package name and layer order. The import direction, the rule that only `worker.py` acks, and the rule that only `config/` reads the environment then fail a test instead of relying on review (**principle-encode-lessons-in-structure-yr**, **principle-build-the-lever-yr**).

## What to write in `architecture.md`

Add a `## Service contract` section:

- The event types and their models.
- The disposition table (outcome to ack or nack, with the retry bound).
- The idempotency key.
- The thread pool size, the broker prefetch and the shutdown time limit, all from config.
- What is async and what is threaded.

## For the skeleton (ground-up mode)

- Create the files and folders of the layout, with stub bodies, plus `tests/test_layers.py`.
- Besides the one skipped test per scenario, add skipped tests for the checks below, so the implementer has a checklist.

## Checks to carry into the implementation

State these in `architecture.md` under "Next implementation step". The implementer runs them as part of verification (**principle-prove-it-works-yr**). If a throughput or latency number is reported, explain what limits it first (**principle-explain-the-number-yr**).

- **Disposition per outcome.** One test per row of the disposition table, asserting exactly one ack or nack.
- **Redelivery.** Feed the same event twice and assert the same end state.
- **Parallel events.** Run many events at once through the worker with a fake broker, and assert no state leaks between them and the pool cap holds.
- **Shutdown.** Stop during in-flight events and assert they finish or are nacked.
- **No blocking in the loop.** For API flows, assert a slow dependency does not delay other requests.
- **Build order.** Bottom-up: `models.py`, `config/`, `common/`, `helper.py`, `worker.py`, `main.py`. In multi-agent mode, the independent `helper` capabilities can run in parallel after the first three.
