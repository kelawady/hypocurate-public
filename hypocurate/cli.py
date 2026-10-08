"""The command-line entry point (PRD Section 12). Step 2: `version` and `check-db`.
Step 4: `sources register` and `sources test`. Step 8a: the curation workflow at registration
(`sources curate | proposals | accept | reject | seal-curation | export-curation`). Step 8b: `run`, `dispatch`
and `show` (owner, A9, Q10): a query is created, submitted, confirmed by a named person and dispatched here,
and the run itself executes in the guarded process (`access.guarded`); the child's error text is never printed."""
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
    curate = sources_sub.add_parser("curate", help="ask the Curator for values the documentation states (costs money)")
    curate.add_argument("key")
    curate.add_argument("--ceiling", help="the most this curation may cost, in USD (refused above it)")
    listing = sources_sub.add_parser("proposals", help="list the Curator's proposals and decisions")
    listing.add_argument("key")
    for name in ("accept", "reject"):
        p = sources_sub.add_parser(name, help=f"{name} one proposal that passed the checks")
        p.add_argument("proposal", type=int)
        p.add_argument("--by", required=True, help="the name of the person deciding")
        p.add_argument("--note")
    seal = sources_sub.add_parser("seal-curation", help="seal the accepted values into a new source version")
    seal.add_argument("key")
    export = sources_sub.add_parser("export-curation", help="write the curated version's curation.json")
    export.add_argument("key")
    export.add_argument("--out", help="the file to write (default: print it)")
    run = sub.add_parser("run", help="create, dispatch and run a query to its end (may cost money: model calls)")
    run.add_argument("claim", help="the hypothesis in words")
    run.add_argument("--sources", required=True, help="comma-separated source keys, e.g. mpea,tamu_fcc")
    run.add_argument("--by", required=True, help="the name of the person confirming the domain")
    run.add_argument("--domain", default="grain_size_strengthening")
    run.add_argument("--sufficiency", default="fixed_minimum", choices=("fixed_minimum", "use_available"))
    run.add_argument("--fixed-plan", action="store_true", help="the reference plan, Planner bypassed (14.1a)")
    run.add_argument("--test-data", action="store_true", help="mark the run as a test with constructed data")
    run.add_argument("--ceiling", help="the most this run's model calls may cost, in USD (refused above it)")
    dispatch = sub.add_parser("dispatch", help="dispatch a submitted query by its number and run it (may cost money)")
    dispatch.add_argument("number", help="the query number, e.g. Q-0002")
    dispatch.add_argument("--by", required=True, help="the name of the person confirming the domain")
    dispatch.add_argument("--ceiling", help="the most this run's model calls may cost, in USD")
    show = sub.add_parser("show", help="print a run's outcome and summary")
    show.add_argument("run", type=int)
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
    if args.command in ("run", "dispatch", "show"):
        from hypocurate.cli_runs import command
        return command(args, engine)
    return _sources(args, engine)


def _sources(args, engine) -> int:
    from hypocurate.sources.connection import test_connection
    from hypocurate.sources.record import AdapterError
    from hypocurate.sources.versions import SOURCES, RegistrationError, UnsealedVersion, register

    if args.sources_command in ("curate", "proposals", "accept", "reject", "seal-curation", "export-curation"):
        return _curation(args, engine)
    try:
        if args.sources_command == "register":
            for key in args.keys or list(SOURCES):
                r = register(engine, key)
                state = "registered and sealed" if r.created else "already registered"
                print(f"{r.key}: {state}; version {r.version_id} ({r.label}); fingerprint {r.fingerprint}")
            return 0
        report = test_connection(engine, args.key, args.n)
        # Assigned values carry status "assigned_from_source" or "assigned_by_decision" and their
        # citation in this output.
        print(json.dumps(report.to_json(), indent=2, ensure_ascii=False))
        return 0
    except (RegistrationError, UnsealedVersion, AdapterError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


def _curation(args, engine) -> int:
    from hypocurate.access.guarded import GuardedRunError, run_guarded
    from hypocurate.sources import curation
    from hypocurate.sources.versions import UnsealedVersion

    try:
        if args.sources_command == "curate":
            try:
                out = run_guarded("hypocurate.sources.curation:curate_guarded",
                                  {"key": args.key, "ceiling": args.ceiling}, timeout=900)
            except GuardedRunError:
                # The child's error text may hold anything; it stays out of the output.
                print("error: the curation did not finish (see the process log)", file=sys.stderr)
                return 1
        elif args.sources_command == "proposals":
            out = curation.proposals(engine, args.key)
        elif args.sources_command in ("accept", "reject"):
            out = curation.decide(engine, args.proposal, args.sources_command + "ed", args.by, args.note)
        elif args.sources_command == "seal-curation":
            r = curation.seal_curation(engine, args.key)
            out = {"key": r.key, "version": r.version_id, "label": r.label, "fingerprint": r.fingerprint,
                   "created": r.created}
        else:
            content = curation.curation_file(engine, args.key)
            if args.out:
                with open(args.out, "wb") as f:
                    f.write(content)
                out = {"written": args.out, "bytes": len(content)}
            else:
                sys.stdout.write(content.decode("utf-8"))
                return 0
    except (curation.CurationRefused, UnsealedVersion) as refused:
        print(f"error: {refused}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
