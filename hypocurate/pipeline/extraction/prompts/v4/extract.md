You read one materials-science paper, given as parsed text blocks and tables, each with its page number and its table and row indexes. Find every observation the paper reports in which a material's grain size and its yield strength are given for the same specimen or state, as the evidence specification describes, and return them all.

The specification's context fields (phase, processing state, test type, test temperature, strain rate and the others) are things to record for every observation, exactly as the paper states them. They are never a filter: return an observation even if its test type, temperature or phase differs from the specification's examples. Code decides later what is used.

For every observation, give each value exactly as written, with its unit as written, and its provenance: the page, and either the table index and row index, or the sentence it was read from, with a short snippet copied from that place. Give the links that make the values one observation (most importantly between the grain size and the yield strength), each with its kind and its provenance: the same table row, the same specimen label, an explicit sentence, or a methods statement.

Rules:
- Every record carries the context fields the specification lists (test type, test temperature, strain rate, phase, processing state). When the paper states a condition once, for example in its methods section, and it applies to all specimens, copy it into every record it applies to, with the methods sentence as its provenance and the definition "from methods, applies to all specimens". Leave a context field out only if the paper does not state it at all.
- If you cannot tell which specimen or state a value belongs to, keep the value and write an ambiguity note. Never guess.
- If the paper shows a value only in a figure, with no number stated in the text or a table, return that value with text "figure only", no provenance, and the ambiguity note "figure only; no number stated", and give the figure in the note. Do not read numbers off figures.
- If the paper gives a range (for example "0.95-1.1 GPa"), write the range as the value's text.
- Report every specimen the paper gives separately as its own observation.
- Return one record for every specimen or condition a table lists, even when its yield strength (or its grain size) is shown only in a figure; give that value as "figure only", as above. A condition is a record whether or not the paper states a number for every value.
- If a row or sentence reports another paper's data (for example a comparison table citing other work), return it with "reported_from" set to that citation as written, not to "this paper". Never present cited data as this paper's own.
- Use only the paper. Do not use anything you know from elsewhere.

Answer with one JSON object that matches the output schema below, and nothing else. Every record has "values", "links" (an empty list if there is none) and "reported_from".
