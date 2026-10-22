"""The pilot's Extractor: a structured model call per document, then a ChatExtract-style verification call (PRD v1.2
R4; owner, 2026-10-22 and 2026-10-23; registers 'pilot_extractor_models', 'pilot_extractor_settings').

Two document invocations per document, each the Extractor's on the same parsed document, in no run:
1. extract: reads the parsed document and the reading sections of the evidence specification (the access layer's
   'parsed_document' and 'extraction_spec'); its answer is stored as its own extraction output, raw and hashed, with
   no candidates and no S0 (method step 'extract');
2. verify: reads the same two and its own draft ('extraction_draft'), and answers yes / no / cannot tell, with a
   quote, for every value and link; its answer is stored raw and hashed (method step 'verify'), and the verified
   records are frozen as S0 on that output (owner, Q-A: S0 is the verified result; both raw outputs are kept).

Verification never drops anything: a value or link answered 'no' or 'cannot tell', or not answered, keeps its value
and gets an ambiguity note quoting the verifier. Anything code could not convert from the answer (a second value for
the same field in one record, a link naming a value the record lacks, a malformed provenance) is listed in the
stored method's 'conversion' list, never silently repaired. Nothing here reads the compilation; every model call is
reserved before it is sent (per-document cap) and recorded."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from hypocurate.access.dispatch import bind_invocation
from hypocurate.db.models import LINK_KINDS, VALUE_FIELDS
from hypocurate.db.retry import run_transaction
from hypocurate.pipeline.agents import libraries
from hypocurate.pipeline.agents.interface import call_agent
from hypocurate.pipeline.agents.settings import ensure_setting, extractor_variant, recorded
from hypocurate.pipeline.extraction import s0
from hypocurate.pipeline.extraction.interface import (THIS_PAPER, CandidateRecord, ExtractionResult, Link,
                                                      ParsedDocument, Provenance, Value)

NAME, VERSION = "pilot_extractor", "1"
EXTRACT_FIELDS = ("parsed_document", "extraction_spec")
VERIFY_FIELDS = ("parsed_document", "extraction_spec", "extraction_draft")
ANSWERS = ("yes", "no", "cannot tell")
NOTE_MAX = 600
CANNOT_TELL_STOP = Decimal("0.5")  # owner, 2026-10-23: stop and ask above half of the values on the first paper
DOCUMENT_STOP_USD = Decimal("1")   # owner, 2026-10-23: stop and ask if any single document costs more


def stop_reasons(run: "DocumentRun") -> list[str]:
    """The owner's stop rules (2026-10-23), checked after every document; any reason means: stop and ask."""
    out = []
    if run.cost > DOCUMENT_STOP_USD:
        out.append(f"the document cost ${run.cost} (more than ${DOCUMENT_STOP_USD})")
    share = run.cannot_tell_share
    if share is not None and share > CANNOT_TELL_STOP:
        out.append(f"verification answered 'cannot tell' for {run.verified.cannot_tell} of {run.verified.values} values")
    return out
_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.S)


# --- what the model sees -----------------------------------------------------------------------------------------

def render_document(doc: Mapping[str, Any]) -> str:
    """The parsed document as text: every text block as '[page p, text i]' and every table row as
    '[page p, table t, row r]', so a provenance can name exactly what it cites."""
    lines = [f"(pages: {doc['pages']})"]
    for t in doc.get("texts") or []:
        lines.append(f"[page {t['page']}, text {t['index']}] {t['text']}")
    for table in doc.get("tables") or []:
        caption = f" {table['caption']}" if table.get("caption") else ""
        lines.append(f"[page {table['page']}, table {table['index']}]{caption}")
        for r, row in enumerate(table.get("rows") or []):
            lines.append(f"[page {table['page']}, table {table['index']}, row {r}] " + " | ".join(row))
    return "\n".join(lines)


def render_spec(spec: Mapping[str, Any]) -> str:
    return json.dumps(spec["sections"], sort_keys=True, ensure_ascii=False, indent=1)


