"""Which papers lie behind the compilation's FCC grain-size records (R2; owner, 2026-10-22, register
'reach_selection').

The FCC definition is Sprint 1's, read from where eligibility reads it (`pipeline.profile`): with single phase
required, the microstructure field must be one of the scope's phase classes. For MPEA that field comes from the
column `PROPERTY: Microstructure`; the reach table records that column. A record counts when its grain size was
converted to µm. Papers are told apart by the normalized DOI (`sources.normalize.doi_group_key`), as Sprint 1 groups
them. Pure functions over an adapter's records: they read no database and no network."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from hypocurate.pipeline import profile
from hypocurate.sources import adapters
from hypocurate.sources.normalize import doi_group_key
from hypocurate.sources.versions import SealedVersion

# The source column behind each harmonized phase field, for the sources this pilot selects from.
PHASE_COLUMNS = {("mpea", "microstructure"): "PROPERTY: Microstructure",
                 ("mpea", "phase_class"): "PROPERTY: BCC/FCC/other"}


def phase_field() -> str:
    """Sprint 1's rule (eligibility): the microstructure when single phase is required, else the phase class."""
    return "microstructure" if profile.SINGLE_PHASE == "required" else "phase_class"


@dataclass(frozen=True)
class Paper:
    doi: str  # as the compilation gives it (the first spelling met)
    doi_key: str
    records: int  # selected records (FCC, grain size converted)
    records_with_yield_strength: int
    item_keys: tuple[str, ...]


@dataclass(frozen=True)
class Selection:
    source_key: str
    version_fingerprint: str
    phase_field: str
    phase_column: str
    phase_classes: tuple[str, ...]
    papers: tuple[Paper, ...]  # most records first, then by DOI key
    records_without_doi: int

    @property
    def records(self) -> int:
        return sum(p.records for p in self.papers) + self.records_without_doi


def fcc_grain_size(version: SealedVersion) -> Selection:
    field = phase_field()
    by_key: dict[str, list] = defaultdict(list)
    without = 0
    for r in adapters.read(version).records:
        phase = r.harmonized[field]
        if phase.value not in profile.PHASE_CLASSES or r.harmonized["grain_size"].status != "converted":
            continue
        key = doi_group_key(r.paper_doi) if r.paper_doi else None
        if key is None:
            without += 1
            continue
        by_key[key].append(r)
    papers = []
    for key, recs in by_key.items():
        papers.append(Paper(doi=recs[0].paper_doi.strip(), doi_key=key, records=len(recs),
                            records_with_yield_strength=sum(r.harmonized["yield_strength"].status == "converted"
                                                            for r in recs),
                            item_keys=tuple(r.source_item_key for r in recs)))
    papers.sort(key=lambda p: (-p.records, p.doi_key))
    return Selection(version.source_key, version.fingerprint, field, PHASE_COLUMNS[(version.source_key, field)],
                     tuple(profile.PHASE_CLASSES), tuple(papers), without)
