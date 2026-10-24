from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pytest
import yaml


class CatalogFiles:
    """Writes a catalog folder for a test. Starts valid: one approved skill and a default per client."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True)
        (root / "pricing.yaml").write_text(yaml.safe_dump({"usd_per_mtok": {"input": 3.0, "output": 15.0}}))
        self.skill("caveman", technique="caveman")
        self.config("code", "default", ["caveman"])
        self.config("cowork", "default", ["caveman"])

    def skill(self, skill_id: str, *, technique: str, status: str = "approved", body: str = "Be terse.") -> None:
        folder = self.root / "skills" / skill_id
        folder.mkdir(parents=True, exist_ok=True)
        meta = yaml.safe_dump({"technique": technique, "status": status})
        (folder / "SKILL.md").write_text(f"---\n{meta}---\n{body}\n")

    def config(
        self,
        client: str,
        task_type: str,
        skills: Sequence[str],
        *,
        version: int = 1,
        input_tokens: int = 1000,
        output_tokens: int = 200,
        provenance: str | None = "estimate",
        suffix: str = ".yaml",
    ) -> Path:
        saving: dict[str, object] = {"percent": 10, "tokens": {"input": input_tokens, "output": output_tokens}}
        if provenance is not None:
            saving["provenance"] = provenance
        path = self.root / "configs" / client / f"{task_type}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump({"version": version, "skills": list(skills), "expected_saving": saving}))
        return path

    def status_template(self, task_type: str, template: dict[str, object]) -> None:
        folder = self.root / "templates" / "status"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{task_type}.json").write_text(json.dumps(template))


@pytest.fixture
def catalog_files(tmp_path: Path) -> CatalogFiles:
    return CatalogFiles(tmp_path / "catalog")


@pytest.fixture
def ledger(tmp_path: Path):
    from hakka_mcp.ledger import Ledger

    return Ledger(f"sqlite:///{tmp_path / 'hakka.db'}")
