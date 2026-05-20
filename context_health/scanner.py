from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

from context_health.models import FileInfo, RepoProfile, RepoSnapshot, ScanConfig
from context_health.rules import agent_instructions, bloat, consistency, docs, env, tests


DEFAULT_IGNORES = {
    ".git",
    "node_modules",
    ".next",
    "dist",
    "build",
    "coverage",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".turbo",
    ".cache",
    "target",
}
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".toml",
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".yml",
    ".yaml",
    ".env",
    ".sample",
    ".example",
    ".lock",
}
IMPORTANT_NAMES = {
    "package.json",
    "pnpm-workspace.yaml",
    "yarn.lock",
    "pnpm-lock.yaml",
    "package-lock.json",
    "pyproject.toml",
    "requirements.txt",
    "uv.lock",
    "poetry.lock",
    "README.md",
    "readme.md",
    "README",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".env.example",
    ".env.sample",
    ".env",
    "docker-compose.yml",
    "Dockerfile",
}
RULES = [
    agent_instructions.run,
    docs.run,
    env.run,
    bloat.run,
    consistency.run,
    tests.run,
]


def scan(config: ScanConfig) -> RepoSnapshot:
    files, texts = _walk(config)
    profile = _profile(config.root, files, texts)
    return RepoSnapshot(config.root, config, tuple(files), profile, texts)


def run_rules(snapshot: RepoSnapshot):
    findings = []
    seen = set()
    for rule in RULES:
        for item in rule(snapshot):
            key = (item.id, item.path, item.evidence)
            if key not in seen:
                findings.append(item)
                seen.add(key)
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(findings, key=lambda f: (order.get(f.severity, 9), f.id))


def _walk(config: ScanConfig) -> tuple[list[FileInfo], dict[str, str]]:
    files: list[FileInfo] = []
    texts: dict[str, str] = {}
    for path in config.root.rglob("*"):
        rel = path.relative_to(config.root).as_posix()
        parts = set(Path(rel).parts)
        if path.is_dir() or parts & DEFAULT_IGNORES:
            continue
        if config.include and not any(fnmatch.fnmatch(rel, glob) for glob in config.include):
            continue
        if any(fnmatch.fnmatch(rel, glob) for glob in config.exclude):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        is_text = _looks_text(path)
        preview = ""
        if is_text:
            try:
                preview = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                preview = ""
            if _should_keep_text(rel, size):
                texts[rel] = preview
        files.append(FileInfo(rel, size, path.suffix.lower(), is_text, preview[:2000]))
    return files, texts


def _looks_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in IMPORTANT_NAMES


def _should_keep_text(rel: str, size: int) -> bool:
    if size > 1024 * 1024:
        return False
    return rel in IMPORTANT_NAMES or rel.startswith((".github/workflows/", ".agents/", ".claude/", ".codex/")) or _looks_source(rel)


def _looks_source(rel: str) -> bool:
    return Path(rel).suffix.lower() in {".py", ".js", ".jsx", ".ts", ".tsx"}


def _profile(root: Path, files: list[FileInfo], texts: dict[str, str]) -> RepoProfile:
    paths = {file.path for file in files}
    package = _parse_json(texts.get("package.json", ""))
    pyproject = _parse_toml(texts.get("pyproject.toml", ""))
    scripts = package.get("scripts", {}) if isinstance(package.get("scripts"), dict) else {}
    ecosystems: list[str] = []
    if "package.json" in paths:
        ecosystems.append("node")
    if "pyproject.toml" in paths or "requirements.txt" in paths:
        ecosystems.append("python")
    if isinstance(package, dict):
        deps = " ".join(
            name
            for key in ("dependencies", "devDependencies")
            if isinstance(package.get(key), dict)
            for name in package[key]
        )
        if "next" in deps:
            ecosystems.append("next")
        if "vite" in deps:
            ecosystems.append("vite")
        if package.get("workspaces") or "pnpm-workspace.yaml" in paths:
            ecosystems.append("monorepo")
    if pyproject.get("tool", {}).get("uv") or "uv.lock" in paths:
        ecosystems.append("python")
    package_manager = _package_manager(package, paths, texts.get("README.md", "") + texts.get("readme.md", ""))
    important = tuple(sorted(path for path in paths if path in IMPORTANT_NAMES or path.startswith(".github/workflows/")))
    return RepoProfile(
        ecosystems=tuple(dict.fromkeys(ecosystems)) or ("generic",),
        package_manager=package_manager,
        has_readme=any(path.lower() in {"readme.md", "readme"} for path in paths),
        has_env_example=(".env.example" in paths or ".env.sample" in paths),
        has_ci=any(path.startswith(".github/workflows/") for path in paths),
        scripts={str(k): str(v) for k, v in scripts.items()},
        important_files=important,
    )


def _parse_json(text: str) -> dict[str, Any]:
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _parse_toml(text: str) -> dict[str, Any]:
    if not text:
        return {}
    try:
        data = tomllib.loads(text)
        return data if isinstance(data, dict) else {}
    except tomllib.TOMLDecodeError:
        return {}


def _package_manager(package: dict[str, Any], paths: set[str], readme: str) -> str | None:
    manager = package.get("packageManager")
    if isinstance(manager, str) and "@" in manager:
        return manager.split("@", 1)[0]
    if "pnpm-lock.yaml" in paths:
        return "pnpm"
    if "yarn.lock" in paths:
        return "yarn"
    if "package-lock.json" in paths:
        return "npm"
    match = re.search(r"\b(pnpm|yarn|npm)\b", readme)
    return match.group(1) if match else None
