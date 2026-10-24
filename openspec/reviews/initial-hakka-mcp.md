# Review report: initial-hakka-mcp

Proposal: openspec/changes/initial-hakka-mcp/proposal.md
Architecture: openspec/changes/initial-hakka-mcp/architecture.md

## Round 1 (2026-10-24)

### Scope
- Base: dev
- Branch: feat/initial-hakka-mcp   Changed code files: 32
- Starting checks: tests pass (32 passed), lint none, typecheck none (command: .venv/bin/python -m pytest -q)

### Summary
| Step | Findings | Fixed | Left open | Notes |
|---|---|---|---|---|
| /code-review | 24 | 17 | 7 (2 judged wrong, 3 decisions kept, 2 open) | built-in (Standards and Spec axes) |
| /security-review | 4 | 2 | 2 | fallback checklist: the built-in needs the session's working directory to be the repo, and this session's is `/home/user` | |

### 1. /code-review (correctness)
Ran as two parallel sub-agents (Standards and Spec axes) over `git diff dev...HEAD`. Every finding was in the branch diff. Two Standards claims were checked by running them.

| # | Severity | Location | Problem | Result | Commit |
|---|---|---|---|---|---|
| S1 | high | `src/hakka_mcp/catalog.py:212` | Malformed skill frontmatter raised an uncaught `YAMLError`, so `check` and `serve` crashed instead of listing problems | fixed (reproduced first) | caca5e1 |
| P1 | high | `tests/test_access.py` | "User id comes from the key" test could pass with the wrong user stored | fixed: asserts the stored `user_id` | caca5e1 |
| S2 | medium | `src/hakka_mcp/ledger.py:80` | `session_id` unbounded; fails on Postgres | fixed: capped at 200 | caca5e1 |
| S3 | medium | `src/hakka_mcp/server.py:135` | Template override rule lived in the adapter | fixed: `Config.status_template(override)` | caca5e1 |
| P2 | medium | `tests/test_access.py` | "Issue a key" did not prove the user is `bob` | fixed | caca5e1 |
| S9 | medium | `src/hakka_mcp/ledger.py:144` | Stats load every event into Python | left open: accepted v1 tradeoff, move to SQL aggregation with Postgres | |
| S10 | medium | `src/hakka_mcp/catalog.py:251` | Both `default` configs would share `default.json` | judged wrong: the spec keys templates by task type | |
| S11 | medium | `src/hakka_mcp/catalog.py:207` | CRLF frontmatter reported as missing | judged wrong: `read_text` normalizes newlines; a CRLF skill loads (ran it) | |
| S4 | low | `src/hakka_mcp/catalog.py:84` | Mutable dict inside frozen `Config` | fixed: stored as JSON text, fresh copy per call | caca5e1 |
| S5 | low | `src/hakka_mcp/catalog.py:246` | `version: true` and negative tokens accepted | fixed | caca5e1 |
| S6 | low | `src/hakka_mcp/cli.py:118` | `keys revoke` of an unknown user exited 0 | fixed: exits 1 | caca5e1 |
| S7 | low | `src/hakka_mcp/server.py:71` | Blocking DB call in async `verify_token` | fixed: `anyio.to_thread` | caca5e1 |
| S8 | low | `src/hakka_mcp/ledger.py`, `cli.py` | Repeated `GroupBy.TOTAL` switches, duplicated `--catalog`, unclear `counted` | fixed | caca5e1 |
| P3 | low | `tests/test_routing.py` | Unknown-client message check too loose | fixed | caca5e1 |
| P4 | low | `tests/test_routing.py` | Stored `fallback` flag not checked | fixed | caca5e1 |
| P5 | low | tests | No test for an admin reading statistics | fixed: `test_admin_reads_statistics` | caca5e1 |
| P6 | low | `tests/test_access.py` | Missing-key test sends `initialize`, not `route` | fixed: docstring states auth is at the transport | caca5e1 |
| P7 | low | `src/hakka_mcp/catalog.py:250` | Skill-state without a template file fails to load; not in spec | decision kept, recorded in architecture.md | caca5e1 |
| P8 | low | `src/hakka_mcp/ledger.py:168` | `keys issue` replaces the old key | decision kept, stated in CLI help | caca5e1 |
| P9 | low | `src/hakka_mcp/ledger.py:148` | Group rows can sum above the total | decision kept, recorded in architecture.md | |
| P10 | low | various | `check` command not in spec; shipped-catalog test checks the union of task types; "restart" test only reloads the catalog | left open: harmless | |

### 2. /security-review
Fallback checklist over `git diff dev...HEAD`, not the built-in review. The built-in would also have seen the skill pack and env files already on `dev` (119 files against `origin/main`, 32 against `dev`).

| # | Severity | Location | Problem | Result | Commit |
|---|---|---|---|---|---|
| X1 | medium | `src/hakka_mcp/server.py` (`route`, `get_usage_stats`) | No rate limit; a key holder can grow the database, and statistics read every event | partly fixed: README requires a per-key limit at the reverse proxy; statistics cost left open (see S9) | a154408 |
| X2 | low | `Dockerfile` | Container ran as root | fixed: `USER hakka` (uid 10001), `/data` owned by it; verified the server writes `hakka.db` | a154408 |
| X3 | low | `Dockerfile`, `requirements.txt` | Base image not pinned by digest; packages pinned by version, not hash | left open: pin a digest and use `--require-hashes` before production | |
| X4 | low | `src/hakka_mcp/cli.py:105`, README | Keys printed to stdout and stored in plain text in Claude Code config | fixed: README states how to hand over, clear and revoke keys | a154408 |

Checked with no finding: SQL goes through SQLAlchemy parameters; YAML uses `safe_load`; no pickle, eval or subprocess; catalog paths come from the maintainer's folder; keys are 256-bit random and stored as SHA-256; keys never appear in logs or responses; admin check on `get_usage_stats`; rationale truncated and no prompt text stored; `proxy_headers` trusts only `127.0.0.1` by default.

### Final checks
- tests pass (37 passed), lint none, typecheck none
- `docker build` and a container run verified after the fixes

### Open items
| # | Item | Why it was not fixed | Who decided |
|---|---|---|---|
| 1 | S9 / X1: statistics read every event into Python | Fine at internal v1 volume; move to SQL aggregation with the Postgres switch | user (accepted recommendation) |
| 2 | X3: image digest and hash-pinned requirements | Production hardening, outside v1 | user (accepted recommendation) |
| 3 | P10: weaker tests for shipped-catalog client mapping and the restart wording | Harmless; behavior is covered elsewhere | user (accepted recommendation) |
| 4 | Cowork custom connector with a static bearer key | Needs the real tenant to verify | user (open question in proposal) |
