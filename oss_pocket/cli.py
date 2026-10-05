# oss-pocket CLI
# Author: Mourad.Soltani
"""Command line for the OSS pocket threshold tracker."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from oss_pocket import SIGNATURE, __version__
from oss_pocket.ledger import LedgerError, build_report, load_csv


def health_payload() -> dict:
    return {
        "status": "ok",
        "service": "oss-pocket",
        "version": __version__,
        "signature": SIGNATURE,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oss-pocket",
        description="Track the EU-wide €10,000 B2C distance-selling threshold from a CSV.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    health = sub.add_parser("health", help="Print a health payload and exit 0")
    health.set_defaults(func=cmd_health)

    report = sub.add_parser("report", help="Score a sales CSV against the threshold")
    report.add_argument("csv_path")
    report.add_argument("--seller", required=True, help="Seller ISO-2 country, e.g. FR")
    report.add_argument("--year", type=int, default=date.today().year)
    report.set_defaults(func=cmd_report)
    return parser


def cmd_health(_args: argparse.Namespace) -> int:
    json.dump(health_payload(), sys.stdout)
    sys.stdout.write("\n")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    sales = load_csv(args.csv_path)
    report = build_report(sales, year=args.year, seller_country=args.seller)
    json.dump(report.as_dict(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 2 if report.over_threshold else 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except LedgerError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
