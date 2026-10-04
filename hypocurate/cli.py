"""The command-line entry point (PRD Section 12). Step 2: `version` and `check-db` only."""
from __future__ import annotations

import argparse
import sys

from hypocurate.config import load_settings
from hypocurate.db.engine import database_reachable, make_engine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hypocurate")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("version", help="print the deployed version")
    sub.add_parser("check-db", help="check that the database answers")
    args = parser.parse_args(argv)

    settings = load_settings(web=False)
    if args.command == "version":
        print(settings.version)
        return 0
    reachable = database_reachable(make_engine(settings.database_url))
    print("database reachable" if reachable else "database NOT reachable")
    return 0 if reachable else 1


if __name__ == "__main__":
    sys.exit(main())
