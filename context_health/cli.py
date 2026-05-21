from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

from context_health.models import ScanConfig
from context_health.report import render_json, render_markdown, render_terminal
from context_health.scanner import run_rules, scan
from context_health.scoring import build_report


CONFIG_FILE = ".context-health.toml"
CONFIG_KEYS = {"include", "exclude", "max_file_kb", "fail_under"}
DEFAULT_MAX_FILE_KB = 512


class ConfigError(ValueError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit repository agent-context readiness.")
    parser.add_argument("path", nargs="?", default=".", help="Repository path to scan")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--markdown", help="Write a Markdown report to this path")
    parser.add_argument("--fail-under", type=int, help="Exit 1 when score is below this value")
    parser.add_argument("--include", action="append", default=[], help="Include glob, repeatable")
    parser.add_argument("--exclude", action="append", default=[], help="Exclude glob, repeatable")
    parser.add_argument("--max-file-kb", type=int, help="Large file threshold")
    parser.add_argument("--verbose", action="store_true", help="Show traceback for internal errors")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: path is not a directory: {root}", file=sys.stderr)
        return 2
    try:
        has_config_file = (root / CONFIG_FILE).exists()
        file_config = _load_config(root)
        include = tuple(file_config.get("include", ())) + tuple(args.include)
        exclude = tuple(file_config.get("exclude", ())) + tuple(args.exclude)
        max_file_kb = args.max_file_kb if args.max_file_kb is not None else file_config.get("max_file_kb", DEFAULT_MAX_FILE_KB)
        fail_under = args.fail_under if args.fail_under is not None else file_config.get("fail_under")
        config_file = CONFIG_FILE if has_config_file else None
        config = ScanConfig(root, include, exclude, max_file_kb, args.verbose, config_file)
        snapshot = scan(config)
        report = build_report(run_rules(snapshot), snapshot.profile)
        if args.markdown:
            Path(args.markdown).write_text(render_markdown(report), encoding="utf-8")
        sys.stdout.write(render_json(report) if args.json else render_terminal(report))
        if fail_under is not None and report.score < fail_under:
            return 1
        return 0
    except Exception as exc:  # pragma: no cover
        if args.verbose:
            traceback.print_exc()
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


def _load_config(root: Path) -> dict[str, Any]:
    path = root / CONFIG_FILE
    if not path.exists():
        return {}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8-sig"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{CONFIG_FILE}: invalid TOML: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{CONFIG_FILE}: expected top-level TOML table")
    unknown = sorted(set(data) - CONFIG_KEYS)
    if unknown:
        raise ConfigError(f"{CONFIG_FILE}: unknown key(s): {', '.join(unknown)}")
    config: dict[str, Any] = {}
    if "include" in data:
        config["include"] = _string_list(data["include"], "include")
    if "exclude" in data:
        config["exclude"] = _string_list(data["exclude"], "exclude")
    if "max_file_kb" in data:
        config["max_file_kb"] = _positive_int(data["max_file_kb"], "max_file_kb")
    if "fail_under" in data:
        config["fail_under"] = _bounded_int(data["fail_under"], "fail_under", 0, 100)
    return config


def _string_list(value: Any, key: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{CONFIG_FILE}: {key} must be a list of strings")
    return tuple(value)


def _positive_int(value: Any, key: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ConfigError(f"{CONFIG_FILE}: {key} must be a positive integer")
    return value


def _bounded_int(value: Any, key: str, minimum: int, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum or value > maximum:
        raise ConfigError(f"{CONFIG_FILE}: {key} must be an integer from {minimum} to {maximum}")
    return value


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
