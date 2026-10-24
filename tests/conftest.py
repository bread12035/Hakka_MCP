from __future__ import annotations

import asyncio
import json
import socket
import sqlite3
import threading
import time
from collections.abc import Sequence
from pathlib import Path

import httpx2
import pytest
import uvicorn
import yaml
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client


class CatalogFiles:
    """Writes a catalog folder for a test. Starts valid: one approved skill and a default per client."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True)
        (root / "pricing.yaml").write_text(yaml.safe_dump({"usd_per_mtok": {"input": 3.0, "output": 15.0}}))
        self.skill("caveman", technique="caveman")
        self.config("code", "default", ["caveman"])
        self.config("cowork", "default", ["caveman"])

    def skill(self, skill_id: str, *, technique: str, status: str = "approved", body: str = "Be terse.") -> None:
        folder = self.root / "skills" / skill_id
        folder.mkdir(parents=True, exist_ok=True)
        meta = yaml.safe_dump({"technique": technique, "status": status})
        (folder / "SKILL.md").write_text(f"---\n{meta}---\n{body}\n")

    def config(
        self,
        client: str,
        task_type: str,
        skills: Sequence[str],
        *,
        version: int = 1,
        input_tokens: int = 1000,
        output_tokens: int = 200,
        provenance: str | None = "estimate",
        suffix: str = ".yaml",
    ) -> Path:
        saving: dict[str, object] = {"percent": 10, "tokens": {"input": input_tokens, "output": output_tokens}}
        if provenance is not None:
            saving["provenance"] = provenance
        path = self.root / "configs" / client / f"{task_type}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump({"version": version, "skills": list(skills), "expected_saving": saving}))
        return path

    def status_template(self, task_type: str, template: dict[str, object]) -> None:
        folder = self.root / "templates" / "status"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{task_type}.json").write_text(json.dumps(template))


@pytest.fixture
def catalog_files(tmp_path: Path) -> CatalogFiles:
    return CatalogFiles(tmp_path / "catalog")


@pytest.fixture
def ledger(tmp_path: Path):
    from hakka_mcp.ledger import Ledger

    return Ledger(f"sqlite:///{tmp_path / 'hakka.db'}")


class McpSession:
    """Calls the running server over streamable HTTP with one API key."""

    def __init__(self, url: str, key: str | None) -> None:
        self.url = url
        self.key = key

    def call(self, tool: str, **arguments: object):
        return asyncio.run(self._call(tool, arguments))

    async def _call(self, tool: str, arguments: dict[str, object]):
        headers = {"Authorization": f"Bearer {self.key}"} if self.key else {}
        async with httpx2.AsyncClient(headers=headers, timeout=10) as http:
            async with streamable_http_client(self.url, http_client=http) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return await session.call_tool(tool, arguments)


@pytest.fixture
def serve(catalog_files: CatalogFiles, ledger):
    """Start the server lazily, so a test can shape the catalog first. Returns the MCP URL."""
    from hakka_mcp.catalog import Catalog
    from hakka_mcp.server import build_app

    servers: list[uvicorn.Server] = []

    def start(*, allow_drafts: bool = False) -> str:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        catalog = Catalog.load(catalog_files.root, allow_drafts=allow_drafts)
        app = build_app(catalog, ledger, public_url=f"http://127.0.0.1:{port}")
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
        threading.Thread(target=server.run, daemon=True).start()
        deadline = time.monotonic() + 10
        while not server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("server did not start")
            time.sleep(0.02)
        servers.append(server)
        return f"http://127.0.0.1:{port}/mcp"

    yield start
    for server in servers:
        server.should_exit = True


@pytest.fixture
def mcp_session(catalog_files: CatalogFiles, ledger, serve):
    """`mcp_session(user, admin=False)` issues a key and returns a session on the running server."""
    catalog_files.config("code", "code-feature", ["caveman"])
    urls: list[str] = []

    def open_session(user_id: str | None, *, admin: bool = False, key: str | None = None) -> McpSession:
        if not urls:
            urls.append(serve())
        if user_id is not None and key is None:
            key = ledger.issue_key(user_id, admin=admin)
        return McpSession(urls[0], key)

    return open_session


@pytest.fixture
def stored_events(tmp_path: Path):
    """The usage events as rows, for scenarios whose THEN is about what was stored."""

    def read() -> list[dict[str, object]]:
        with sqlite3.connect(tmp_path / "hakka.db") as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute("SELECT * FROM usage_events ORDER BY id")]

    return read
