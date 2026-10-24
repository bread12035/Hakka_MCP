"""The ledger: the only owner of the database. Usage events, statistics and API keys.

SQL is SQLAlchemy Core so the URL decides the dialect (SQLite now, Postgres later).
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Final

import sqlalchemy as sa

from hakka_mcp.catalog import Client, Estimate, Provenance, Resolution

MAX_RATIONALE_CHARS: Final = 200
MAX_ID_CHARS: Final = 200


@dataclass(frozen=True)
class Principal:
    user_id: str
    admin: bool


@dataclass(frozen=True)
class KeyInfo:
    user_id: str
    admin: bool
    revoked: bool
    created_at: datetime


@dataclass(frozen=True)
class UsageEvent:
    user_id: str
    client: Client
    task_type: str
    session_id: str
    rationale: str
    resolution: Resolution
    at: datetime


class GroupBy(StrEnum):
    TOTAL = "total"
    CLIENT = "client"
    TASK_TYPE = "task_type"
    CONFIG = "config"


@dataclass(frozen=True)
class StatsRow:
    group: str
    users: int
    calls: int
    sessions: int
    saved_tokens: Mapping[Provenance, int]
    saved_usd: Mapping[Provenance, float]


@dataclass(frozen=True)
class Stats:
    rows: tuple[StatsRow, ...]
    total: StatsRow


_metadata = sa.MetaData()

_events = sa.Table(
    "usage_events",
    _metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id", sa.String(200), nullable=False, index=True),
    sa.Column("client", sa.String(20), nullable=False),
    sa.Column("task_type", sa.String(100), nullable=False),
    sa.Column("session_id", sa.String(MAX_ID_CHARS), nullable=False),
    sa.Column("config_id", sa.String(200), nullable=False),
    sa.Column("config_version", sa.Integer, nullable=False),
    sa.Column("fallback", sa.Boolean, nullable=False),
    sa.Column("rationale", sa.String(MAX_RATIONALE_CHARS), nullable=False),
    sa.Column("at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("est_percent", sa.Float, nullable=False),
    sa.Column("est_input_tokens", sa.Integer, nullable=False),
    sa.Column("est_output_tokens", sa.Integer, nullable=False),
    sa.Column("est_usd", sa.Float, nullable=False),
    sa.Column("est_provenance", sa.String(20), nullable=False),
)

_keys = sa.Table(
    "api_keys",
    _metadata,
    sa.Column("user_id", sa.String(200), primary_key=True),
    sa.Column("key_hash", sa.String(64), nullable=False, unique=True),
    sa.Column("admin", sa.Boolean, nullable=False),
    sa.Column("revoked", sa.Boolean, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)


def _hash(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class Ledger:
    def __init__(self, url: str) -> None:
        """Connect and create the tables if they do not exist."""
        self._engine = sa.create_engine(url)
        _metadata.create_all(self._engine)

    def record(self, event: UsageEvent) -> None:
        """Store the event with its estimate snapshot; truncate the rationale and the session id."""
        config = event.resolution.config
        estimate = config.estimate
        with self._engine.begin() as conn:
            conn.execute(
                _events.insert().values(
                    user_id=event.user_id,
                    client=event.client.value,
                    task_type=event.task_type,
                    session_id=event.session_id[:MAX_ID_CHARS],
                    config_id=config.id,
                    config_version=config.version,
                    fallback=event.resolution.fallback,
                    rationale=event.rationale[:MAX_RATIONALE_CHARS],
                    at=event.at,
                    est_percent=estimate.percent,
                    est_input_tokens=estimate.input_tokens,
                    est_output_tokens=estimate.output_tokens,
                    est_usd=estimate.usd,
                    est_provenance=estimate.provenance.value,
                )
            )

    def stats(self, group_by: GroupBy, current: Mapping[str, Estimate] | None = None) -> Stats:
        """Aggregate events. Savings count once per (user, session, config).

        With `current`, each event is priced by its config's current estimate instead of its snapshot.
        """
        with self._engine.connect() as conn:
            rows = conn.execute(sa.select(_events).order_by(_events.c.id)).all()
        column = _GROUP_COLUMNS.get(group_by)
        total = _Tally()
        groups: dict[str, _Tally] = {}
        for row in rows:
            total.add(row, current)
            if column is not None:
                groups.setdefault(row._mapping[column], _Tally()).add(row, current)
        total_row = total.row("total")
        if column is None:
            return Stats(rows=(total_row,), total=total_row)
        return Stats(rows=tuple(t.row(name) for name, t in sorted(groups.items())), total=total_row)

    def issue_key(self, user_id: str, *, admin: bool) -> str:
        """Create a key for the user and return it. Only its hash is stored.

        Issuing again for the same user replaces the old key.
        """
        raw_key = "hk_" + secrets.token_urlsafe(32)
        values = {
            "key_hash": _hash(raw_key),
            "admin": admin,
            "revoked": False,
            "created_at": datetime.now(UTC),
        }
        with self._engine.begin() as conn:
            conn.execute(_keys.delete().where(_keys.c.user_id == user_id))
            conn.execute(_keys.insert().values(user_id=user_id, **values))
        return raw_key

    def authenticate(self, raw_key: str) -> Principal | None:
        """Return the key's principal, or None for an unknown or revoked key."""
        with self._engine.connect() as conn:
            row = conn.execute(
                sa.select(_keys.c.user_id, _keys.c.admin).where(
                    _keys.c.key_hash == _hash(raw_key), _keys.c.revoked.is_(False)
                )
            ).first()
        return Principal(row.user_id, row.admin) if row else None

    def list_keys(self) -> tuple[KeyInfo, ...]:
        with self._engine.connect() as conn:
            rows = conn.execute(sa.select(_keys).order_by(_keys.c.user_id)).all()
        return tuple(KeyInfo(r.user_id, r.admin, r.revoked, r.created_at) for r in rows)

    def revoke_key(self, user_id: str) -> bool:
        """Revoke the user's key. Returns False when the user has no key."""
        with self._engine.begin() as conn:
            result = conn.execute(_keys.update().where(_keys.c.user_id == user_id).values(revoked=True))
        return result.rowcount > 0


_GROUP_COLUMNS: Final[Mapping[GroupBy, str]] = {
    GroupBy.CLIENT: "client",
    GroupBy.TASK_TYPE: "task_type",
    GroupBy.CONFIG: "config_id",
}


@dataclass
class _Tally:
    users: set[str] = field(default_factory=set)
    calls: int = 0
    sessions: set[tuple[str, str, str]] = field(default_factory=set)
    tokens: dict[Provenance, int] = field(default_factory=lambda: dict.fromkeys(Provenance, 0))
    usd: dict[Provenance, float] = field(default_factory=lambda: dict.fromkeys(Provenance, 0.0))

    def add(self, row: sa.Row[Any], current: Mapping[str, Estimate] | None) -> None:
        self.users.add(row.user_id)
        self.calls += 1
        key = (row.user_id, row.session_id, row.config_id)
        if key in self.sessions:
            return
        self.sessions.add(key)
        estimate = current.get(row.config_id) if current is not None else None
        if estimate is not None:
            provenance, tokens, usd = estimate.provenance, estimate.input_tokens + estimate.output_tokens, estimate.usd
        else:
            provenance = Provenance(row.est_provenance)
            tokens, usd = row.est_input_tokens + row.est_output_tokens, row.est_usd
        self.tokens[provenance] += tokens
        self.usd[provenance] += usd

    def row(self, group: str) -> StatsRow:
        return StatsRow(group, len(self.users), self.calls, len(self.sessions), dict(self.tokens), dict(self.usd))
