"""Step 10a, a5 (owner's condition 1 for a parallel suite, 2026-10-11): no test can see another test's data. The suite
runs serially since the owner's decision of 2026-10-11 (register 'parallel_suite'); these checks keep it ready for a
parallel run.

How it holds: every test that needs tables gets a database of its own, made and dropped by tests/conftest.py
(`empty_database`, `migrated_database`; random names), from a template each pytest process makes for itself (under
xdist, one per worker). These checks keep it that way: databases are made only by conftest's `_create`, with random
names; the one database not made for a test (`DATABASE_URL`'s own) is opened only by the read-only /health and
`check-db` tests; and the serial group names only files that exist.
"""
from __future__ import annotations

import ast
import os
import pathlib
import re

import conftest

TESTS = pathlib.Path(__file__).resolve().parent
# The tests that open DATABASE_URL's own database: /health and `check-db`, which only read (the schema revision).
READS_THE_SHARED_DATABASE = {"test_health.py"}


def test_databases_are_made_only_by_conftest_with_random_names():
    for path in TESTS.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        if path.name in ("conftest.py", "test_parallel_isolation.py"):
            continue
        assert "CREATE DATABASE" not in source.upper(), path.name
    body = (TESTS / "conftest.py").read_text(encoding="utf-8")
    assert 'name = f"{prefix}_{uuid.uuid4().hex[:12]}"' in body  # a fresh random name for every database made


def test_only_the_read_only_health_tests_open_the_shared_database():
    """`database_url` (DATABASE_URL's own database) may be named by a test only to make scratch databases from it
    (`url_for`, `_create`), except in the health tests, which open it to read its schema revision."""
    for path in TESTS.glob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == "make_engine":
                args = [a.id for a in node.args if isinstance(a, ast.Name)]
                if "database_url" in args:
                    assert path.name in READS_THE_SHARED_DATABASE, path.name
        if path.name in READS_THE_SHARED_DATABASE:
            text_ = path.read_text(encoding="utf-8")
            assert not re.search(r"\b(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\b", text_), path.name


def test_each_test_database_is_made_from_a_template_of_this_process(template_database):
    assert re.fullmatch(r"hypocurate_tmpl_[0-9a-f]{12}", template_database), template_database


def test_the_serial_group_names_only_existing_test_files():
    assert conftest.SERIAL_FILES and all((TESTS / name).is_file() for name in conftest.SERIAL_FILES)
