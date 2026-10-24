# Hakka MCP

A remote MCP server that gives Claude Code and Cowork the token-saving skill set for a task, and counts the estimated savings.

The model calls `route(client, task_type, session_id, rationale)` once at the start of a task. The server returns the full text of the skills for that client and task type, and records one usage event. An admin can see the totals with `get_usage_stats` or the `report` command.

## Run the server

```text
python -m pip install -r requirements-dev.txt -e .
hakka-mcp check --catalog catalog --allow-drafts
hakka-mcp serve --catalog catalog --db sqlite:///hakka.db --public-url https://hakka.example.com --allow-drafts
```

Remove `--allow-drafts` when every skill in `catalog/skills/` has `status: approved`.

Docker:

```text
docker build -t hakka-mcp .
# behind a TLS-inspecting proxy, add: --secret id=pip_cert,src=<ca-bundle.pem>
docker run -p 8000:8000 -v hakka-data:/data -e HAKKA_PUBLIC_URL=https://hakka.example.com hakka-mcp \
  hakka-mcp serve --host 0.0.0.0 --allow-drafts
```

TLS ends at the reverse proxy in front of the container. Set `HAKKA_PUBLIC_URL` to the public HTTPS address.

## Give a user access

```text
hakka-mcp keys issue alice            # prints the key once
hakka-mcp keys issue maintainer --admin
hakka-mcp keys list
hakka-mcp keys revoke alice
```

The user adds the server to Claude Code:

```text
claude mcp add --transport http hakka https://hakka.example.com/mcp --header "Authorization: Bearer <key>"
```

## See the savings

```text
hakka-mcp report --group-by task_type
hakka-mcp report --group-by config --current-estimates --allow-drafts --csv > savings.csv
```

Each event keeps the estimate that was current when it was recorded. `--current-estimates` re-prices the old events with the catalog's current numbers and changes nothing in the database.

## Edit the catalog

| Path | Holds |
|---|---|
| `catalog/configs/<client>/<task-type>.yaml` | One config set: skills, version, expected saving with provenance |
| `catalog/skills/<id>/SKILL.md` | A skill. Frontmatter: `technique`, `status`, `source` |
| `catalog/templates/status/<task-type>.json` | Default `status.json` for configs with skill-state |
| `catalog/pricing.yaml` | USD per million tokens for the savings estimate. The shipped values are a placeholder list price; set the company rate |

A new task type is one new YAML file. Run `hakka-mcp check` before you deploy; it lists every problem.

## Tests

```text
.venv/bin/python -m pytest -q
```
