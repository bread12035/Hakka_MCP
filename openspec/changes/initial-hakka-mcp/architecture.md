# Architecture: initial-hakka-mcp

## Problem

One remote MCP server must hand Claude Code and Cowork the right token-saving skill set for a client and task type, and count who used what with an estimated saving. Three things make the shape non-obvious. The catalog (techniques, skills, configs, numbers) is authored as files and changes often, while usage history must never be rewritten by a later recalibration. The task-type list grows over time and must appear as an enum in the tool schema without a second hand-kept list. Storage is SQLite now and Postgres later, and auth is a per-user API key now and SSO later, so both must sit behind one seam each.

## Usage (caller's view)

Maintainer:

```text
hakka-mcp check   --catalog catalog/                 # validate; exit 1 with every problem listed
hakka-mcp serve   --catalog catalog/ --db sqlite:///data/hakka.db [--allow-drafts] --port 8000
hakka-mcp keys issue alice [--admin]                 # prints the key once
hakka-mcp keys list | hakka-mcp keys revoke alice
hakka-mcp report  --group-by task_type [--current-estimates] [--csv]
```

User, once:

```text
claude mcp add --transport http hakka https://hakka.example.com/mcp --header "Authorization: Bearer <key>"
```

Model, inside a session:

```python
route(client="code", task_type="code-bugfix", session_id="s-81f2",
      rationale="User reports a failing test in the payment module")
# -> RouteResult(config_id="code/code-bugfix", config_version=3, fallback=False,
#                skills=[SkillText(id="code-graph", draft=False, text="..."), ...],
#                status_template=None)

get_usage_stats(group_by="task_type", current_estimates=False)   # admin key only
# -> Stats(rows=[StatsRow(group="code-bugfix", users=12, calls=40, sessions=31,
#                         saved_tokens={"measured": 0, "vendor-claim": 0, "estimate": 930000},
#                         saved_usd={...}), ...], total=StatsRow(...))
```

Catalog on disk, the one place the maintainer edits:

```text
catalog/
  pricing.yaml                      # USD per million input / output tokens
  skills/<skill-id>/SKILL.md        # frontmatter: technique, status, source, version, license
  configs/<client>/<task-type>.yaml # one file per pair; default.yaml per client
  templates/status/<task-type>.json # skill-state default templates
```

```yaml
# catalog/configs/code/code-bugfix.yaml
version: 3
skills: [code-graph, ponytail-rules-only, model-routing]
expected_saving:
  percent: 20
  tokens: {input: 30000, output: 4000}
  provenance: estimate          # measured | vendor-claim | estimate
  source: https://...           # optional
```

## Shape

Two deep modules, two thin adapters.

```text
src/hakka_mcp/
  catalog.py   Catalog: load + validate files, resolve(client, task_type)   (owns: catalog files)
  ledger.py    Ledger: usage events, stats, API keys                          (owns: the database)
  server.py    build_app(catalog, ledger) -> ASGI app; tools route, get_usage_stats
  cli.py       check | serve | keys | report
```

Core types (`catalog.py`):

```python
class Client(StrEnum): CODE = "code"; COWORK = "cowork"
class Technique(StrEnum): PASS_BY_REFERENCE; CAVEMAN; PONYTAIL_RULES_ONLY; CODE_GRAPH; SKILL_STATE; MODEL_ROUTING
APPLICABILITY: Final[Mapping[Technique, frozenset[Client]]]   # the one matrix
class Provenance(StrEnum): MEASURED; VENDOR_CLAIM; ESTIMATE

@dataclass(frozen=True) class Estimate: percent: float; input_tokens: int; output_tokens: int; usd: float; provenance: Provenance; source: str | None
@dataclass(frozen=True) class Skill: id: str; technique: Technique; draft: bool; text: str
@dataclass(frozen=True) class Config: id: str; client: Client; task_type: str; version: int; skills: tuple[Skill, ...]; estimate: Estimate; status_template: str | None
@dataclass(frozen=True) class Resolution: config: Config; fallback: bool

class CatalogError(Exception): problems: tuple[str, ...]
class Catalog:
    @classmethod
    def load(cls, root: Path, *, allow_drafts: bool) -> Catalog      # raises CatalogError with all problems
    def resolve(self, client: Client, task_type: str) -> Resolution  # falls back to <client>/default
    def task_types(self) -> tuple[str, ...]                          # feeds the tool enum
    def estimates(self) -> Mapping[str, Estimate]                    # config_id -> current estimate
```

