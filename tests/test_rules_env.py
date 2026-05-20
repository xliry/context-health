from __future__ import annotations

from context_health.models import ScanConfig
from context_health.rules import env
from context_health.scanner import scan

from tests.conftest import FIXTURES


def test_python_env_example_missing():
    findings = env.run(scan(ScanConfig(FIXTURES / "python_missing_env")))
    assert "env.missing_example" in {f.id for f in findings}


def test_env_secret_present(tmp_path):
    (tmp_path / "README.md").write_text("# x\n", encoding="utf-8")
    (tmp_path / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
    findings = env.run(scan(ScanConfig(tmp_path)))
    assert "env.secret_file_present" in {f.id for f in findings}
