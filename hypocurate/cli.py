"""The command-line entry point (PRD Section 12). Step 2: `version` and `check-db`.
Step 4: `sources register` and `sources test`."""
from __future__ import annotations

import argparse
import json
import sys

from hypocurate.config import load_settings
from hypocurate.db.engine import database_reachable, make_engine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hypocurate")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("version", help="print the deployed version")
    sub.add_parser("check-db", help="check that the database answers")
    sources = sub.add_parser("sources", help="register the frozen sources; test a connection")
    sources_sub = sources.add_subparsers(dest="sources_command", required=True)
    register = sources_sub.add_parser("register", help="register and seal the frozen sources")
    register.add_argument("keys", nargs="*", help="source keys (default: all)")
    test = sources_sub.add_parser("test", help="read a source and show sample records")
    test.add_argument("key")
    test.add_argument("-n", type=int, default=5, help="number of sample records (default 5)")
    args = parser.parse_args(argv)

    settings = load_settings(web=False)
    if args.command == "version":
        print(settings.version)
        return 0
    engine = make_engine(settings.database_url)
    if args.command == "check-db":
        reachable = database_reachable(engine)
        print("database reachable" if reachable else "database NOT reachable")
        return 0 if reachable else 1
    return _sources(args, engine)


def _sources(args, engine) -> int:
    from hypocurate.sources.connection import test_connection
    from hypocurate.sources.record import AdapterError
    from hypocurate.sources.versions import SOURCES, RegistrationError, UnsealedVersion, register

    try:
        if args.sources_command == "register":
            for key in args.keys or list(SOURCES):
                r = register(engine, key)
                state = "registered and sealed" if r.created else "already registered"
                print(f"{r.key}: {state}; version {r.version_id} ({r.label}); fingerprint {r.fingerprint}")
            return 0
        report = test_connection(engine, args.key, args.n)
        # Assigned values carry status "assigned" and their citation in this output.
        print(json.dumps(report.to_json(), indent=2, ensure_ascii=False))
        return 0
    except (RegistrationError, UnsealedVersion, AdapterError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