Ledger (`ledger.py`):

```python
@dataclass(frozen=True) class Principal: user_id: str; admin: bool
@dataclass(frozen=True) class UsageEvent: user_id: str; client: Client; task_type: str; session_id: str; rationale: str; resolution: Resolution; at: datetime
class GroupBy(StrEnum): TOTAL; CLIENT; TASK_TYPE; CONFIG
@dataclass(frozen=True) class StatsRow: group: str; users: int; calls: int; sessions: int; saved_tokens: Mapping[Provenance, int]; saved_usd: Mapping[Provenance, float]
@dataclass(frozen=True) class Stats: rows: tuple[StatsRow, ...]; total: StatsRow

class Ledger:
    def __init__(self, url: str)                                     # sqlite:///... now, postgresql://... later
    def record(self, event: UsageEvent) -> None                      # snapshots the estimate, truncates rationale to 200
    def stats(self, group_by: GroupBy, current: Mapping[str, Estimate] | None = None) -> Stats
    def issue_key(self, user_id: str, *, admin: bool) -> str
    def authenticate(self, raw_key: str) -> Principal | None         # None for unknown or revoked
    def list_keys(self) -> tuple[KeyInfo, ...]
    def revoke_key(self, user_id: str) -> None
```

Load-bearing decisions:

- **The catalog is immutable after load and validated whole.** `Catalog.load` collects every problem (missing skill, draft without `--allow-drafts`, technique outside `APPLICABILITY`, missing provenance, skill over 4 KB, duplicate pair, skill-state without template) and raises once. Everything downstream trusts the types (per boundary-discipline). Configs are keyed by their path, so a duplicate pair can only come from a mismatched `client`/`task_type` field, which the loader forbids by deriving both from the path.
- **One list per fact.** `APPLICABILITY` is the only matrix. Task types come from the files; the `route` tool's enum is built from `Catalog.task_types()` at startup, so adding a YAML file is the whole change (per encode-lessons-in-structure).
- **The event owns its numbers.** `Ledger.record` writes the config version, percent, tokens, USD and provenance onto the row. History reads the row; `current=` re-prices rows by `config_id` without touching them (per make-operations-idempotent: recalibration is a pure read).
- **Dedup is a query, not a write rule.** Every call is a row; `sessions` and savings count `DISTINCT (user_id, session_id, config_id)`. No upsert races, no lost calls (per separate-before-serializing-shared-state).
- **One owner per store.** `Ledger` alone touches the database, both tables (`usage_events`, `api_keys`). SQL is SQLAlchemy Core, so Postgres is a URL change. Keys are stored as SHA-256 hashes; keys are 32 random bytes, so a fast hash is sufficient.
- **Auth uses the SDK's bearer seam.** `server.py` passes a `TokenVerifier` that calls `Ledger.authenticate` and returns an `AccessToken(client_id=user_id, scopes=["admin"] or [])`. Tools read the principal with `get_access_token()`. The model never supplies a user id. SSO later replaces only the verifier.
- **`server.py` is an adapter.** Each tool parses arguments into domain types, calls `Catalog.resolve` and `Ledger.record`, and maps the result to the wire model. No policy lives there.

Interface depth: the public surface is `Catalog.load/resolve`, the `Ledger` methods, and `build_app`. Hidden behind it: YAML and frontmatter parsing, the matrix, fallback, draft policy, pricing, SQL dialects, hashing, dedup.

