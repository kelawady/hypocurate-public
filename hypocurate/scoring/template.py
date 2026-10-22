"""The annotation template (PRD v1.2 Appendix B, plus the identity columns; owner, 2026-10-22, register
'annotation_template').

Every Appendix B column is kept, with its meaning unchanged. Three are added so that the scorer can match on R-identity
without reading free text: `observation_location` and `specimen_label`, placed right after `processing_state` so the
annotator fills the identity before the values, and `test_temperature_unit`. One column list (`COLUMNS`); the .xlsx is
generated from it, and the loader reads by it."""
from __future__ import annotations

import io

TEMPLATE_VERSION = "B1+identity-1"

# (column, what to enter, example) in the order of the sheet.
COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("paper_doi", "The DOI.", "10.1016/j.actamat.2013.06.018"),
    ("alloy_as_written", "The name as the paper writes it.", "CrMnFeCoNi"),
    ("composition_at_pct", "The nominal composition if given.", "Co20Cr20Fe20Mn20Ni20"),
    ("processing_state", "The final heat treatment or state the specimen was tested in, as written.",
     "cold-rolled 85 %, annealed 1 h at 800 °C"),
    ("observation_location", "Where this observation is reported as a whole: page and table and row, or page and "
                             "sentence. Always fill it.", "p. 5, Table 2, row 1"),
    ("specimen_label", "The paper's specimen or replicate label, if it gives one; blank if it gives none.", "A1"),
    ("grain_size_value", "As written.", "4.4"),
    ("grain_size_unit", "µm or as written.", "µm"),
    ("grain_size_method", "Linear intercept / equivalent diameter / as stated; twins counted if stated.",
     "linear intercept, twins excluded"),
    ("grain_size_location", "Page and table and row, or page and sentence, or figure number and caption.",
     "p. 5, Table 2, row 1"),
    ("yield_strength_value", "As written.", "360"),
    ("yield_strength_unit", "MPa or as written.", "MPa"),
    ("yield_strength_definition", "0.2 % offset or as stated.", "0.2 % offset"),
    ("yield_strength_location", "As for grain size.", "p. 5, Table 2, row 1"),
    ("test_type", "tension / compression.", "tension"),
    ("test_temperature", "The number (or 'room temperature') as written.", "293"),
    ("test_temperature_unit", "°C or K, as written; blank for 'room temperature'.", "K"),
    ("strain_rate", "If given.", "1e-3 /s"),
    ("link_evidence", "Why these two values are one observation: same table row / same specimen label (give it) / "
                      "explicit sentence (quote it) / methods statement (quote it).", "same table row"),
    ("link_location", "Where the link evidence is.", "p. 5, Table 2"),
    ("ambiguity_note", "Anything you could not decide, in a sentence.",
     "two specimens 'A' and 'A2' both annealed at 800 °C; strength not attributed"),
    ("in_compilation", "Leave blank; the script fills it.", ""),
    ("annotator", "Your name.", "K. El-Awady"),
    ("minutes", "Time spent on this paper (on its first row is enough).", "25"),
)
NAMES = tuple(c[0] for c in COLUMNS)

READ_ME = (
    "HypoCurate pilot: annotation template, version " + TEMPLATE_VERSION,
    "One row per observation, filled from the PDF without looking at the extractor's output.",
    "Leave a cell blank if the paper does not give it; write 'ambiguous' and a note if it gives it but you cannot tell "
    "which specimen it belongs to. Time yourself per paper.",
    "Fill the identity first: processing_state, observation_location, specimen_label. Every row needs an "
    "observation_location; specimen_label only when the paper labels its specimens.",
    "",
    "Example 1 (illustration, not from a real paper): a paper that labels its specimens. Table 2 on page 5 lists "
    "specimens A1 and A2, both annealed 1 h at 800 °C, with their grain sizes and yield strengths.",
    "   Row for A1: processing_state 'annealed 1 h at 800 °C'; observation_location 'p. 5, Table 2, row 1'; "
    "specimen_label 'A1'.",
    "   Row for A2: the same processing_state; observation_location 'p. 5, Table 2, row 2'; specimen_label 'A2'. "
    "Two rows: they are separately reported specimens.",
    "Example 2 (illustration, not from a real paper): a paper with no specimen labels. Page 6 says: 'After annealing at "
    "900 °C for 1 h the grain size was 25 µm and the yield strength 210 MPa.'",
    "   Row: processing_state 'annealed 1 h at 900 °C'; observation_location 'p. 6, sentence: After annealing at "
    "900 °C for 1 h the grain size was 25 µm and the yield strength 210 MPa.'; specimen_label blank. The location "
    "stands in for the label.",
    "",
    "Columns (what to enter; example):",
) + tuple(f"   {name}: {what} (e.g. {example})" if example else f"   {name}: {what}" for name, what, example in COLUMNS)


def workbook() -> bytes:
    """The template as .xlsx: a 'Read me' sheet (instructions and the two examples), then 'Annotation' with the header
    row only, so no example can be loaded as data."""
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    readme = wb.active
    readme.title = "Read me"
    for line in READ_ME:
        readme.append([line])
    readme.column_dimensions["A"].width = 140
    sheet = wb.create_sheet("Annotation")
    sheet.append(list(NAMES))
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    sheet.freeze_panes = "A2"
    for i, name in enumerate(NAMES, start=1):
        sheet.column_dimensions[sheet.cell(1, i).column_letter].width = max(14, len(name) + 2)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
