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
