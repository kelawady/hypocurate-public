"""Step 8a review fixes (ChatGPT finding 5; owner's term-check changes a-g, 2026-10-07): the checks on
a Curator proposal's quote, in code (`quotes.check`). The database's own copy of these checks is
tested against this one in tests/test_migrations_step8a.py.

The rules: the quote is found in one documentation file after collapsing runs of whitespace, and it
begins and ends at a word boundary there; 30 to 600 characters; it holds a listed term for the value
as a whole word (case-insensitive, except B2 and L12), after collapsing whitespace and setting aside
"ultimate tensile strength"; for test type, temperature band and test temperature it also holds a
testing word; a test temperature is a complete signed number equal to the value and followed by a
Celsius unit in a form found in the frozen documents ("°C", or LaTeX \\SI{n}{\\degreeCelsius}).

What these tests do not show: that a sentence that passes supports the value. A person decides that.
"""
from __future__ import annotations

import pytest

from hypocurate.pipeline.agents import quotes
from hypocurate.sources.versions import DATA_DIR

PROPOSAL_5 = ("Quasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers indentation "
              "tests provided the HV.")
PROPOSAL_2 = "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system."


def frozen_documents() -> dict[str, str]:
    folder = DATA_DIR / "sources" / "tamu_fcc" / "documentation"
    return {f"documentation/{p.name}": p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.tex"))}


def checked(field, value, quote, document=None):
    """The check's code for a quote that is itself the whole document (so it is always found)."""
    return quotes.check(field, value, quote, {"documentation/notes.md": document if document is not None else quote})


# --- g. the owner's two accepted proposals under the new rules ------------------------------------------

@pytest.mark.parametrize("field, value, quote, line, term", [
    ("test_type", "tension", PROPOSAL_5, 177, "tensile"),
    ("phase_class", "FCC", PROPOSAL_2, 173, "FCC"),
])
def test_the_owners_two_accepted_proposals_still_pass(field, value, quote, line, term):
    result = quotes.check(field, value, quote, frozen_documents())
    assert (result.code, result.located, result.term) == (
        None, quotes.Located("documentation/main.tex", line), term)


# --- a. whole words; case ---------------------------------------------------------------------------------

@pytest.mark.parametrize("field, value, quote, code", [
    ("microstructure", "B2", "The Nb25 alloys were examined by diffraction after annealing.", "term_missing"),
    ("microstructure", "B2", "Ordered B2 precipitates were found after annealing in every alloy.", None),
    ("microstructure", "B2", "Ordered b2 precipitates were found after annealing in every alloy.", "term_missing"),
    ("microstructure", "L12", "Coherent L12 precipitates were found after ageing in every alloy.", None),
    ("microstructure", "L12", "Coherent l12 precipitates were found after ageing in every alloy.", "term_missing"),
    ("microstructure", "FCC", "All alloys showed a single fcc phase after the final anneal.", None),
    ("microstructure", "HCP", "All alloys showed a single hcp phase after the final anneal.", None),
    ("microstructure", "FCC+B2", "Each alloy had an FCC matrix with B2 particles after annealing.", None),
    ("microstructure", "FCC+B2", "Each alloy had an FCC matrix with Nb2 particles after annealing.", "term_missing"),
    ("phase_class", "FCC", "All alloys were designed as fcc solid solutions in this study.", None),
    ("phase_class", "BCC", "All alloys were designed as BCCs and HCPs in this study, then.", "term_missing"),
    ("test_type", "tension", "Specimens were tested after extension of the gauge section by machining.", "term_missing"),
    ("test_type", "tension", "Specimens were tested in tension at a constant crosshead speed.", None),
    ("test_type", "tension", "The ultimate tensile strength was tested for each of the alloys.", "term_missing"),
    ("test_type", "tension", "The ultimate tensile strength and tensile ductility were tested for each.", None),
    ("test_type", "compression", "Cylinders were tested under compressive loading at room temperature.", None),
    ("test_type", "compression", "Cylinders were tested under precompression before the main experiment.",
     "term_missing"),
])
def test_terms_match_whole_words_with_the_stated_case_rules(field, value, quote, code):
    assert checked(field, value, quote).code == code


def test_whitespace_is_collapsed_for_terms_as_for_locating_the_quote():
    quote = "All specimens were tested at room\ntemperature in laboratory air, every time."
    result = checked("test_temperature_band", "room temperature", quote)
    assert (result.code, result.term) == (None, "room temperature")


# --- b. a testing word for test type, temperature band and test temperature -----------------------------

@pytest.mark.parametrize("field, value, quote, code", [
    ("test_temperature_band", "room temperature",
     "The plates were cold rolled at room temperature to a 60% reduction in thickness.", "testing_word_missing"),
    ("test_temperature_band", "room temperature",
     "The plates were deformed at room temperature to a 60% reduction in thickness.", None),
    ("test_type", "tension", "Dog-bone tensile specimens were cut from each plate by machining.", "testing_word_missing"),
    ("test_type", "tension", "Dog-bone specimens were loaded in tension until they broke.", None),
    ("test_type", "tension", "Dog-bone specimens were attested to be tensile by the supplier, sure.",
     "testing_word_missing"),
    ("test_type", "tension", "Specimens were pulled in tension at a strain rate of 0.001 per second.", None),
    ("test_temperature", 25, "Plates were annealed and then cooled to 25 °C in still laboratory air.",
     "testing_word_missing"),
    ("test_temperature", 25, "All the specimens were strained at 25 °C in still laboratory air.", None),
    ("phase_class", "FCC", "The dataset contains 94 FCC alloy conditions in one alloy system.", None),  # not needed
])
def test_test_conditions_need_a_testing_word(field, value, quote, code):
    assert checked(field, value, quote).code == code


# --- c. and finding 5: a test temperature is a complete number with a Celsius unit ------------------------

@pytest.mark.parametrize("value, quote, term", [
    (25, "All the specimens were tested at 25 °C in laboratory air.", "25"),
    (25, "All the specimens were tested at 25°C in laboratory air.", "25"),
    (25, "All the specimens were tested at 25~°C in laboratory air.", "25"),
    (25, "All the specimens were tested at \\SI{25}{\\degreeCelsius} in laboratory air.", "25"),
    (25, "All the specimens were tested at 25.0 °C in laboratory air.", "25.0"),
    (25.5, "All the specimens were tested at 25.5 °C in laboratory air.", "25.5"),
    (-196, "All the specimens were tested at −196 °C in liquid nitrogen.", "−196"),
    (-196, "All the specimens were tested at -196 °C in liquid nitrogen.", "-196"),
    (25, "Tested at 300 °C, and also tested at 25 °C in laboratory air.", "25"),
])
def test_a_temperature_is_the_whole_number_with_its_unit(value, quote, term):
    result = checked("test_temperature", value, quote)
    assert (result.code, result.term) == (None, term)


@pytest.mark.parametrize("value, quote", [
    (25, "All the specimens were tested at −25 °C in laboratory air."),   # another temperature
    (25, "All the specimens were tested at -25 °C in laboratory air."),
    (25, "All the specimens were tested at 25.5 °C in laboratory air."),
    (25, "All the specimens were tested at 125 °C in laboratory air."),
    (25, "All the specimens were tested at 2.25 °C in laboratory air."),
    (25, "All the specimens were tested between 20-25 °C in laboratory air."),  # a range: refused (safe)
    (25, "All the specimens were tested at 25 MPa in laboratory air and more."),  # no unit
    (25, "All the specimens were tested at 25 and then held in laboratory air."),
    (298, "All the specimens were tested at 298 K in laboratory air, as usual."),  # kelvin: refused (f)
    (25, "All the specimens were tested at 25 $^\\circ$C in laboratory air."),  # a form not in the documents
    (25, "All the specimens were tested at \\SI{125}{\\degreeCelsius} in laboratory air."),
    (-196, "All the specimens were tested at 196 °C in laboratory air, as usual."),
])
def test_another_number_or_no_celsius_unit_is_refused(value, quote):
    assert checked("test_temperature", value, quote).code == "term_missing"


# --- d. spelling variants -------------------------------------------------------------------------------------

@pytest.mark.parametrize("field, value, phrase", [
    ("phase_class", "FCC", "face-centred cubic"), ("phase_class", "FCC", "face centered cubic"),
    ("phase_class", "FCC", "face-centered-cubic"), ("phase_class", "FCC", "face centred cubic"),
    ("phase_class", "BCC", "body-centred cubic"), ("phase_class", "BCC", "body centered cubic"),
    ("phase_class", "BCC", "body-centered-cubic"),
    ("test_temperature_band", "cryogenic", "liquid helium"),
])
def test_spelling_variants_are_listed(field, value, phrase):
    quote = f"All the alloys tested here were {phrase} in the study, without exception."
    assert checked(field, value, quote).code is None


# --- e. at most 600 characters, beginning and ending at a word boundary --------------------------------------

def test_a_quote_is_at_most_600_characters():
    body = "Specimens were tested in tension " + "and again " * 60
    at_600 = body[:599].rstrip() + "."
    assert len(quotes.collapse(at_600)) <= quotes.QUOTE_MAX_CHARS == 600
    assert checked("test_type", "tension", at_600).code is None
    over = at_600[:-1] + " and again."
    assert len(quotes.collapse(over)) > 600 and checked("test_type", "tension", over).code == "quote_too_long"


@pytest.mark.parametrize("quote, found", [
    ("The specimens were tested in tension throughout the study.", True),
    ("he specimens were tested in tension throughout the study.", False),     # begins inside a word
    ("The specimens were tested in tension throughout the stu", False),       # ends inside a word
    ("specimens were tested in tension throughout the study", True),
])
def test_a_quote_begins_and_ends_at_a_word_boundary(quote, found):
    docs = {"documentation/a.md": "Intro.\nThe specimens were tested in tension throughout the study.\n"}
    assert (quotes.locate(quote, docs) is not None) is found


def test_a_later_occurrence_at_word_boundaries_is_the_one_found():
    docs = {"documentation/a.md": "Xspecimens were tested in tension at all times.\n"
                                  "Then: specimens were tested in tension at all times.\n"}
    assert quotes.locate("specimens were tested in tension at all times.", docs) == quotes.Located(
        "documentation/a.md", 2)


# --- f. the safe refusals the register records ------------------------------------------------------------------

@pytest.mark.parametrize("field, value, quote, code", [
    ("test_type", "tension", "Tested in tension.", "quote_too_short"),                    # under 30 characters
    ("test_temperature", 25, "All the specimens were tested at 298.15 K in laboratory air.", "term_missing"),
    ("microstructure", "L12", "Coherent L1$_2$ precipitates were found after ageing in every alloy.", "term_missing"),
])
def test_the_recorded_safe_refusals(field, value, quote, code):
    assert checked(field, value, quote).code == code


def test_the_value_is_checked_first_and_json_null_is_never_a_value():
    for field, value in (("test_type", None), ("test_temperature", None), ("test_temperature", True),
                         ("test_temperature", "25"), ("microstructure", "FCC+"), ("microstructure", "Sec.+FCC+x")):
        assert quotes.value_problem(field, value) == "value_not_allowed", (field, value)
