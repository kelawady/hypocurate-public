"""Step 10b: the Help page and the information buttons (PRD 9.7; criterion 14.5): one glossary file; every entry has a
button on some screen and appears on the Help page; every key a template uses exists; no template repeats an
explanation's text; the Help page can be searched."""
from __future__ import annotations

import html
import pathlib
import re

import pytest

from hypocurate.db.engine import make_engine
from hypocurate.web import app as web_app
from hypocurate.web import glossary
from test_web_runs import make_client, plain, signed_in

TEMPLATES = pathlib.Path(web_app.__file__).resolve().parent / "templates"


@pytest.fixture
def own(migrated_database):
    e = make_engine(migrated_database)
    yield e, migrated_database
    e.dispose()


def used_keys() -> set[str]:
    keys = set(web_app.STATEMENT_TERMS)
    for t in TEMPLATES.glob("*.html"):
        keys |= set(re.findall(r'(?:info|term)\("([a-z_]+)"\)', t.read_text(encoding="utf-8")))
    return keys


def test_every_glossary_entry_has_a_button_and_every_button_has_an_entry():
    keys = set(glossary.by_key())
    assert used_keys() == keys, {"no button": sorted(keys - used_keys()), "no entry": sorted(used_keys() - keys)}


def test_no_template_repeats_an_explanations_text():
    for t in TEMPLATES.glob("*.html"):
        source = t.read_text(encoding="utf-8")
        for e in glossary.entries():
            assert e["text"][:60] not in source, (t.name, e["key"])


def test_the_help_page_lists_every_explanation_and_where_it_appears(own):
    engine, url = own
    page = signed_in(engine, url).get("/help").text
    shown = plain(page)
    assert f"{len(glossary.entries())} of {len(glossary.entries())} explanations" in shown
    for e in glossary.entries():
        assert html.escape(e["text"], quote=False) in page.replace("&#39;", "'"), e["key"]
        assert f'id="{e["key"]}"' in page


def test_the_help_page_can_be_searched(own):
    engine, url = own
    shown = plain(signed_in(engine, url).get("/help?q=spending cap").text)
    assert "Spending cap" in shown and "Checkpoint 1: rules lock" not in shown
    assert "contain “spending cap”" in shown


def test_the_help_page_needs_the_login(own):
    engine, url = own
    assert make_client(engine, url).get("/help").status_code == 303
