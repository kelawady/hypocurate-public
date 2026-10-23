"""Sprint 2 pilot, R15 (P9): costs per document and per run, and the owner's time, from stored rows only."""
from __future__ import annotations

import json
from decimal import Decimal

from sqlalchemy import text

import stub_provider as sp
from hypocurate.pipeline import costs
from hypocurate.pipeline import reconcile as rc
from test_reconcile import DOI, frozen, stub  # noqa: F401 (fixtures)


def test_a_documents_calls_tokens_and_dollars_come_from_its_model_call_rows(db, frozen, stub):  # noqa: F811
    f, _ = frozen
    stub.queue(sp.reply(sp.fields(mappings=json.dumps({"mappings": []})), input_tokens=3000, output_tokens=500))
    run = rc.reconcile(db, f.output_id, client_options=sp.client_options(stub))
    with db.connect() as conn:
        (row,) = costs.per_document(conn)
        stored = conn.execute(text("SELECT sum(cost), sum(input_tokens), sum(output_tokens) FROM model_call")).one()
        conn_report = costs.report(conn)
    assert (row["doi_key"], row["role"], row["calls"], row["failed_calls"]) == ("doi:" + DOI, "reconciler", 1, 0)
    assert (row["cost_usd"], row["input_tokens"], row["output_tokens"]) == (Decimal(stored[0]), stored[1], stored[2])
    assert row["cost_usd"] == run.cost > 0 and row["wall_seconds"] >= 0
    assert conn_report["totals"]["documents_cost_usd"] == row["cost_usd"]


def test_the_owners_time_is_read_from_the_time_log(db):
    with db.begin() as conn:
        for m in (12, 5):
            conn.execute(text("INSERT INTO owner_time_log (doi_key, activity, minutes, logged_by) VALUES "
                              "(:k, 'repair_fetch', :m, 'K. El-Awady')"), dict(k="doi:" + DOI, m=m))
    with db.connect() as conn:
        assert costs.owner_time(conn) == [{"activity": "repair_fetch", "doi_key": "doi:" + DOI, "minutes": 17,
                                           "entries": 2}]
