from __future__ import annotations

from context_health.models import ScanConfig
from context_health.rules import bloat
from context_health.scanner import scan

from tests.conftest import FIXTURES


def test_bloaty_repo_flags_large_and_generated_file():
    snapshot = scan(ScanConfig(FIXTURES / "bloaty_repo", max_file_kb=1))
    ids = {f.id for f in bloat.run(snapshot)}
    assert "context.large_file" in ids
    assert "context.generated_artifact_in_repo" in ids


def test_dist_is_ignored_by_default():
    paths = {f.path for f in scan(ScanConfig(FIXTURES / "bloaty_repo")).files}
    assert "dist/bundle.js" not in paths
