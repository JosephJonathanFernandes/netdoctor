"""Headless CLI for NetDoctor.

Allows running speed tests and exporting data without the GUI, useful for
automation, CI, and power users.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from app.config import APP_NAME, APP_VERSION
from app.database.repository import (
    SpeedTestRepository,
    export_speed_tests_csv,
    export_speed_tests_json,
)
from app.services.speed_test import SpeedTestService, check_connectivity, format_result_for_display
from app.services.updater import check_for_updates_sync
from app.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="netdoctor",
        description=f"{APP_NAME} — Command-line interface",
    )
    sub = parser.add_subparsers(dest="command")

    # run-test
    p_test = sub.add_parser("run-test", help="Run a single speed test")
    p_test.add_argument("--json", action="store_true", help="Output JSON")
    p_test.add_argument("--save", action="store_true", help="Save result to SQLite")

    # history
    p_hist = sub.add_parser("history", help="Show recent speed-test history")
    p_hist.add_argument("--limit", type=int, default=10, help="Max records")
    p_hist.add_argument("--json", action="store_true", help="Output JSON")

    # export
    p_exp = sub.add_parser("export", help="Export history to CSV/JSON")
    p_exp.add_argument("path", help="Output file path")
    p_exp.add_argument("--format", choices=["csv", "json"], default="csv")

    # stats
    sub.add_parser("stats", help="Show aggregate statistics")

    # check
    sub.add_parser("check", help="Check internet connectivity")

    # update
    p_upd = sub.add_parser("update", help="Check for updates")
    p_upd.add_argument("--download", action="store_true", help="Download latest release")

    # version
    sub.add_parser("version", help="Show version")

    return parser


def cmd_run_test(args: argparse.Namespace) -> int:
    svc = SpeedTestService()
    result = svc.run()
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, default=str))
    else:
        disp = format_result_for_display(result)
        print(f"Status: {disp['status']}")
        print(f"Download: {disp['download']}")
        print(f"Upload: {disp['upload']}")
        print(f"Latency: {disp['latency']}")
        print(f"Jitter: {disp['jitter']}")
        print(f"Packet loss: {disp['packet_loss']}")
        print(f"Server: {disp['server']}")
        if disp["error"]:
            print(f"Error: {disp['error']}")
    if args.save:
        repo = SpeedTestRepository()
        repo.insert(result.to_dict())
        print("Saved to database.")
    return 0 if result.status == "completed" else 1


def cmd_history(args: argparse.Namespace) -> int:
    repo = SpeedTestRepository()
    records = repo.fetch_all(limit=args.limit)
    if args.json:
        print(json.dumps(records, indent=2, default=str))
    else:
        if not records:
            print("No records found.")
            return 0
        print(f"{'Timestamp':<20} {'Download':<12} {'Upload':<10} {'Latency':<10} {'Status':<10}")
        print("-" * 65)
        for rec in records:
            ts = rec.get("timestamp") or ""
            try:
                dt = datetime.fromisoformat(ts)
                ts_disp = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                ts_disp = str(ts)[:19]
            dl = f"{rec.get('download_mbps'):.2f} Mbps" if rec.get("download_mbps") is not None else "n/a"
            ul = f"{rec.get('upload_mbps'):.2f} Mbps" if rec.get("upload_mbps") is not None else "n/a"
            lat = f"{rec.get('latency_ms'):.1f} ms" if rec.get("latency_ms") is not None else "n/a"
            print(f"{ts_disp:<20} {dl:<12} {ul:<10} {lat:<10} {rec.get('status') or '—':<10}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    repo = SpeedTestRepository()
    records = repo.fetch_all()
    if args.format == "csv":
        written = export_speed_tests_csv(args.path, records)
    else:
        written = export_speed_tests_json(args.path, records)
    print(f"Exported {written} record(s) to {args.path}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    repo = SpeedTestRepository()
    stats = repo.stats()
    print(json.dumps(stats, indent=2, default=str))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    ok = check_connectivity()
    print("Online" if ok else "Offline")
    return 0 if ok else 1


def cmd_update(args: argparse.Namespace) -> int:
    release = check_for_updates_sync()
    if release is None:
        print(f"NetDoctor {APP_VERSION} is up to date.")
        return 0
    print(f"Update available: {release.version} (current {APP_VERSION})")
    print(release.html_url)
    if args.download:
        print("Download not supported in headless CLI; visit the URL above.")
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    print(f"{APP_NAME} {APP_VERSION}")
    return 0


COMMAND_MAP = {
    "run-test": cmd_run_test,
    "history": cmd_history,
    "export": cmd_export,
    "stats": cmd_stats,
    "check": cmd_check,
    "update": cmd_update,
    "version": cmd_version,
}


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1
    handler = COMMAND_MAP.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
