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
    """Missing API key rejected."""
    assert_unauthorized(mcp_session(None).url, None)
    assert ledger.stats(GroupBy.TOTAL).total.calls == 0


def test_revoked_key_rejected(mcp_session, ledger):
    """Revoked key rejected."""
    key = ledger.issue_key("alice", admin=False)
    ledger.revoke_key("alice")
    assert_unauthorized(mcp_session(None).url, key)


def test_user_id_comes_from_the_key(mcp_session, ledger):
    """User id comes from the key."""
    mcp_session("alice").call("route", **ROUTE, user_id="mallory")
    keys = {k.user_id for k in ledger.list_keys()}
    assert keys == {"alice"}
    rows = ledger.stats(GroupBy.TOTAL).total
    assert rows.users == 1
    assert "mallory" not in repr(ledger.stats(GroupBy.CONFIG))


def test_non_admin_asks_for_statistics(mcp_session):
    """Non-admin asks for statistics."""
    result = mcp_session("alice").call("get_usage_stats")
    assert result.is_error
    assert "forbidden" in result.content[0].text


def test_issue_a_key(mcp_session, ledger, capsys, tmp_path):
    """Issue a key."""
    assert main(["keys", "issue", "bob", "--db", f"sqlite:///{tmp_path / 'hakka.db'}"]) == 0
    key = capsys.readouterr().out.strip()
    result = mcp_session(None, key=key).call("route", **ROUTE)
    assert not result.is_error
    total = ledger.stats(GroupBy.TOTAL).total
    assert total.users == 1
    assert [k.user_id for k in ledger.list_keys()] == ["bob"]


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