def signatures(step: str, instruction: str):
    _, dspy = libraries.load()
    if step == "extract":
        class ExtractSignature(dspy.Signature):
            document: str = dspy.InputField(desc="The paper: text blocks and table rows, each with its page and indexes.")
            specification: str = dspy.InputField(desc="What to read (the evidence specification's reading sections).")
            note: str = dspy.InputField(desc="'none', or a note about your previous answer.")
            records: str = dspy.OutputField(desc="One JSON object {\"records\": [...]} matching the output schema.")
        return ExtractSignature.with_instructions(instruction)

    class VerifySignature(dspy.Signature):
        document: str = dspy.InputField(desc="The paper: text blocks and table rows, each with its page and indexes.")
        specification: str = dspy.InputField(desc="What was to be read (the evidence specification's reading sections).")
        draft: str = dspy.InputField(desc="The draft list of observations to check, as JSON.")
        note: str = dspy.InputField(desc="'none', or a note about your previous answer.")
        checks: str = dspy.OutputField(desc="One JSON object {\"checks\": [...]} with one entry per value and link.")
    return VerifySignature.with_instructions(instruction)


# --- reading the answers -----------------------------------------------------------------------------------------

def parse_json(text_: str) -> Any:
    body = text_.strip()
    fenced = _FENCE.match(body)
    if fenced:
        body = fenced.group(1)
    try:
        return json.loads(body)
    except ValueError:
        return None


def extract_problems(data: Any) -> list[str]:
    """What makes an extraction answer unreadable (the output schema's shape, checked by code)."""
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        return ["the answer is not one JSON object with a 'records' list"]
    problems = []
    for i, r in enumerate(data["records"]):
        if not isinstance(r, dict) or not isinstance(r.get("values"), list) or not isinstance(r.get("links"), list):
            problems.append(f"record {i}: needs 'values' and 'links' lists")
            continue
        if not isinstance(r.get("reported_from"), str) or not r["reported_from"].strip():
            problems.append(f"record {i}: needs 'reported_from' ('this paper' or the citation)")
        for j, v in enumerate(r["values"]):
            if not isinstance(v, dict) or v.get("field") not in VALUE_FIELDS or not str(v.get("text") or "").strip():
                problems.append(f"record {i}, value {j}: needs a known 'field' and a non-empty 'text'")
    return problems[:20]


def check_extract(outputs: Mapping[str, str]) -> str | None:
    problems = extract_problems(parse_json(outputs["records"]))
    check_extract.last_reason = "; ".join(problems) if problems else None
    check_extract.last_problems = problems
    return "malformed" if problems else None


def check_verify(outputs: Mapping[str, str]) -> str | None:
    data = parse_json(outputs["checks"])
    ok = isinstance(data, dict) and isinstance(data.get("checks"), list) and all(
        isinstance(c, dict) and isinstance(c.get("record"), int) and isinstance(c.get("item"), str)
        and str(c.get("answer", "")).strip().casefold() in ANSWERS for c in data["checks"])
    check_verify.last_reason = None if ok else ("the answer is not one JSON object with a 'checks' list whose entries "
                                                "name a record, an item and an answer yes, no or cannot tell")
    check_verify.last_problems = [] if ok else [check_verify.last_reason]
    return None if ok else "malformed"


for _f in (check_extract, check_verify):
    _f.last_reason, _f.last_problems = None, []


def _number(text_: str) -> Decimal | None:
    try:
        return Decimal(text_.strip())
    except (InvalidOperation, AttributeError):
        return None


def _provenance(raw: Any, where: str, conversion: list[str]) -> Provenance | None:
    if not isinstance(raw, dict):
        return None
    try:
        return Provenance(page=int(raw["page"]), snippet=str(raw.get("snippet") or ""),
                          table_index=raw.get("table_index"), row_index=raw.get("row_index"),
                          sentence=raw.get("sentence") or None)
    except (KeyError, TypeError, ValueError) as e:
        conversion.append(f"{where}: provenance not usable ({type(e).__name__}: {str(e)[:120]})")
        return None


def _note(*parts: str | None) -> str | None:
    joined = "; ".join(p for p in parts if p)
    return joined[:NOTE_MAX] if joined else None


@dataclass
class Verified:
    records: list[CandidateRecord]
    conversion: list[str]
    answers: dict = field(default_factory=dict)  # counts of yes / no / cannot tell / not answered, values and links
    values: int = 0
    cannot_tell: int = 0


