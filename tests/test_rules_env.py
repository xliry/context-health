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


def test_env_inference_skips_virtualenv_like_paths(tmp_path):
    app_key = "APP" + "_KEY"
    third_party_key = "THIRD" + "_PARTY_KEY"
    (tmp_path / "README.md").write_text("# x\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text(f"{app_key}=fake\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(f"os.getenv('{app_key}')\n", encoding="utf-8")
    third_party = tmp_path / "dough-env" / "lib" / "site-packages" / "pkg"
    third_party.mkdir(parents=True)
    (third_party / "config.py").write_text(f"os.getenv('{third_party_key}')\n", encoding="utf-8")

    snapshot = scan(ScanConfig(tmp_path))
    keys = env._env_keys(snapshot)
    findings = env.run(snapshot)

    assert app_key in keys
    assert third_party_key not in keys
    assert "env.example_missing_required_keys" not in {f.id for f in findings}


def test_env_missing_example_still_uses_first_party_source(tmp_path):
    api_key = "API" + "_KEY"
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(f"process.env.{api_key}\n", encoding="utf-8")

    findings = env.run(scan(ScanConfig(tmp_path)))

    assert "env.missing_example" in {f.id for f in findings}
