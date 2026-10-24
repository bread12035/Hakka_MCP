"""Scenarios of the catalog delta spec. One test per scenario."""

from pathlib import Path

import pytest

from hakka_mcp.catalog import Catalog, CatalogError, Client

SHIPPED = Path(__file__).resolve().parents[1] / "catalog"


def load_problems(catalog_files, *, allow_drafts=False) -> str:
    with pytest.raises(CatalogError) as err:
        Catalog.load(catalog_files.root, allow_drafts=allow_drafts)
    return "\n".join(err.value.problems)


def test_code_only_technique_in_a_cowork_config(catalog_files):
    """Code-only technique in a Cowork config."""
    catalog_files.skill("code-graph", technique="code-graph")
    catalog_files.config("cowork", "cowork-poc", ["code-graph"])
    problems = load_problems(catalog_files)
    assert "cowork/cowork-poc" in problems
    assert "code-graph" in problems


def test_shared_technique_in_both_clients(catalog_files):
    """Shared technique in both clients."""
    catalog_files.config("code", "code-feature", ["caveman"])
    catalog_files.config("cowork", "cowork-doc", ["caveman"])
    catalog = Catalog.load(catalog_files.root, allow_drafts=False)
    assert catalog.resolve(Client.CODE, "code-feature").fallback is False
    assert catalog.resolve(Client.COWORK, "cowork-doc").fallback is False


def test_config_resolves_for_a_known_pair(catalog_files):
    """Config resolves for a known pair."""
    catalog_files.config("code", "code-bugfix", ["caveman"], version=3, input_tokens=5000, output_tokens=700)
    resolution = Catalog.load(catalog_files.root, allow_drafts=False).resolve(Client.CODE, "code-bugfix")
    config = resolution.config
    assert config.id == "code/code-bugfix"
    assert [s.id for s in config.skills] == ["caveman"]
    assert config.version == 3
    assert config.estimate.percent == 10
    assert (config.estimate.input_tokens, config.estimate.output_tokens) == (5000, 700)


def test_duplicate_config_for_one_pair(catalog_files):
    """Duplicate config for one pair."""
    first = catalog_files.config("code", "code-bugfix", ["caveman"])
    second = catalog_files.config("code", "code-bugfix", ["caveman"], suffix=".yml")
    problems = load_problems(catalog_files)
    assert str(first) in problems
    assert str(second) in problems


def test_config_names_a_missing_skill(catalog_files):
    """Config names a missing skill."""
    catalog_files.config("code", "code-feature", ["no-such-skill"])
    problems = load_problems(catalog_files)
    assert "code/code-feature" in problems
    assert "no-such-skill" in problems


def test_several_invalid_configs_reported_together(catalog_files):
    """Several invalid configs reported together."""
    catalog_files.config("code", "code-feature", ["missing-a"])
    catalog_files.config("cowork", "cowork-poc", ["missing-b"])
    problems = load_problems(catalog_files)
    assert "missing-a" in problems
    assert "missing-b" in problems


def test_skill_over_the_size_limit(catalog_files):
    """Skill over the size limit."""
    catalog_files.skill("huge", technique="caveman", body="x" * 5000)
    problems = load_problems(catalog_files)
    assert "huge" in problems
    assert "5000" in problems


def test_saving_number_without_provenance(catalog_files):
    """Saving number without provenance."""
    catalog_files.config("code", "code-feature", ["caveman"], provenance=None)
    problems = load_problems(catalog_files)
    assert "code/code-feature" in problems
    assert "provenance" in problems


def test_shipped_catalog_loads():
    """Shipped catalog loads."""
    catalog = Catalog.load(SHIPPED, allow_drafts=True)
    assert set(catalog.task_types()) == {
        "cowork-poc", "cowork-daily-data", "cowork-doc",
        "code-feature", "code-bugfix", "code-explore", "default",
    }
    assert catalog.resolve(Client.CODE, "default").fallback is False
    assert catalog.resolve(Client.COWORK, "default").fallback is False


def test_config_references_a_draft_skill(catalog_files):
    """Config references a draft skill."""
    catalog_files.skill("new-rules", technique="caveman", status="draft")
    catalog_files.config("code", "code-feature", ["new-rules"])
    problems = load_problems(catalog_files)
    assert "code/code-feature" in problems
    assert "new-rules" in problems


def test_malformed_skill_frontmatter_reported_with_other_problems(catalog_files):
    (catalog_files.root / "skills" / "broken").mkdir()
    (catalog_files.root / "skills" / "broken" / "SKILL.md").write_text("---\ntechnique: [\n---\nbody\n")
    catalog_files.config("code", "code-feature", ["missing-a"])
    problems = load_problems(catalog_files)
    assert "skill broken" in problems
    assert "missing-a" in problems


def test_boolean_version_and_negative_tokens_rejected(catalog_files):
    path = catalog_files.config("code", "code-feature", ["caveman"], input_tokens=-5)
    path.write_text(path.read_text().replace("version: 1", "version: true"))
    problems = load_problems(catalog_files)
    assert "version must be a positive integer" in problems
    assert "non-negative tokens" in problems
