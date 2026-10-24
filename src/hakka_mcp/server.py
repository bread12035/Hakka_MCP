"""MCP adapter: the `route` and `get_usage_stats` tools over streamable HTTP.

No policy lives here. Tools parse arguments into domain types, call Catalog and Ledger,
and map the result to wire models. The principal always comes from the bearer key.
"""

# No `from __future__ import annotations`: the tool signatures use a TaskType enum built at
# runtime, and the SDK must see the real objects to build the input schema.

from datetime import UTC, datetime
from urllib.parse import urlsplit
from enum import StrEnum
from typing import Any

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette

from hakka_mcp.catalog import Catalog, Client
from hakka_mcp.ledger import GroupBy, Ledger, Principal, StatsRow, UsageEvent

ADMIN_SCOPE = "admin"

INSTRUCTIONS = """\
Hakka MCP serves the token-saving practices for this company.
At the start of a task, call `route` once with the client you run in, the task type that fits
the user's request best, a stable session id for this conversation, and a one-line rationale.
Do not put names, secrets or the user's prompt text in the rationale.
Then follow every skill text in the result for the rest of the task.
"""


class SkillText(BaseModel):
    id: str
    technique: str
    draft: bool
    text: str


class RouteResult(BaseModel):
    config_id: str
    config_version: int
    fallback: bool
    skills: list[SkillText]
    status_template: dict[str, Any] | None


class StatsRowOut(BaseModel):
    group: str
    users: int
    calls: int
    sessions: int
    saved_tokens: dict[str, int]
    saved_usd: dict[str, float]


class StatsResult(BaseModel):
    rows: list[StatsRowOut]
    total: StatsRowOut


class _KeyVerifier:
    def __init__(self, ledger: Ledger) -> None:
        self._ledger = ledger

    async def verify_token(self, token: str) -> AccessToken | None:
        principal = self._ledger.authenticate(token)
        if principal is None:
            return None
        scopes = [ADMIN_SCOPE] if principal.admin else []
        return AccessToken(token=token, client_id=principal.user_id, scopes=scopes)


def _principal() -> Principal:
    token = get_access_token()
    if token is None:
        raise ToolError("unauthorized")
    return Principal(token.client_id, ADMIN_SCOPE in token.scopes)


def _stats_row(row: StatsRow) -> StatsRowOut:
    return StatsRowOut(
        group=row.group,
        users=row.users,
        calls=row.calls,
        sessions=row.sessions,
        saved_tokens={p.value: n for p, n in row.saved_tokens.items()},
        saved_usd={p.value: round(n, 4) for p, n in row.saved_usd.items()},
    )


def build_app(catalog: Catalog, ledger: Ledger, *, public_url: str) -> Starlette:
    """Build the ASGI app. The `task_type` enum of `route` is built from `catalog.task_types()`."""
    public_url = public_url.rstrip("/")
    server: MCPServer[Any] = MCPServer(
        name="hakka-mcp",
        instructions=INSTRUCTIONS,
        token_verifier=_KeyVerifier(ledger),
        auth=AuthSettings(
            issuer_url=public_url,
            resource_server_url=f"{public_url}/mcp",
            validate_token_resource=False,
        ),
    )
    TaskType = StrEnum("TaskType", {t: t for t in catalog.task_types()})

    @server.tool()
    def route(
        client: Client,
        task_type: TaskType,  # type: ignore[valid-type]
        session_id: str,
        rationale: str,
        status_template: dict[str, Any] | None = None,
    ) -> RouteResult:
        """Return the token-saving skill set for this client and task type. Follow every skill text."""
        principal = _principal()
        resolution = catalog.resolve(client, task_type.value)
        ledger.record(
            UsageEvent(
                user_id=principal.user_id,
                client=client,
                task_type=task_type.value,
                session_id=session_id,
                rationale=rationale,
                resolution=resolution,
                at=datetime.now(UTC),
            )
        )
        config = resolution.config
        template = None
        if config.status_template is not None:
            template = dict(status_template if status_template is not None else config.status_template)
        return RouteResult(
            config_id=config.id,
            config_version=config.version,
            fallback=resolution.fallback,
            skills=[SkillText(id=s.id, technique=s.technique.value, draft=s.draft, text=s.text) for s in config.skills],
            status_template=template,
        )

    @server.tool()
    def get_usage_stats(group_by: GroupBy = GroupBy.TOTAL, current_estimates: bool = False) -> StatsResult:
        """Usage and estimated savings. Admin keys only."""
        if not _principal().admin:
            raise ToolError("forbidden: get_usage_stats needs an admin key")
        stats = ledger.stats(group_by, catalog.estimates() if current_estimates else None)
        return StatsResult(rows=[_stats_row(r) for r in stats.rows], total=_stats_row(stats.total))

    public_host = urlsplit(public_url).netloc
    security = TransportSecuritySettings(
        allowed_hosts=[public_host, "127.0.0.1:*", "localhost:*"],
        allowed_origins=[public_url, "http://127.0.0.1:*", "http://localhost:*"],
    )
    return server.streamable_http_app(stateless_http=True, json_response=True, transport_security=security)
