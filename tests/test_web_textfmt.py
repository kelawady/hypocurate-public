"""Step 10a (owner's review of the screenshots, 2026-10-11): the Analyst's text showed raw ** and |---|. It is shown in a
small safe subset of Markdown (bold, lists, simple tables), everything escaped first; exponents are superscripts on the
screens only."""
from __future__ import annotations

from hypocurate.web.textfmt import model_text, units


def test_bold_lists_and_a_simple_table_are_rendered_and_no_raw_signs_remain():
    text = ("The claim is **supported** here.\n\n- first point\n- second **point**\n\n1. one\n2. two\n\n"
            "| Source | Estimate |\n|---|---:|\n| MPEA | 424.1 MPa·µm^0.5 |\n| Texas A&M | 1173.3 |")
    out = str(model_text(text))
    assert "<p>The claim is <strong>supported</strong> here.</p>" in out
    assert "<ul><li>first point</li><li>second <strong>point</strong></li></ul>" in out
    assert "<ol><li>one</li><li>two</li></ol>" in out
    assert "<thead><tr><th>Source</th><th>Estimate</th></tr></thead>" in out
    assert "<td>424.1 MPa·µm<sup>0.5</sup></td>" in out and "<td>Texas A&amp;M</td>" in out
    assert "**" not in out and "---" not in out and "|" not in out


def test_everything_the_model_writes_is_escaped():
    out = str(model_text('<script>alert(1)</script> **<b>x</b>** <img src=x onerror=y> & "q"\n- <i>item</i>'))
    assert "<script>" not in out and "<b>" not in out and "<img" not in out and "<i>" not in out
    assert "&lt;script&gt;" in out and "<strong>&lt;b&gt;x&lt;/b&gt;</strong>" in out and "&amp;" in out
    assert "<li>&lt;i&gt;item&lt;/i&gt;</li>" in out


def test_a_heading_mark_is_dropped_and_other_signs_stay_as_text():
    out = str(model_text("## Result\nA * B and 2 ^ x"))
    assert out == "<p>Result A * B and 2 ^ x</p>"


def test_units_escapes_and_writes_exponents_as_superscripts():
    assert str(units("k = 424.9 MPa·µm^0.5 and d^-1/2 <x>")) == \
        "k = 424.9 MPa·µm<sup>0.5</sup> and d<sup>-1/2</sup> &lt;x&gt;"
