<!-- Extractor prompt, version 1 (draft, 2026-10-22; first sent on Friday after the access allow-list exists). -->
You read one materials-science paper, given as parsed text blocks and tables with page numbers and table and row
indexes. List every observation the paper reports that matches the evidence specification below.

For each observation give its values exactly as written, each with its provenance: the page, and either the table
index and row index, or the sentence it was read from, and a short snippet copied from that place. Give the links
between the grain size and the yield strength (and any other values) that show they belong to one specimen, with the
evidence for the link: the same table row, the same specimen label, an explicit sentence, or a methods statement.

If you cannot tell which specimen a value belongs to, keep the value and write an ambiguity note; never guess. If a
value comes only from a figure with no stated number, leave it out. Report every specimen the paper gives separately.
Answer with JSON that matches the output schema, and nothing else.

Evidence specification (the parts that say what to read):
{spec_sections}

The paper:
{document}
