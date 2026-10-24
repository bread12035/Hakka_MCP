"""The ledger: the only owner of the database. Usage events, statistics and API keys.

SQL is SQLAlchemy Core so the URL decides the dialect (SQLite now, Postgres later).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Final

from hakka_mcp.catalog import Client, Estimate, Provenance, Resolution

MAX_RATIONALE_CHARS: Final = 200


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


class Ledger:
    def __init__(self, url: str) -> None:
        """Connect and create the tables if they do not exist."""
        raise NotImplementedError

    def record(self, event: UsageEvent) -> None:
        """Store the event with its estimate snapshot; truncate the rationale to MAX_RATIONALE_CHARS."""
        raise NotImplementedError

    def stats(self, group_by: GroupBy, current: Mapping[str, Estimate] | None = None) -> Stats:
        """Aggregate events. Savings count once per (user, session, config).

        With `current`, each event is priced by its config's current estimate instead of its snapshot.
        """
        raise NotImplementedError

    def issue_key(self, user_id: str, *, admin: bool) -> str:
        """Create a key for the user and return it. Only its hash is stored."""
        raise NotImplementedError

    def authenticate(self, raw_key: str) -> Principal | None:
        """Return the key's principal, or None for an unknown or revoked key."""
        raise NotImplementedError

    def list_keys(self) -> tuple[KeyInfo, ...]:
        raise NotImplementedError

    def revoke_key(self, user_id: str) -> None:
        raise NotImplementedError
