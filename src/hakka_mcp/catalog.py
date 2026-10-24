"""The catalog: techniques, skills and config sets, loaded from files and validated whole.

The catalog is immutable after `Catalog.load`. Every rule about what may be served lives here,
so callers trust the types and never re-check them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

MAX_SKILL_BYTES: Final = 4096


class Client(StrEnum):
    CODE = "code"
    COWORK = "cowork"


class Technique(StrEnum):
    PASS_BY_REFERENCE = "pass-by-reference"
    CAVEMAN = "caveman"
    PONYTAIL_RULES_ONLY = "ponytail-rules-only"
    CODE_GRAPH = "code-graph"
    SKILL_STATE = "skill-state"
    MODEL_ROUTING = "model-routing"


_BOTH: Final = frozenset({Client.CODE, Client.COWORK})
_CODE_ONLY: Final = frozenset({Client.CODE})

APPLICABILITY: Final[Mapping[Technique, frozenset[Client]]] = {
    Technique.PASS_BY_REFERENCE: _BOTH,
    Technique.CAVEMAN: _BOTH,
    Technique.PONYTAIL_RULES_ONLY: _CODE_ONLY,
    Technique.CODE_GRAPH: _CODE_ONLY,
    Technique.SKILL_STATE: _BOTH,
    Technique.MODEL_ROUTING: _BOTH,
}


class Provenance(StrEnum):
    MEASURED = "measured"
    VENDOR_CLAIM = "vendor-claim"
    ESTIMATE = "estimate"


@dataclass(frozen=True)
class Estimate:
    """Expected saving per counted session. `usd` is derived from `pricing.yaml` at load time."""

    percent: float
    input_tokens: int
    output_tokens: int
    usd: float
    provenance: Provenance
    source: str | None


@dataclass(frozen=True)
class Skill:
    id: str
    technique: Technique
    draft: bool
    text: str


@dataclass(frozen=True)
class Config:
    """One config set. `id` is `<client>/<task_type>`, derived from the file path."""

    id: str
    client: Client
    task_type: str
    version: int
    skills: tuple[Skill, ...]
    estimate: Estimate
    status_template: str | None


@dataclass(frozen=True)
class Resolution:
    config: Config
    fallback: bool


class CatalogError(Exception):
    """Raised once by `Catalog.load` with every problem found."""

    def __init__(self, problems: tuple[str, ...]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


class Catalog:
    """Resolves a client and task type to exactly one config."""

    def __init__(self, configs: Mapping[str, Config]) -> None:
        self._configs = dict(configs)

    @classmethod
    def load(cls, root: Path, *, allow_drafts: bool) -> Catalog:
        """Read `root` (pricing.yaml, skills/, configs/, templates/) and validate it whole.

        Raises CatalogError listing every problem: missing skill, draft skill without
        `allow_drafts`, technique outside APPLICABILITY, estimate without provenance,
        skill over MAX_SKILL_BYTES, skill-state without a template, a client without default.
        """
        raise NotImplementedError

    def resolve(self, client: Client, task_type: str) -> Resolution:
        """Return the config for the pair, or the client's `default` with `fallback=True`."""
        raise NotImplementedError

    def task_types(self) -> tuple[str, ...]:
        """Every configured task type, sorted. Feeds the `route` tool enum."""
        raise NotImplementedError

    def estimates(self) -> Mapping[str, Estimate]:
        """Current estimate per config id, for re-pricing old usage events."""
        raise NotImplementedError
