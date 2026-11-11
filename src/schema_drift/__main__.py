"""Command-line interface for schema-drift."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import compare, load_jsonl, profile
from .error import DriftError
from .model import Profile


def main(argv: list[str] | None = None) -> int:
    """Run the CLI, returning process exit code."""
    parser = argparse.ArgumentParser(
        prog="schema-drift", description="Detect schema drift between data batches"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    baseline_parser = subparsers.add_parser(
        "baseline", help="Create a baseline profile from a JSONL file"
    )
    baseline_parser.add_argument("jsonl", help="Input JSONL file")
    baseline_parser.add_argument("--out", required=True, help="Output profile file")

    check_parser = subparsers.add_parser(
        "check", help="Compare current JSONL against a baseline profile"
    )
    check_parser.add_argument("profile", help="Baseline profile JSON file")
    check_parser.add_argument("jsonl", help="Current JSONL file")
    check_parser.add_argument(
        "--null-rate-delta",
        type=float,
        default=0.1,
        help="Threshold for null rate increase (default: 0.1)",
    )

    args = parser.parse_args(argv)

    try:
        if args.command == "baseline":
            return _baseline(args)
        elif args.command == "check":
            return _check(args)
    except DriftError as e:
        print(f"error: {e.code}: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


def _baseline(args: argparse.Namespace) -> int:
    text = Path(args.jsonl).read_text(encoding="utf-8")
    records = load_jsonl(text)
    prof = profile(records)
    prof_json = prof.to_json()
    Path(args.out).write_text(prof_json, encoding="utf-8")
    return 0


def _check(args: argparse.Namespace) -> int:
    baseline_text = Path(args.profile).read_text(encoding="utf-8")
    baseline = Profile.from_json(baseline_text)
    current_text = Path(args.jsonl).read_text(encoding="utf-8")
    current_records = load_jsonl(current_text)
    current = profile(current_records)
    drifts = compare(baseline, current, null_rate_delta=args.null_rate_delta)
    has_high_or_medium = False
    for drift in drifts:
        print(f"{drift.severity} {drift.code} {drift.column}: {drift.detail}")
        if drift.severity in ("high", "medium"):
            has_high_or_medium = True
    return 1 if has_high_or_medium else 0


if __name__ == "__main__":
    raise SystemExit(main())
