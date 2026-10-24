"""Scenarios of the access delta spec. One test per scenario."""

import sqlite3

import httpx2

from hakka_mcp.cli import main
from hakka_mcp.ledger import GroupBy

ROUTE = {"client": "code", "task_type": "code-feature", "session_id": "s1", "rationale": "why"}


def assert_unauthorized(url: str, key: str | None) -> None:
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    initialize = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}}
    response = httpx2.post(url, json=initialize, headers=headers)
    assert response.status_code == 401


def test_missing_api_key_rejected(mcp_session, ledger):
    """Missing API key rejected.

    Auth sits at the HTTP transport, so the first request of any session is refused before `route` is reachable.
    """
    assert_unauthorized(mcp_session(None).url, None)
    assert ledger.stats(GroupBy.TOTAL).total.calls == 0


def test_revoked_key_rejected(mcp_session, ledger):
    """Revoked key rejected."""
    key = ledger.issue_key("alice", admin=False)
    ledger.revoke_key("alice")
    assert_unauthorized(mcp_session(None).url, key)


def test_user_id_comes_from_the_key(mcp_session, stored_events):
    """User id comes from the key."""
    result = mcp_session("alice").call("route", **ROUTE, user_id="mallory")
    assert not result.is_error
    assert [e["user_id"] for e in stored_events()] == ["alice"]


def test_non_admin_asks_for_statistics(mcp_session):
    """Non-admin asks for statistics."""
    result = mcp_session("alice").call("get_usage_stats")
    assert result.is_error
    assert "forbidden" in result.content[0].text


def test_issue_a_key(mcp_session, stored_events, capsys, tmp_path):
    """Issue a key."""
    assert main(["keys", "issue", "bob", "--db", f"sqlite:///{tmp_path / 'hakka.db'}"]) == 0
    key = capsys.readouterr().out.strip()
    result = mcp_session(None, key=key).call("route", **ROUTE)
    assert not result.is_error
    assert [e["user_id"] for e in stored_events()] == ["bob"]


def test_stored_key_is_not_readable(ledger, capsys, tmp_path):
    """Stored key is not readable."""
    key = ledger.issue_key("alice", admin=True)
    assert main(["keys", "list", "--db", f"sqlite:///{tmp_path / 'hakka.db'}"]) == 0
    listing = capsys.readouterr().out
    assert listing.startswith("alice\tadmin\tactive\t")
    assert key not in listing
    with sqlite3.connect(tmp_path / "hakka.db") as conn:
        stored = [v for row in conn.execute("SELECT * FROM api_keys") for v in row]
    assert key not in stored


def test_revoke_unknown_user_fails(ledger, capsys, tmp_path):
    assert main(["keys", "revoke", "nobody", "--db", f"sqlite:///{tmp_path / 'hakka.db'}"]) == 1
    assert "nobody" in capsys.readouterr().err
