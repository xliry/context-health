from __future__ import annotations

import json

from context_health.models import Finding, ScanConfig
from context_health.scanner import scan

from tests.conftest import FIXTURES


def test_finding_serializes_required_fields():
    data = Finding("x.y", "Title", "low", "docs", "evidence", "fix").to_dict()
    assert {"id", "title", "severity", "category", "evidence", "recommendation"} <= data.keys()


def test_detects_node_profile_and_ignores_dependencies():
    snapshot = scan(ScanConfig(FIXTURES / "healthy_node"))
    assert "node" in snapshot.profile.ecosystems
    assert snapshot.profile.package_manager == "pnpm"
    assert snapshot.profile.workspaces == ()
    assert "node_modules/ignored.js" not in {file.path for file in snapshot.files}


def test_ignores_env_like_directories_but_keeps_root_dotenv(tmp_path):
    (tmp_path / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
    env_dir = tmp_path / "project-env"
    env_dir.mkdir()
    ignored_key = "IGNORED" + "_KEY"
    (env_dir / "ignored.py").write_text(f"os.getenv('{ignored_key}')\n", encoding="utf-8")

    snapshot = scan(ScanConfig(tmp_path))
    paths = {file.path for file in snapshot.files}

    assert ".env" in paths
    assert "project-env/ignored.py" not in paths


def test_detects_python_profile():
    snapshot = scan(ScanConfig(FIXTURES / "python_missing_env"))
    assert "python" in snapshot.profile.ecosystems
    assert snapshot.profile.has_readme


def test_detects_pnpm_monorepo_workspaces():
    snapshot = scan(ScanConfig(FIXTURES / "pnpm_monorepo"))

    assert snapshot.profile.workspaces == ("apps/*", "packages/*")
    assert "monorepo" in snapshot.profile.ecosystems
    assert snapshot.profile.package_manager == "pnpm"
    assert snapshot.profile.to_dict()["workspaces"] == ["apps/*", "packages/*"]


def test_detects_package_json_workspace_list(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps({"workspaces": ["./apps\\*", "packages/*", 123, "packages/*"]}),
        encoding="utf-8",
    )

    snapshot = scan(ScanConfig(tmp_path))

    assert snapshot.profile.workspaces == ("apps/*", "packages/*")
    assert "monorepo" in snapshot.profile.ecosystems


def test_detects_package_json_workspace_packages_object(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps({"workspaces": {"packages": ["apps/*", "./packages/*"]}}),
        encoding="utf-8",
    )

    snapshot = scan(ScanConfig(tmp_path))

    assert snapshot.profile.workspaces == ("apps/*", "packages/*")
    assert "monorepo" in snapshot.profile.ecosystems
