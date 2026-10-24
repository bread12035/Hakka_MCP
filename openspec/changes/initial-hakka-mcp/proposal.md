# Proposal: Hakka MCP — a token-saving skill router

## Intent
The Hakka vibe experiments show which harness techniques cut token cost, but the results only help people who find and install the right skills by hand. Hakka MCP is one internal MCP server that, given the client (Claude Code or Cowork) and the task type, pushes the best-practice skill set for that situation. Central delivery lets the maintainer update the skills in one place and count how many people use them and how many tokens they are estimated to save.

## Scope
In scope:
- A catalog of techniques (pass-by-reference, caveman, ponytail-rules-only, code-graph, skill-state, model-routing) with a client applicability matrix (catalog: Technique applicability).
- Config sets in versioned YAML: client × task type → skill set + expected saving (catalog: Config sets, Config validation, Number provenance).
- Six initial task types: `cowork-poc`, `cowork-daily-data`, `cowork-doc`, `code-feature`, `code-bugfix`, `code-explore`, plus a `default` per client (catalog: Initial task types).
- A `route` MCP tool that returns the full skill texts for a client and task type, with fallback to the client default (routing: Route request, Fallback config, Skill-state template).
- Usage events in SQLite with the estimate snapshotted at call time, deduplicated per session (usage: Record usage event, Session deduplication, Estimate snapshot, Privacy of rationale).
- Statistics: a CLI report and an admin-only `get_usage_stats` MCP tool (usage: Usage statistics).
- Per-user API keys mapped to `user_id`, an admin flag, and a key-management CLI (access: API key authentication, Admin authorization, Key management).

Out of scope:
- SSO, OAuth and fine-grained authorization. The key-to-user layer is the seam they replace later.
- Postgres. SQL stays portable so the move is a driver change, not a rewrite.
- A web dashboard.
- Ingesting real token usage from Claude Code or Cowork.
- Programmatic tool calling and other future techniques.
- Server-side LLM classification of the user's request.
- Ponytail's lifecycle hooks. Only its SKILL.md rules are delivered.

Constraints:
- Python, with the official MCP Python SDK.
- Remote MCP over streamable HTTP, reachable from the internet over HTTPS so Cowork custom connectors can reach it. TLS terminates at the company reverse proxy.
- Shipped as a Docker image, one process, the SQLite file on a volume.
- Third-party skill copies keep their source, version and license notice.
- Every expected-saving number carries a provenance: `measured`, `vendor-claim` or `estimate`. The Hakka vibe report has no run data yet, so v1 numbers are vendor claims or estimates.

## Approach
Skills and configs live as files in the repo and load at startup; invalid configs stop the server. The model classifies the task itself and calls `route(client, task_type, session_id, rationale)`; the server only looks up the config, returns the skill texts and writes a usage event. Each event stores the config version, percentage and token estimate as they were at call time, so later recalibration never rewrites history. The design is in `architecture.md` once written.

## Open questions
- Whether a public, non-admin tool showing company-wide totals (no per-user detail) helps adoption. (owner: user)
- How Cowork authenticates to a custom connector with a per-user API key in your tenant; verify on the real deployment. (owner: user)
- Whether Cowork lets a session choose the model, which limits model-routing there. (owner: user)
- Initial expected-saving numbers per config until the Hakka vibe runs produce data. (owner: user)
- Draft skill texts for the Hakka vibe techniques need the maintainer's review before they are marked approved. (owner: user)