def verified_records(draft: Mapping[str, Any], checks: list[dict]) -> Verified:
    """The draft's records with the verifier's answers applied as ambiguity notes; nothing dropped."""
    by_item = {}
    for c in checks:
        by_item[(c["record"], c["item"].strip())] = (str(c["answer"]).strip().casefold(), str(c.get("quote") or "")[:300])
    conversion: list[str] = []
    counts: dict[str, int] = {}
    out, n_values, n_cannot = [], 0, 0

    def verdict(i: int, item: str) -> tuple[str, str | None]:
        answer, quote = by_item.get((i, item), ("not answered", None))
        counts[answer] = counts.get(answer, 0) + 1
        if answer == "yes":
            return answer, None
        return answer, f"verification: {answer}" + (f': "{quote}"' if quote else "")

    for i, r in enumerate(draft["records"]):
        values, seen = [], {}
        for j, v in enumerate(r["values"]):
            name = v["field"]
            prov = _provenance(v.get("provenance"), f"record {i}, value {j} ({name})", conversion)
            answer, vnote = verdict(i, name)
            n_values += 1
            n_cannot += answer == "cannot tell"
            note = _note(v.get("ambiguity_note"), vnote)
            if name in seen:  # one value per field in an observation (the database's rule): the first is kept, flagged
                conversion.append(f"record {i}: a second '{name}' ({str(v['text'])[:80]!r}) was not stored")
                k = seen[name]
                values[k] = Value(values[k].field, values[k].text, values[k].number, values[k].unit,
                                  values[k].definition, values[k].provenance,
                                  _note(values[k].ambiguity_note, f"the extractor gave more than one {name}"))
                continue
            seen[name] = len(values)
            text_ = str(v["text"]).strip()
            values.append(Value(name, text_, _number(text_), v.get("unit") or None, v.get("definition") or None,
                                prov, note))
        links = []
        for j, l in enumerate(r["links"]):
            if not isinstance(l, dict):
                conversion.append(f"record {i}, link {j}: not an object")
                continue
            a, b = str(l.get("from_field") or ""), str(l.get("to_field") or "")
            if a not in seen or b not in seen or a == b:
                conversion.append(f"record {i}, link {j}: names a value the record lacks ({a} - {b}); not stored")
                continue
            kind = l.get("kind") if l.get("kind") in LINK_KINDS else None
            prov = _provenance(l.get("provenance"), f"record {i}, link {j}", conversion)
            _, lnote = verdict(i, f"link:{a}-{b}")
            links.append(Link(a, b, kind, prov if kind else None,
                              _note(l.get("ambiguity_note"), None if kind else "the link's kind is not one of the "
                                    "listed kinds", lnote)))
        out.append(CandidateRecord(tuple(values), tuple(links), str(r.get("reported_from") or THIS_PAPER).strip()))
    return Verified(out, conversion, counts, n_values, n_cannot)


# --- one document --------------------------------------------------------------------------------------------------

@dataclass
class DocumentRun:
    parse_id: int
    extract_invocation: int | None = None
    verify_invocation: int | None = None
    draft_output_id: int | None = None
    frozen: s0.Frozen | None = None
    failure: str | None = None
    verified: Verified | None = None
    cost: Decimal = Decimal("0")
    calls: int = 0

    @property
    def cannot_tell_share(self) -> Decimal | None:
        if not self.verified or not self.verified.values:
            return None
        return Decimal(self.verified.cannot_tell) / Decimal(self.verified.values)


def _invocation(engine: Engine, parse_id: int, setting: int) -> int:
    def write(conn: Connection):
        inv = conn.execute(text("INSERT INTO agent_invocation (scope, role, agent_setting_id) "
                                "VALUES ('document', 'extractor', :a) RETURNING id"), dict(a=setting)).scalar_one()
        conn.execute(text("INSERT INTO document_invocation (invocation_id, document_parse_id) VALUES (:i, :p)"),
                     dict(i=inv, p=parse_id))
        return inv
    return run_transaction(engine, write)


def _call(engine, invocation, step, inputs, client_options):
    s = recorded(engine, invocation)
    return call_agent(engine, invocation, signatures(step, s["instruction"]), inputs, model=s["model"],
                      max_tokens=s["limits"]["max_tokens"], max_output_chars=s["limits"]["max_output_chars"],
                      lm_options={"reasoning_effort": s["settings"]["reasoning_effort"]},
                      client_options=client_options, check=check_extract if step == "extract" else check_verify)


