from __future__ import annotations

from collections.abc import Callable

import pytest

from context_health.models import Report, ScanConfig
from context_health.report import render_json, render_markdown, render_terminal
from context_health.scanner import run_rules, scan
from context_health.scoring import build_report

from tests.conftest import FIXTURES, ROOT


SNAPSHOTS = ROOT / "tests" / "snapshots"
RENDERERS: dict[str, Callable[[Report], str]] = {
    "json": render_json,
    "md": render_markdown,
    "txt": render_terminal,
}


@pytest.mark.parametrize(
    ("fixture_name", "fmt"),
    (
        ("blocked_node", "json"),
        ("blocked_node", "md"),
        ("healthy_node", "txt"),
        ("pnpm_monorepo", "json"),
        ("vague_agent_instructions", "json"),
    ),
)
def test_output_snapshots(fixture_name: str, fmt: str):
    assert render_fixture(fixture_name, fmt) == read_snapshot(f"{fixture_name}.{fmt}")


def render_fixture(name: str, fmt: str) -> str:
    snapshot = scan(ScanConfig(FIXTURES / name))
    report = build_report(run_rules(snapshot), snapshot.profile)
    return _normalize_line_endings(RENDERERS[fmt](report))


def read_snapshot(name: str) -> str:
    return _normalize_line_endings((SNAPSHOTS / name).read_text(encoding="utf-8"))


def _normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n")


# If intentional output wording changes, regenerate snapshots by running
# render_fixture() for the affected case or copying verified output from the
# test failure.
