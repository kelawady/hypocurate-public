"""Step 10b: the plot (PRD 9.4; owner's answer of 2026-10-11: raw values, marker shape by source, crosses for
sensitivity-only records, hollow for records not used, one line segment per alloy in the test with the stored slope).

The check that matters most: the points the plot marks as used in the test, grouped by the plot's alloys, give back
the stored slope when fitted test-side (least squares with one baseline per alloy, numpy) - so the plot shows the fit's
own records and alloys, and its lines are the fit's lines.
"""
from __future__ import annotations

import re

import numpy as np
import pytest

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from conftest import _create, _drop, url_for
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import plot, queries, run_view
from test_web_runs import plain, signed_in


def completed(engine, stub, claim=to.FCC_CLAIM, sources=("mpea", "tamu_fcc"), sufficiency="fixed_minimum",
              fixed_plan=True):
    stub.respond(to.responder(to.BCC if claim == to.BCC_CLAIM else None))
    q = queries.create(engine, claim, sources, sufficiency=sufficiency)
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id, fixed_plan=fixed_plan)
    assert to.run(engine, rid, stub).status == "completed"
    return rid


@pytest.fixture(scope="module")
def world(admin, database_url, template_database):
    name = _create(admin, "hypocurate_t", template=template_database)
    url = url_for(database_url, name)
    engine = make_engine(url)
    stub = sp.StubProvider()
    try:
        pw.registered(engine, ("mpea", "tamu_fcc"))
        runs = {"reference": completed(engine, stub),
                "withheld": completed(engine, stub, sources=("tamu_fcc",)),
                "coefficient_only": completed(engine, stub, sources=("tamu_fcc",), sufficiency="use_available"),
                "nothing_frozen": completed(engine, stub, to.BCC_CLAIM, fixed_plan=False),
                "open": to.dispatched(engine, fixed_plan=True)}
        yield engine, url, runs
    finally:
        stub.close()
        engine.dispose()
        _drop(admin, name)


def fitted_slope(points) -> float:
    """Test-side least squares with one baseline per alloy (independent of the statistics module)."""
    alloys = sorted({p["alloy"] for p in points})
    X = np.zeros((len(points), len(alloys) + 1))
    for i, p in enumerate(points):
        X[i, alloys.index(p["alloy"])] = 1.0
        X[i, -1] = p["x"]
    return float(np.linalg.lstsq(X, np.array([p["y"] for p in points]), rcond=None)[0][-1])


def test_the_used_points_fit_back_to_the_stored_slope_and_each_alloy_gets_one_line(world):
    engine, _, runs = world
    d = plot.data(engine, runs["reference"])
    used = [p for p in d["points"] if p["use"] == plot.USED]
    assert len(used) == 97 and len({p["alloy"] for p in used}) == 22  # the reference test: 97 records, 22 alloys
    stored = run_view.show(engine, runs["reference"])["results"][0]["estimate"]
    assert d["k"] == stored
    assert abs(fitted_slope(used) - stored) <= 1e-9 * abs(stored)
    assert len(d["segments"]) == 22
    for s in d["segments"]:  # every line has the stored slope
        assert abs((s["y1"] - s["y0"]) / (s["x1"] - s["x0"]) - stored) <= 1e-9 * abs(stored)


def test_records_are_marked_by_how_they_were_used_and_shaped_by_source(world):
    engine, _, runs = world
    d = plot.data(engine, runs["reference"])
    uses = {p["use"] for p in d["points"]}
    assert uses == {plot.USED, plot.SENSITIVITY_ONLY, plot.NOT_USED}
    assert [s["key"] for s in d["sources"]] == ["mpea", "tamu_fcc"] and d["sources"][0]["shape"] != d["sources"][1]["shape"]
    svg = str(plot.svg(d))
    assert svg.count('class="fit"') == 22 and svg.count("<circle") + svg.count("<path") + svg.count("<rect") >= len(d["points"])


def test_below_the_minimums_there_are_points_but_no_lines_and_the_reason(world):
    engine, _, runs = world
    d = plot.data(engine, runs["withheld"])
    assert d["plot"] and d["points"] and d["segments"] == [] and d["k"] is None
    assert d["reason"] == "No fitted lines: the minimums were not met, so no estimate is shown."
    assert d["reason"] in plot.legend(d)


def test_a_coefficient_only_result_draws_its_lines_with_the_stored_coefficient(world):
    engine, _, runs = world
    d = plot.data(engine, runs["coefficient_only"])
    stored = run_view.show(engine, runs["coefficient_only"])["results"][0]["estimate"]
    assert d["k"] == stored and d["segments"]
    used = [p for p in d["points"] if p["use"] == plot.USED]
    assert abs(fitted_slope(used) - stored) <= 1e-9 * abs(stored)


def test_with_no_dataset_frozen_there_is_no_plot_and_the_reason_is_stated(world):
    engine, _, runs = world
    d = plot.data(engine, runs["nothing_frozen"])
    assert d["plot"] is False and d["reason"] == "No plot: no dataset was frozen, so nothing was tested."


def test_the_plot_states_its_format_and_the_code_version_that_built_it(world, monkeypatch):
    engine, _, runs = world
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    assert plot.data(engine, runs["reference"])["version"] == "Plot format 1; built by code version unknown."
    monkeypatch.setenv("RENDER_GIT_COMMIT", "0123abcd")
    assert plot.data(engine, runs["reference"])["version"] == "Plot format 1; built by code version 0123abcd."


def test_the_run_page_shows_the_plot_of_a_completed_run_only(world):
    engine, url, runs = world
    c = signed_in(engine, url)
    page = c.get(f"/runs/{runs['reference']}").text
    assert '<svg class="plot"' in page and "built by code version" in plain(page)
    assert "each with the stored slope k = 424.9 MPa·µm^0.5" in plain(page)
    assert "No plot: no dataset was frozen" in plain(c.get(f"/runs/{runs['nothing_frozen']}").text)
    assert '<svg class="plot"' not in c.get(f"/runs/{runs['open']}").text


def test_the_plots_text_is_never_drawn_below_12_px():
    """Owner's addition 6: the SVG's text is FONT units in a viewBox W wide, and the plot is never narrower than the
    stylesheet's min-width, so FONT * min-width / W >= 12."""
    import pathlib
    css = (pathlib.Path(plot.__file__).resolve().parents[1] / "web" / "static" / "style.css").read_text()
    min_width = float(re.search(r"svg\.plot \{[^}]*min-width: (\d+)px", css).group(1))
    assert plot.FONT * min_width / plot.W >= 12
    svg = str(plot.svg({"points": [{"x": 0.5, "y": 300.0, "source": "mpea", "use": plot.USED}], "segments": [],
                        "sources": [{"key": "mpea", "name": "MPEA", "shape": "circle"}]}))
    sizes = [float(x) for x in re.findall(r'font-size="([\d.]+)"', svg)]
    assert sizes and min(sizes) >= plot.FONT
