from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def main() -> int:
    _clean_dist()
    _run([sys.executable, "-m", "build"], cwd=ROOT)
    wheel = _built_wheel()

    with tempfile.TemporaryDirectory(prefix="context-health-smoke-") as tmp:
        venv_dir = Path(tmp) / "venv"
        work_dir = Path(tmp) / "work"
        work_dir.mkdir()
        venv.EnvBuilder(with_pip=True).create(venv_dir)
        python = _venv_python(venv_dir)
        context_health = _venv_script(venv_dir, "context-health")

        _run([str(python), "-m", "pip", "install", str(wheel)], cwd=work_dir)
        _run([str(context_health), "--help"], cwd=work_dir)
        _run([str(context_health), str(ROOT / "tests" / "fixtures" / "healthy_node")], cwd=work_dir)
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


def _built_wheel() -> Path:
    wheels = sorted(DIST.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"Expected exactly one wheel in {DIST}, found {len(wheels)}")
    sdists = sorted(DIST.glob("*.tar.gz"))
    if len(sdists) != 1:
        raise RuntimeError(f"Expected exactly one sdist in {DIST}, found {len(sdists)}")
    print(f"built artifacts: {sdists[0].name}, {wheels[0].name}")
    return wheels[0]


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