What it deliberately does not do: no caching layer (the catalog is in memory), no migrations tool (one `CREATE TABLE IF NOT EXISTS` at start; Alembic when Postgres lands), no hot reload (a config change is a deploy).

## Synthesis decision

Not run. Single-agent sketch.

## Tradeoffs accepted

- We accept a restart per catalog change in exchange for a catalog that is validated whole before it serves anything.
- We accept a dynamic `Enum` for `task_type` in exchange for one list of task types.
- We accept SQLAlchemy as a dependency in exchange for a Postgres move that changes the URL, not the module.
- We accept that `Ledger` owns two tables in exchange for one owner of the database and one connection setup.
- We accept that every call is stored, deduplicated only at read time, in exchange for no write-time race and a full call log.

## Alternatives considered

- **Catalog in the database.** Load YAML into tables at startup and resolve with SQL joins. It lost: the YAML and the tables are two copies of one truth (split ownership), and validation errors surface as constraint failures instead of a list.
- **One `Router` object that owns catalog, events and keys.** Smaller file count, but one class with three reasons to change, and tests for routing would need a database (shallow on each concern, wide overall).
- **Own Starlette middleware for auth instead of the SDK `TokenVerifier`.** It works without OAuth-shaped settings, but it duplicates what the SDK already does and moves the principal into request state that each tool would have to dig out.

## Implementation reconciliation

- `status_template` is a JSON object, not a string, on `Config`, the `route` argument and `RouteResult`. The SDK parses a JSON-looking string argument into an object before validation, so a string type rejected real calls. The catalog now also rejects a template that is not a JSON object. The shared contract holds: the caller still sends a template and gets one back. Accepted by the implementer; flagged for review.
- `build_app` serves stateless streamable HTTP with JSON responses and an allow-list of hosts (the public URL's host plus localhost). The SDK enables DNS-rebinding protection only for localhost and would otherwise reject or accept every host. Local detail, contract unchanged.
- The Dockerfile takes an optional `pip_cert` build secret for a TLS-inspecting proxy. Found while verifying the image behind this environment's proxy. Contract unchanged.

## Open questions and risks

- The SDK bearer path requires `AuthSettings` (issuer and resource URL) and publishes protected-resource metadata. Claude Code with a static `Authorization` header is fine. Will Cowork's custom connector send a static bearer key, or does it insist on OAuth? If it insists, v1 needs a minimal OAuth front or a key-in-URL fallback. Verify on the real tenant before rollout.
- Should `report` show weighted USD from `pricing.yaml` only, or also per-model prices? The sketch has one price pair, which matches the Hakka vibe cost model only roughly.
- The draft skill texts for the Hakka vibe techniques are written during implementation and shipped as `draft`.

## Packages (new project only)

Approved by the user on 2026-10-24.

| Package | For | Used in | Why not stdlib | Alternative considered |
|---|---|---|---|---|
| `mcp==2.3.0` | MCP server, streamable HTTP, bearer auth seam | `server.py` | The protocol and transport | Hand-rolled JSON-RPC over Starlette |
| `PyYAML==6.0.3` | Config, pricing and skill frontmatter | `catalog.py` | No YAML in stdlib | TOML via `tomllib` (stdlib), rejected: YAML reads better for nested estimates and is what the maintainer asked for |
| `SQLAlchemy==2.1.6` | Portable SQL (Core only, no ORM) | `ledger.py` | `sqlite3` ties SQL to one dialect | stdlib `sqlite3`, rejected: the Postgres move would rewrite the ledger |

`uvicorn`, `starlette` and `pydantic` arrive as dependencies of `mcp` and are used through it.

| Tooling | For |
|---|---|
| `pytest==9.1.1` | Tests, one per scenario |

## Tooling (new project only)

- Python 3.13.17 (`.venv/bin/python`).
- Test: `.venv/bin/python -m pytest -q`.
- Lint: none. Typecheck: none (build check is `compileall`).

## Next implementation step

`Catalog.load` with its validation scenarios, against a tmp-path catalog, because routing, usage and the tool enum all depend on it.
