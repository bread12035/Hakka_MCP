"""MCP adapter: the `route` and `get_usage_stats` tools over streamable HTTP.

No policy lives here. Tools parse arguments into domain types, call Catalog and Ledger,
and map the result to wire models. The principal always comes from the bearer key.
"""

from __future__ import annotations

from starlette.applications import Starlette

from hakka_mcp.catalog import Catalog
from hakka_mcp.ledger import Ledger


def build_app(catalog: Catalog, ledger: Ledger, *, public_url: str) -> Starlette:
    """Build the ASGI app. The `task_type` enum of `route` is built from `catalog.task_types()`."""
    raise NotImplementedError
