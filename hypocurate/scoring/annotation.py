"""Loads an annotation file (PRD v1.2 R7, R8): the template's columns exactly, one row per observation, each row's
identity computed by the one R-identity function (`pipeline.extraction.identity`).

A file is refused whole, with every problem listed, when its columns differ from the template's, or any row lacks a
paper DOI, an annotator, or both a specimen label and an observation location (the identity needs one). Wholly blank
rows are skipped and counted. Nothing is corrected: cells are stored as written (strings), with the identity code
computed beside them."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from hypocurate.db.retry import run_transaction
from hypocurate.pipeline.extraction.identity import IdentityError, identity
from hypocurate.scoring.template import NAMES, TEMPLATE_VERSION
from hypocurate.sources.normalize import doi_group_key

FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,199}[.](xlsx|csv)$")


class AnnotationRefused(ValueError):
    def __init__(self, problems: list[str]):
        super().__init__("the annotation file is refused: " + "; ".join(problems[:20]))
        self.problems = problems


@dataclass(frozen=True)
class Row:
    number: int  # the row's number in the sheet (the header is row 1)
    cells: dict
    doi_key: str
    identity: dict
    identity_key: str
    annotator: str
    minutes: int | None


def _cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return " ".join(str(v).split())


def read_table(filename: str, content: bytes) -> list[list[str]]:
    if filename.lower().endswith(".csv"):
        return [[_cell(c) for c in row] for row in csv.reader(io.StringIO(content.decode("utf-8-sig")))]
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    if "Annotation" not in wb.sheetnames:
        raise AnnotationRefused(["no sheet named 'Annotation'"])
    return [[_cell(c) for c in row] for row in wb["Annotation"].iter_rows(values_only=True)]


def parse(filename: str, content: bytes) -> tuple[list[Row], int]:
    """The rows and the number of wholly blank rows skipped; refuses the file whole on any problem."""
    if not FILENAME.match(filename):
        raise AnnotationRefused([f"file name {filename!r}: letters, digits, '._ -', ending .xlsx or .csv"])
    table = read_table(filename, content)
    if not table:
        raise AnnotationRefused(["the file is empty"])
    header = [h for h in table[0]]
    while header and header[-1] == "":
        header.pop()
    if tuple(header) != NAMES:
        missing, extra = [n for n in NAMES if n not in header], [h for h in header if h not in NAMES]
        raise AnnotationRefused([f"the columns differ from the template's (missing {missing}, extra {extra}, "
                                 f"or out of order)"])
    rows, problems, blank = [], [], 0
    for number, raw in enumerate(table[1:], start=2):
        cells = dict(zip(NAMES, (raw + [""] * len(NAMES))[:len(NAMES)]))
        if not any(cells.values()):
            blank += 1
            continue
        key = doi_group_key(cells["paper_doi"]) if cells["paper_doi"] else None
        if key is None:
            problems.append(f"row {number}: no paper_doi")
        if not cells["annotator"]:
            problems.append(f"row {number}: no annotator")
        minutes = None
        if cells["minutes"]:
            try:
                minutes = int(float(cells["minutes"]))
            except ValueError:
                problems.append(f"row {number}: minutes {cells['minutes']!r} is not a number")
        try:
            ident = identity(cells["paper_doi"], cells["alloy_as_written"], cells["processing_state"],
                             cells["test_type"], cells["test_temperature"], cells["specimen_label"],
                             cells["observation_location"], composition=cells["composition_at_pct"],
                             test_temperature_unit=cells["test_temperature_unit"])
        except IdentityError as e:
            problems.append(f"row {number}: {e}")
            continue
        if key is not None and cells["annotator"]:
            rows.append(Row(number, cells, key, ident.to_json(), ident.key, cells["annotator"], minutes))
    if problems:
        raise AnnotationRefused(problems)
    return rows, blank


def load(engine: Engine, filename: str, content: bytes, loaded_by: str) -> tuple[int, int, int]:
    """Stores the file and its rows in one transaction. Returns (file id, rows, blank rows skipped)."""
    rows, blank = parse(filename, content)

    def write(conn: Connection):
        fid = conn.execute(text(
            "INSERT INTO annotation_file (filename, content, sha256, template_version, loaded_by) "
            "VALUES (:f, :c, :h, :v, :by) RETURNING id"),
            dict(f=filename, c=content, h=hashlib.sha256(content).hexdigest(), v=TEMPLATE_VERSION,
                 by=loaded_by)).scalar_one()
        for r in rows:
            conn.execute(text(
                "INSERT INTO annotation_row (annotation_file_id, row_number, doi_key, identity, identity_key, cells, "
                "annotator, minutes) VALUES (:f, :n, :k, CAST(:i AS jsonb), :ik, CAST(:c AS jsonb), :a, :m)"),
                dict(f=fid, n=r.number, k=r.doi_key, i=json.dumps(r.identity, sort_keys=True), ik=r.identity_key,
                     c=json.dumps(r.cells, sort_keys=True, ensure_ascii=False), a=r.annotator, m=r.minutes))
        return fid
    return run_transaction(engine, write), len(rows), blank
