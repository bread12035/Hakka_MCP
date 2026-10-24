"""Scenarios of the routing delta spec, plus the catalog scenario that needs `route`."""

from hakka_mcp.ledger import GroupBy


def route(session, **overrides):
    arguments = {"client": "code", "task_type": "code-feature", "session_id": "s1", "rationale": "why"}
    return session.call("route", **(arguments | overrides))


def test_route_a_known_task(catalog_files, mcp_session):
    """Route a known task."""
    catalog_files.skill("code-graph", technique="code-graph", body="Query the graph first.")
    catalog_files.config("code", "code-feature", ["code-graph", "caveman"], version=4)
    result = route(mcp_session("alice"))
    assert not result.is_error
    body = result.structured_content
    assert (body["config_id"], body["config_version"], body["fallback"]) == ("code/code-feature", 4, False)
    assert [(s["id"], s["text"]) for s in body["skills"]] == [
        ("code-graph", "Query the graph first.\n"),
        ("caveman", "Be terse.\n"),
    ]


def test_unknown_client_rejected(mcp_session, ledger):
    """Unknown client rejected."""
    result = route(mcp_session("alice"), client="vscode")
    assert result.is_error
    message = result.content[0].text
    assert "'code'" in message and "'cowork'" in message
    assert ledger.stats(GroupBy.TOTAL).total.calls == 0


def test_unconfigured_task_type_falls_back(mcp_session, stored_events):
    """Unconfigured task type falls back."""
    body = route(mcp_session("alice"), client="cowork", task_type="code-feature").structured_content
    assert body["config_id"] == "cowork/default"
    assert body["fallback"] is True
    [stored] = stored_events()
    assert (stored["config_id"], stored["task_type"], stored["fallback"]) == ("cowork/default", "code-feature", 1)


def test_default_status_template_returned(catalog_files, mcp_session):
    """Default status template returned."""
    catalog_files.skill("skill-state", technique="skill-state")
    catalog_files.config("code", "code-feature", ["skill-state"])
    catalog_files.status_template("code-feature", {"goal": "", "done": []})
    body = route(mcp_session("alice")).structured_content
    assert body["status_template"] == {"goal": "", "done": []}


def test_caller_template_overrides_default(catalog_files, mcp_session):
    """Caller template overrides default."""
    catalog_files.skill("skill-state", technique="skill-state")
    catalog_files.config("code", "code-feature", ["skill-state"])
    catalog_files.status_template("code-feature", {"goal": ""})
    mine = {"ticket": "", "files": []}
    body = route(mcp_session("alice"), status_template=mine).structured_content
    assert body["status_template"] == mine


def test_draft_skill_served_when_enabled(catalog_files, ledger, serve):
    """Draft skill served when enabled."""
    from conftest import McpSession

    catalog_files.skill("new-rules", technique="caveman", status="draft", body="Draft rules.")
    catalog_files.config("code", "code-feature", ["new-rules"])
    session = McpSession(serve(allow_drafts=True), ledger.issue_key("alice", admin=False))
    skills = route(session).structured_content["skills"]
    assert skills == [{"id": "new-rules", "technique": "caveman", "draft": True, "text": "Draft rules.\n"}]
