from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from context_health.models import ScanConfig
from context_health.report import render_json, render_markdown, render_terminal
from context_health.scanner import run_rules, scan
from context_health.scoring import build_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit repository agent-context readiness.")
    parser.add_argument("path", nargs="?", default=".", help="Repository path to scan")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--markdown", help="Write a Markdown report to this path")
    parser.add_argument("--fail-under", type=int, help="Exit 1 when score is below this value")
    parser.add_argument("--include", action="append", default=[], help="Include glob, repeatable")
    parser.add_argument("--exclude", action="append", default=[], help="Exclude glob, repeatable")
    parser.add_argument("--max-file-kb", type=int, default=512, help="Large file threshold")
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
        config = ScanConfig(root, tuple(args.include), tuple(args.exclude), args.max_file_kb, args.verbose)
        snapshot = scan(config)
        report = build_report(run_rules(snapshot), snapshot.profile)
        if args.markdown:
            Path(args.markdown).write_text(render_markdown(report), encoding="utf-8")
        sys.stdout.write(render_json(report) if args.json else render_terminal(report))
        if args.fail_under is not None and report.score < args.fail_under:
            return 1
        return 0
    except Exception as exc:  # pragma: no cover
        if args.verbose:
            traceback.print_exc()
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
