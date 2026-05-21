from __future__ import annotations

from tests.conftest import ROOT


def test_agent_handoff_recipe_is_linked_and_has_core_commands():
    recipe_path = ROOT / "docs" / "agent-handoff-recipe.md"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    recipe = recipe_path.read_text(encoding="utf-8")

    assert recipe_path.exists()
    assert "docs/agent-handoff-recipe.md" in readme
    assert "context-health . --markdown" in recipe
    assert "context-health . --json" in recipe
    assert "context-health . --fail-under" in recipe


def test_docs_cover_v0_2_limitations_and_config_recipe():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    recipe = (ROOT / "docs" / "agent-handoff-recipe.md").read_text(encoding="utf-8")
    limitations_path = ROOT / "docs" / "known-limitations.md"
    assert limitations_path.exists()
    limitations = limitations_path.read_text(encoding="utf-8")
    checklist = (ROOT / "docs" / "release-checklist.md").read_text(encoding="utf-8")

    assert "docs/known-limitations.md" in readme
    assert ".context-health.toml" in readme
    assert ".context-health.toml" in recipe
    assert "*-env/**" in readme
    assert "*-env/**" in recipe
    assert "env var inference is heuristic" in limitations.lower()
    assert "root `AGENTS.md`" in limitations
    assert "dogfood" in checklist.lower()