def _store_raw(engine: Engine, document: ParsedDocument, invocation: int, method_json: dict, raw: str,
               status: str) -> int:
    import hashlib

    def write(conn: Connection):
        return conn.execute(text(
            "INSERT INTO extraction_output (document_parse_id, parse_sha256, method, status, raw_output, raw_sha256, "
            "invocation_id) VALUES (:p, :h, CAST(:m AS jsonb), :s, :r, :rh, :i) RETURNING id"),
            dict(p=document.parse_id, h=document.parse_sha256, m=json.dumps(method_json, sort_keys=True), s=status,
                 r=raw, rh=hashlib.sha256(raw.encode("utf-8")).hexdigest(), i=invocation)).scalar_one()
    return run_transaction(engine, write)


def _spent(engine: Engine, invocations: list[int]) -> tuple[Decimal, int]:
    with engine.connect() as conn:
        row = conn.execute(text("SELECT coalesce(sum(coalesce(cost, max_cost)), 0), count(*) FROM model_call "
                                "WHERE invocation_id = ANY(:i)"), dict(i=invocations)).one()
    return Decimal(row[0]), int(row[1])


def extract_document(engine: Engine, parse_id: int, spec_name: str = "H1_v1",
                     client_options: Mapping[str, Any] | None = None) -> DocumentRun:
    """Extract, verify, store both raw outputs and freeze S0 for one parsed document."""
    run = DocumentRun(parse_id)
    with engine.connect() as conn:
        document = ParsedDocument.load(conn, parse_id)
    extract_setting = ensure_setting(engine, "extractor", extractor_variant("extract", spec_name))
    run.extract_invocation = _invocation(engine, parse_id, extract_setting)
    access = bind_invocation(engine, run.extract_invocation)
    data = {f: access.get(f) for f in EXTRACT_FIELDS}
    inputs = {"document": render_document(data["parsed_document"]), "specification": render_spec(data["extraction_spec"])}
    first = _call(engine, run.extract_invocation, "extract", inputs, client_options)
    base = {"method": "model_call", "name": NAME, "version": VERSION, "model": recorded(engine, run.extract_invocation)["model"],
            "prompt_version": extractor_variant("extract", spec_name)["settings"]["prompt_version"],
            "evidence_spec": data["extraction_spec"]["key"] + " v" + data["extraction_spec"]["version"],
            "evidence_spec_sha256": data["extraction_spec"]["sha256"]}
    if first.failure is not None:
        run.draft_output_id = _store_raw(engine, document, run.extract_invocation,
                                         base | {"step": "extract", "failure": first.failure}, "", "failed")
        run.failure = f"extract: {first.failure}"
        run.cost, run.calls = _spent(engine, [run.extract_invocation])
        return run
    run.draft_output_id = _store_raw(engine, document, run.extract_invocation, base | {"step": "extract"},
                                     first.outputs["records"], "returned")

    verify_setting = ensure_setting(engine, "extractor", extractor_variant("verify", spec_name))
    run.verify_invocation = _invocation(engine, parse_id, verify_setting)
    access = bind_invocation(engine, run.verify_invocation)
    vdata = {f: access.get(f) for f in VERIFY_FIELDS}
    draft = parse_json(vdata["extraction_draft"]["raw_output"])
    second = _call(engine, run.verify_invocation, "verify",
                   {"document": render_document(vdata["parsed_document"]),
                    "specification": render_spec(vdata["extraction_spec"]),
                    "draft": json.dumps(draft, sort_keys=True, ensure_ascii=False)}, client_options)
    if second.failure is not None:
        _store_raw(engine, document, run.verify_invocation,
                   base | {"step": "verify", "draft_output_id": run.draft_output_id, "failure": second.failure},
                   "", "failed")
        run.failure = f"verify: {second.failure}"
        run.cost, run.calls = _spent(engine, [run.extract_invocation, run.verify_invocation])
        return run
    checks = parse_json(second.outputs["checks"])["checks"]
    run.verified = verified_records(draft, checks)
    m = base | {"step": "verify", "draft_output_id": run.draft_output_id, "draft_raw_sha256":
                vdata["extraction_draft"]["raw_sha256"], "conversion": run.verified.conversion,
                "verification": run.verified.answers}
    result = ExtractionResult(MethodJson(m), second.outputs["checks"], tuple(run.verified.records),
                              invocation_id=run.verify_invocation)
    run.frozen = s0.store_and_freeze(engine, document, result)
    run.cost, run.calls = _spent(engine, [run.extract_invocation, run.verify_invocation])
    return run


@dataclass(frozen=True)
class MethodJson:
    """A method whose stored form carries the pilot's full record (step, draft, conversion, verification counts)."""
    data: dict

    def to_json(self) -> dict:
        return dict(self.data)
