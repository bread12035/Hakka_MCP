"""Command line: check, serve, keys, report."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from hakka_mcp.catalog import Catalog, CatalogError, Provenance
from hakka_mcp.ledger import GroupBy, Ledger, StatsRow

DEFAULT_CATALOG = os.environ.get("HAKKA_CATALOG", "catalog")
DEFAULT_DB = os.environ.get("HAKKA_DB", "sqlite:///hakka.db")


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for `hakka-mcp`. Returns the process exit code."""
    args = _parser().parse_args(argv)
    return int(args.run(args) or 0)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hakka-mcp")
    commands = parser.add_subparsers(required=True)

    check = commands.add_parser("check", help="validate the catalog")
    _catalog_options(check)
    check.set_defaults(run=_check)

    serve = commands.add_parser("serve", help="run the MCP server")
    _catalog_options(serve)
    _db_option(serve)
    serve.add_argument("--public-url", default=os.environ.get("HAKKA_PUBLIC_URL", "http://127.0.0.1:8000"))
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.set_defaults(run=_serve)

    keys = commands.add_parser("keys", help="manage API keys").add_subparsers(required=True)
    issue = keys.add_parser("issue", help="issue a key; it is printed once and replaces the user's old key")
    issue.add_argument("user_id")
    issue.add_argument("--admin", action="store_true")
    _db_option(issue)
    issue.set_defaults(run=_issue)
    listing = keys.add_parser("list", help="list keys without their values")
    _db_option(listing)
    listing.set_defaults(run=_list)
    revoke = keys.add_parser("revoke", help="revoke a user's key")
    revoke.add_argument("user_id")
    _db_option(revoke)
    revoke.set_defaults(run=_revoke)

    report = commands.add_parser("report", help="usage and estimated savings")
    _db_option(report)
    report.add_argument("--group-by", type=GroupBy, choices=list(GroupBy), default=GroupBy.TOTAL)
    report.add_argument("--current-estimates", action="store_true", help="re-price with the catalog's estimates")
    _catalog_options(report)
    report.add_argument("--csv", action="store_true")
    report.set_defaults(run=_report)
    return parser


def _catalog_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--catalog", type=Path, default=Path(DEFAULT_CATALOG))
    parser.add_argument("--allow-drafts", action="store_true")


def _db_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLAlchemy URL")


def _load(root: Path, *, allow_drafts: bool) -> Catalog | None:
    try:
        return Catalog.load(root, allow_drafts=allow_drafts)
    except CatalogError as err:
        for problem in err.problems:
            print(problem, file=sys.stderr)
        return None


def _check(args: argparse.Namespace) -> int:
    catalog = _load(args.catalog, allow_drafts=args.allow_drafts)
    if catalog is None:
        return 1
    print(f"ok: task types {', '.join(catalog.task_types())}")
    return 0


def _serve(args: argparse.Namespace) -> int:
    import uvicorn

    from hakka_mcp.server import build_app

    catalog = _load(args.catalog, allow_drafts=args.allow_drafts)
    if catalog is None:
        return 1
    app = build_app(catalog, Ledger(args.db), public_url=args.public_url)
    uvicorn.run(app, host=args.host, port=args.port, proxy_headers=True)
    return 0


def _issue(args: argparse.Namespace) -> int:
    print(Ledger(args.db).issue_key(args.user_id, admin=args.admin))
    return 0


def _list(args: argparse.Namespace) -> int:
    for key in Ledger(args.db).list_keys():
        status = "revoked" if key.revoked else "active"
        role = "admin" if key.admin else "user"
        print(f"{key.user_id}\t{role}\t{status}\t{key.created_at:%Y-%m-%d}")
    return 0


def _revoke(args: argparse.Namespace) -> int:
    if not Ledger(args.db).revoke_key(args.user_id):
        print(f"no key for {args.user_id}", file=sys.stderr)
        return 1
    return 0


def _report(args: argparse.Namespace) -> int:
    current = None
    if args.current_estimates:
        catalog = _load(args.catalog, allow_drafts=args.allow_drafts)
        if catalog is None:
            return 1
        current = catalog.estimates()
    stats = Ledger(args.db).stats(args.group_by, current)
    rows = [stats.total] if args.group_by is GroupBy.TOTAL else [*stats.rows, stats.total]
    _write_report(rows, as_csv=args.csv)
    return 0


def _write_report(rows: Sequence[StatsRow], *, as_csv: bool) -> None:
    header = ["group", "users", "calls", "sessions"]
    header += [f"tokens_{p.value}" for p in Provenance] + [f"usd_{p.value}" for p in Provenance]
    lines = [
        [r.group, r.users, r.calls, r.sessions]
        + [r.saved_tokens[p] for p in Provenance]
        + [f"{r.saved_usd[p]:.2f}" for p in Provenance]
        for r in rows
    ]
    if as_csv:
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(lines)
        return
    widths = [max(len(str(c)) for c in col) for col in zip(header, *lines, strict=True)]
    for line in [header, *lines]:
        print("  ".join(str(c).ljust(w) for c, w in zip(line, widths, strict=True)))


if __name__ == "__main__":
    raise SystemExit(main())
