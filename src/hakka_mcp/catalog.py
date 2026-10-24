"""The catalog: techniques, skills and config sets, loaded from files and validated whole.

The catalog is immutable after `Catalog.load`. Every rule about what may be served lives here,
so callers trust the types and never re-check them.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Final

import yaml

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
    status_template: Mapping[str, Any] | None


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
        problems: list[str] = []
        prices = _load_pricing(root / "pricing.yaml", problems)
        skills = _load_skills(root / "skills", problems)
        configs: dict[str, Config] = {}
        seen: dict[str, Path] = {}
        for path in sorted((root / "configs").glob("*/*.y*ml")):
            config_id = f"{path.parent.name}/{path.stem}"
            if config_id in seen:
                problems.append(f"{config_id}: duplicate config files {seen[config_id]} and {path}")
                continue
            seen[config_id] = path
            config = _load_config(path, config_id, skills, prices, root, allow_drafts, problems)
            if config is not None:
                configs[config_id] = config
        for client in Client:
            if f"{client}/default" not in seen:
                problems.append(f"{client}: no default config")
        if problems:
            raise CatalogError(tuple(problems))
        return cls(configs)

    def resolve(self, client: Client, task_type: str) -> Resolution:
        """Return the config for the pair, or the client's `default` with `fallback=True`."""
        config = self._configs.get(f"{client}/{task_type}")
        if config is not None:
            return Resolution(config, fallback=False)
        return Resolution(self._configs[f"{client}/default"], fallback=True)

    def task_types(self) -> tuple[str, ...]:
        """Every configured task type, sorted. Feeds the `route` tool enum."""
        return tuple(sorted({c.task_type for c in self._configs.values()}))

    def estimates(self) -> Mapping[str, Estimate]:
        """Current estimate per config id, for re-pricing old usage events."""
        return {cid: c.estimate for cid, c in self._configs.items()}


@dataclass(frozen=True)
class _Prices:
    input_usd_per_mtok: float
    output_usd_per_mtok: float


def _read_yaml(path: Path, problems: list[str]) -> dict[str, Any] | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        problems.append(f"{path}: cannot read ({exc})")
        return None
    if not isinstance(data, dict):
        problems.append(f"{path}: expected a mapping")
        return None
    return data


def _load_pricing(path: Path, problems: list[str]) -> _Prices:
    data = _read_yaml(path, problems) or {}
    try:
        usd = data["usd_per_mtok"]
        return _Prices(float(usd["input"]), float(usd["output"]))
    except (KeyError, TypeError, ValueError):
        problems.append(f"{path}: needs usd_per_mtok.input and usd_per_mtok.output")
        return _Prices(0.0, 0.0)


def _load_skills(folder: Path, problems: list[str]) -> dict[str, Skill]:
    skills: dict[str, Skill] = {}
    for path in sorted(folder.glob("*/SKILL.md")):
        skill_id = path.parent.name
        text = path.read_text(encoding="utf-8")
        meta, body = _split_frontmatter(text)
        body = body.strip()
        if meta is None:
            problems.append(f"skill {skill_id}: missing frontmatter")
            continue
        size = len(body.encode("utf-8"))
        if size > MAX_SKILL_BYTES:
            problems.append(f"skill {skill_id}: {size} bytes, over the {MAX_SKILL_BYTES} byte limit")
        try:
            technique = Technique(meta.get("technique"))
        except ValueError:
            problems.append(f"skill {skill_id}: unknown technique {meta.get('technique')!r}")
            continue
        status = meta.get("status")
        if status not in ("draft", "approved"):
            problems.append(f"skill {skill_id}: status must be draft or approved, got {status!r}")
            continue
        skills[skill_id] = Skill(skill_id, technique, status == "draft", body + "\n")
    return skills


def _split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    meta = yaml.safe_load(text[4:end])
    return (meta if isinstance(meta, dict) else None), text[end + 5 :]


def _load_config(
    path: Path,
    config_id: str,
    skills: Mapping[str, Skill],
    prices: _Prices,
    root: Path,
    allow_drafts: bool,
    problems: list[str],
) -> Config | None:
    try:
        client = Client(path.parent.name)
    except ValueError:
        problems.append(f"{config_id}: unknown client folder {path.parent.name!r}")
        return None
    data = _read_yaml(path, problems)
    if data is None:
        return None
    before = len(problems)
    chosen: list[Skill] = []
    for skill_id in data.get("skills") or []:
        skill = skills.get(skill_id)
        if skill is None:
            problems.append(f"{config_id}: unknown skill {skill_id!r}")
            continue
        if skill.draft and not allow_drafts:
            problems.append(f"{config_id}: skill {skill_id!r} is a draft")
        if client not in APPLICABILITY[skill.technique]:
            problems.append(f"{config_id}: technique {skill.technique} is not allowed for {client}")
        chosen.append(skill)
    version = data.get("version")
    if not isinstance(version, int):
        problems.append(f"{config_id}: version must be an integer")
    estimate = _parse_estimate(data.get("expected_saving"), config_id, prices, problems)
    template = None
    if any(s.technique is Technique.SKILL_STATE for s in chosen):
        template_path = root / "templates" / "status" / f"{path.stem}.json"
        template = _load_template(template_path, config_id, problems)
    if len(problems) > before or estimate is None or not isinstance(version, int):
        return None
    return Config(config_id, client, path.stem, version, tuple(chosen), estimate, template)


def _load_template(path: Path, config_id: str, problems: list[str]) -> Mapping[str, Any] | None:
    if not path.is_file():
        problems.append(f"{config_id}: skill-state needs {path}")
        return None
    try:
        template = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        problems.append(f"{path}: invalid JSON ({exc})")
        return None
    if not isinstance(template, dict):
        problems.append(f"{path}: must be a JSON object")
        return None
    return template


def _parse_estimate(raw: object, config_id: str, prices: _Prices, problems: list[str]) -> Estimate | None:
    if not isinstance(raw, dict):
        problems.append(f"{config_id}: expected_saving is missing")
        return None
    try:
        provenance = Provenance(raw.get("provenance"))
    except ValueError:
        problems.append(
            f"{config_id}: expected_saving.provenance must be one of "
            f"{', '.join(p.value for p in Provenance)}"
        )
        return None
    try:
        tokens = raw["tokens"]
        percent = float(raw["percent"])
        input_tokens = int(tokens["input"])
        output_tokens = int(tokens["output"])
    except (KeyError, TypeError, ValueError):
        problems.append(f"{config_id}: expected_saving needs percent, tokens.input and tokens.output")
        return None
    usd = (input_tokens * prices.input_usd_per_mtok + output_tokens * prices.output_usd_per_mtok) / 1_000_000
    source = raw.get("source")
    return Estimate(percent, input_tokens, output_tokens, usd, provenance, str(source) if source else None)
