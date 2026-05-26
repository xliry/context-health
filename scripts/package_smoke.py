from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def main() -> int:
    _clean_dist()
    _run([sys.executable, "-m", "build"], cwd=ROOT)
    sdist, wheel = _built_artifacts()
    _check_sdist(sdist)

    with tempfile.TemporaryDirectory(prefix="context-health-smoke-") as tmp:
        venv_dir = Path(tmp) / "venv"
        work_dir = Path(tmp) / "work"
        work_dir.mkdir()
        venv.EnvBuilder(with_pip=True).create(venv_dir)
        python = _venv_python(venv_dir)
        context_health = _venv_script(venv_dir, "context-health")

        _run([str(python), "-m", "pip", "install", str(wheel)], cwd=work_dir)
        _run([str(context_health), "--help"], cwd=work_dir)
        _run([str(context_health), "run-audit", "--help"], cwd=work_dir)
        _run([str(context_health), str(ROOT / "tests" / "fixtures" / "healthy_node")], cwd=work_dir)
        _run([str(context_health), "run-audit", str(ROOT / "tests" / "fixtures" / "agent_run_good")], cwd=work_dir)
        blocked = _run([str(context_health), str(ROOT / "tests" / "fixtures" / "blocked_node"), "--json"], cwd=work_dir)
        json.loads(blocked.stdout)

    print(f"package smoke passed: {wheel.name}")
    return 0


def _clean_dist() -> None:
    DIST.mkdir(exist_ok=True)
    dist_root = DIST.resolve()
    if dist_root.parent != ROOT.resolve():
        raise RuntimeError(f"Refusing to clean unexpected dist path: {dist_root}")
    for path in DIST.iterdir():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def _built_artifacts() -> tuple[Path, Path]:
    wheels = sorted(DIST.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"Expected exactly one wheel in {DIST}, found {len(wheels)}")
    sdists = sorted(DIST.glob("*.tar.gz"))
    if len(sdists) != 1:
        raise RuntimeError(f"Expected exactly one sdist in {DIST}, found {len(sdists)}")
    print(f"built artifacts: {sdists[0].name}, {wheels[0].name}")
    return sdists[0], wheels[0]


def _check_sdist(sdist: Path) -> None:
    required = {
        "tests/fixtures/healthy_node/README.md",
        "tests/fixtures/blocked_node/package.json",
        "tests/snapshots/blocked_node.json",
        "tests/snapshots/healthy_node.txt",
    }
    forbidden = {
        "dist/",
        "build/",
        ".pytest_cache/",
        "__pycache__/",
        "context_health.egg-info/",
        "blocked.json",
        "context-health-report.json",
    }
    with tarfile.open(sdist, "r:gz") as archive:
        members = {_strip_archive_root(name) for name in archive.getnames()}

    missing = sorted(path for path in required if path not in members)
    if missing:
        raise RuntimeError(f"sdist is missing expected test assets: {', '.join(missing)}")

    present_forbidden = sorted(path for path in members for forbidden_path in forbidden if _matches(path, forbidden_path))
    if present_forbidden:
        raise RuntimeError(f"sdist contains generated artifacts: {', '.join(present_forbidden)}")
    print("sdist manifest check passed")


def _strip_archive_root(name: str) -> str:
    normalized = name.replace("\\", "/")
    parts = normalized.split("/", 1)
    return parts[1] if len(parts) == 2 else parts[0]


def _matches(path: str, forbidden: str) -> bool:
    if forbidden.endswith("/"):
        return forbidden.rstrip("/") in path.split("/")
    return path == forbidden


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_script(venv_dir: Path, name: str) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / f"{name}.exe"
    return venv_dir / "bin" / name


def _run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    print(f"+ {' '.join(args)}", flush=True)
    try:
        return subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as error:
        if error.stdout:
            print(error.stdout, end="")
        if error.stderr:
            print(error.stderr, end="", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
