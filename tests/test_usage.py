"""Scenarios of the usage delta spec. One test per scenario."""

import csv
import io
from datetime import UTC, datetime

from hakka_mcp.catalog import Catalog, Client, Provenance
from hakka_mcp.cli import main
from hakka_mcp.ledger import GroupBy, UsageEvent


def event(resolution, *, user="alice", session="s1", task_type=None, rationale="why"):
    config = resolution.config
    return UsageEvent(
        user_id=user,
        client=config.client,
        task_type=task_type or config.task_type,
        session_id=session,
        rationale=rationale,
        resolution=resolution,
        at=datetime.now(UTC),
    )


def load(catalog_files):
    return Catalog.load(catalog_files.root, allow_drafts=False)


def test_successful_route_writes_an_event(mcp_session, ledger):
    """Successful route writes an event."""
    session = mcp_session("alice")
    session.call("route", client="code", task_type="code-feature", session_id="s1", rationale="new endpoint")
    rows = ledger.stats(GroupBy.CONFIG).rows
    assert [(r.group, r.users, r.calls) for r in rows] == [("code/code-feature", 1, 1)]


def test_repeated_route_in_one_session_counted_once(catalog_files, ledger):
    """Repeated route in one session counted once."""
    catalog_files.config("code", "code-feature", ["caveman"], input_tokens=1000, output_tokens=0)
    resolution = load(catalog_files).resolve(Client.CODE, "code-feature")
    ledger.record(event(resolution))
    ledger.record(event(resolution))
    total = ledger.stats(GroupBy.TOTAL).total
    assert (total.calls, total.sessions) == (2, 1)
    assert total.saved_tokens[Provenance.ESTIMATE] == 1000


def test_different_config_in_the_same_session_counted_separately(catalog_files, ledger):
    """Different config in the same session counted separately."""
    catalog_files.config("code", "code-feature", ["caveman"])
    catalog_files.config("code", "code-bugfix", ["caveman"])
    catalog = load(catalog_files)
    ledger.record(event(catalog.resolve(Client.CODE, "code-feature")))
    ledger.record(event(catalog.resolve(Client.CODE, "code-bugfix")))
    rows = {r.group: r.sessions for r in ledger.stats(GroupBy.CONFIG).rows}
    assert rows == {"code/code-feature": 1, "code/code-bugfix": 1}


def test_recalibration_keeps_history(catalog_files, ledger):
    """Recalibration keeps history."""
    catalog_files.config("code", "code-feature", ["caveman"], input_tokens=1000, output_tokens=0)
    ledger.record(event(load(catalog_files).resolve(Client.CODE, "code-feature")))
    catalog_files.config("code", "code-feature", ["caveman"], version=2, input_tokens=500, output_tokens=0)
    load(catalog_files)
    assert ledger.stats(GroupBy.TOTAL).total.saved_tokens[Provenance.ESTIMATE] == 1000


def test_recompute_with_current_estimates(catalog_files, ledger):
    """Recompute with current estimates."""
    catalog_files.config("code", "code-feature", ["caveman"], input_tokens=1000, output_tokens=0)
    ledger.record(event(load(catalog_files).resolve(Client.CODE, "code-feature")))
    catalog_files.config("code", "code-feature", ["caveman"], version=2, input_tokens=500, output_tokens=0)
    current = load(catalog_files).estimates()
    assert ledger.stats(GroupBy.TOTAL, current).total.saved_tokens[Provenance.ESTIMATE] == 500


def test_long_rationale_truncated(mcp_session, stored_events):
    """Long rationale truncated."""
    mcp_session("alice").call(
        "route", client="code", task_type="code-feature", session_id="s1", rationale="r" * 500
    )
    assert [e["rationale"] for e in stored_events()] == ["r" * 200]


def test_long_session_id_truncated(mcp_session, stored_events):
    mcp_session("alice").call(
        "route", client="code", task_type="code-feature", session_id="s" * 500, rationale="why"
    )
    assert [e["session_id"] for e in stored_events()] == ["s" * 200]


def test_admin_reads_statistics(mcp_session):
    mcp_session("alice").call("route", client="code", task_type="code-feature", session_id="s1", rationale="why")
    result = mcp_session("boss", admin=True).call("get_usage_stats", group_by="client")
    assert not result.is_error
    body = result.structured_content
    assert [(r["group"], r["users"], r["calls"]) for r in body["rows"]] == [("code", 1, 1)]
    assert body["total"]["saved_tokens"]["estimate"] == 1200


def test_statistics_grouped_by_task_type(catalog_files, ledger):
    """Statistics grouped by task type."""
    catalog_files.config("code", "code-feature", ["caveman"], input_tokens=100, output_tokens=0)
    catalog_files.config("code", "code-bugfix", ["caveman"], input_tokens=10, output_tokens=0)
    catalog = load(catalog_files)
    ledger.record(event(catalog.resolve(Client.CODE, "code-feature"), user="alice"))
    ledger.record(event(catalog.resolve(Client.CODE, "code-feature"), user="bob"))
    ledger.record(event(catalog.resolve(Client.CODE, "code-bugfix"), user="bob"))
    rows = {r.group: (r.users, r.calls, r.saved_tokens[Provenance.ESTIMATE]) for r in ledger.stats(GroupBy.TASK_TYPE).rows}
    assert rows == {"code-feature": (2, 2, 200), "code-bugfix": (1, 1, 10)}


def test_savings_split_by_provenance(catalog_files, ledger):
    """Savings split by provenance."""
    catalog_files.config("code", "code-feature", ["caveman"], input_tokens=100, output_tokens=0, provenance="measured")
    catalog_files.config("code", "code-bugfix", ["caveman"], input_tokens=7, output_tokens=0, provenance="vendor-claim")
    catalog = load(catalog_files)
    ledger.record(event(catalog.resolve(Client.CODE, "code-feature")))
    ledger.record(event(catalog.resolve(Client.CODE, "code-bugfix")))
    saved = ledger.stats(GroupBy.TOTAL).total.saved_tokens
    assert saved[Provenance.MEASURED] == 100
    assert saved[Provenance.VENDOR_CLAIM] == 7


def test_cli_report_as_csv(catalog_files, ledger, capsys, tmp_path):
    """CLI report as CSV."""
    catalog_files.config("code", "code-feature", ["caveman"], input_tokens=100, output_tokens=0)
    catalog_files.config("code", "code-bugfix", ["caveman"], input_tokens=10, output_tokens=0)
    catalog = load(catalog_files)
    ledger.record(event(catalog.resolve(Client.CODE, "code-feature")))
    ledger.record(event(catalog.resolve(Client.CODE, "code-bugfix")))
    db = f"sqlite:///{tmp_path / 'hakka.db'}"
    assert main(["report", "--db", db, "--group-by", "task_type", "--csv"]) == 0
    rows = list(csv.DictReader(io.StringIO(capsys.readouterr().out)))
    assert [(r["group"], r["calls"], r["tokens_estimate"]) for r in rows] == [
        ("code-bugfix", "1", "10"),
        ("code-feature", "1", "100"),
        ("total", "2", "110"),
    ]


def test_empty_usage_store(ledger):
    """Empty usage store."""
    total = ledger.stats(GroupBy.TOTAL).total
    assert (total.users, total.calls, total.sessions) == (0, 0, 0)
    assert sum(total.saved_tokens.values()) == 0
    assert sum(total.saved_usd.values()) == 0
