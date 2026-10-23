"""Sprint 2 pilot, merge review C4 (2026-10-23): a re-extraction of a paper after its review sees none of the review.
Planted in the database before the second extraction of the same parsed document: a Reconciler mapping (subject, quote,
proposal), a person's decision with its reason, an Auditor finding, a value correction, and the compilation and claim
of test_extractor's planted world; none of their text reaches either outbound request of the second extraction (the
verification call reads only its own new draft)."""
from __future__ import annotations

import json

from sqlalchemy import text

import stub_provider as sp
from hypocurate.pipeline.extraction import model_extractor as mx
from test_extractor import (ALL_YES, CLAIM, PLANTED_RECORD, PLANTED_VALUE, checks, draft, gs_ys_record,  # noqa: F401
                            plant_compilation, stored_parse, stub, w)

PLANTS = ("ZQ-MAPPING-SUBJECT", "ZQ-MAPPING-QUOTE", "ZQ-PROPOSED-9.87", "ZQ-DECISION-REASON", "ZQ-FINDING-DETAIL",
          "ZQ-CORRECTED-321", "ZQ-CORRECTION-REASON")


def test_a_re_extraction_after_review_sees_no_review_reconciler_or_compilation_text(w, db, stub):
    plant_compilation(w)
    parse_id = stored_parse(w)
    stub.queue(sp.reply(sp.fields(records=draft([gs_ys_record()])), input_tokens=4000, output_tokens=900),
               sp.reply(checks(*ALL_YES), input_tokens=5000, output_tokens=400))
    first = mx.extract_document(db, parse_id, "H1_v1", client_options=sp.client_options(stub))
    out = first.frozen.output_id
    with db.begin() as conn:
        obs = conn.execute(text("SELECT id FROM candidate_observation WHERE extraction_output_id = :x"), dict(x=out)).scalar()
        val = conn.execute(text("SELECT id FROM candidate_value WHERE observation_id = :o AND field = 'yield_strength'"),
                           dict(o=obs)).scalar()
        m = conn.execute(text(
            "INSERT INTO reconciler_mapping (extraction_output_id, observation_id, kind, subject, proposed, applied, quote, "
            "mapping_version) VALUES (:x, :o, 'alias_to_composition', 'ZQ-MAPPING-SUBJECT', "
            "'{\"composition\": \"ZQ-PROPOSED-9.87\"}', '{\"ok\": false}', 'ZQ-MAPPING-QUOTE', 'reconcile-v2') RETURNING id"),
            dict(x=out, o=obs)).scalar_one()
        conn.execute(text("INSERT INTO evidence_state_event (object_kind, object_id, extraction_output_id, state, "
                          "by_person, reason) VALUES ('mapping', :m, :x, 'disputed', 'K. El-Awady', 'ZQ-DECISION-REASON')"),
                     dict(m=m, x=out))
        conn.execute(text("INSERT INTO auditor_finding (object_kind, object_id, extraction_output_id, finding_kind, "
                          "consequence, detail, by_person) VALUES ('observation', :o, :x, 'implausible_value', "
                          "'re_extract', 'ZQ-FINDING-DETAIL', 'K. El-Awady')"), dict(o=obs, x=out))
        conn.execute(text("INSERT INTO value_correction (value_id, corrected_text, reason, by_person) VALUES "
                          "(:v, 'ZQ-CORRECTED-321', 'ZQ-CORRECTION-REASON', 'K. El-Awady')"), dict(v=val))
    stub.queue(sp.reply(sp.fields(records=draft([gs_ys_record()])), input_tokens=4000, output_tokens=900),
               sp.reply(checks(*ALL_YES), input_tokens=5000, output_tokens=400))
    second = mx.extract_document(db, parse_id, "H1_v1", client_options=sp.client_options(stub))
    assert second.failure is None and len(stub.requests) == 4
    for request in stub.requests[2:]:
        raw = request["raw"].decode("utf-8")
        for absent in PLANTS + (PLANTED_VALUE, PLANTED_RECORD, CLAIM):
            assert absent not in raw, absent
