"""R-identity (PRD v1.2 Section 4; owner, 2026-10-22, register 'observation_identity'): one observation is one paper,
one alloy, one processing state, one test type, one test temperature and one specimen. The specimen is the source's
specimen or replicate label where the paper gives one, otherwise the observation's location in the source (table and
row, or page and sentence), so separately reported specimens under identical conditions stay separate observations.

This module is the one place the identity is defined. The Extractor's records, the annotation rows, the re-report rule
and the scorer all call `identity`; none builds its own. What each component normalizes, and nothing more:
- paper: the normalized DOI (`sources.normalize.doi_group_key`, Sprint 1's paper identity);
- alloy: Sprint 1's same-alloy key (composition in at.% rounded to 0.1, `normalize.same_alloy_key`) from the
  composition if given, else from the alloy name read as a formula; a name that does not parse is kept as
  'name:<name, case-folded, without spaces>', so it can still match itself but never a composition;
- processing state, specimen label, location: case-folded, runs of whitespace collapsed, the degree sign unified;
- test type: 'tension' or 'compression' when the text says so (tensile, compressive), else the text normalized;
- test temperature: converted to °C (from K) and then rounded to the nearest degree; a stated 'room temperature' (or
  RT, ambient) and any rounded temperature within Sprint 1's room-temperature range (20 to 25 °C,
  `pipeline.profile.ROOM_TEMPERATURE_C`) both key to the band 'room temperature' (owner, 2026-10-23), so a record
  stated as 'room temperature' matches one stated as 20 °C or 25 °C; anything else, the text normalized.
The scorer and the re-report rule match on `match_key` (owner, 2026-10-23): the identity without the processing state,
whose text is reported per pair and adjudicated, never matched. Matching is one-to-one (the scorer's rule); a value
within tolerance is the scorer's and the re-report rule's question, not the identity's."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass

from hypocurate.pipeline.profile import ROOM_TEMPERATURE_C
from hypocurate.sources.normalize import doi_group_key, formula_to_atomic_percent, same_alloy_key

ROOM_TEMPERATURE = "room temperature"
_RT = re.compile(r"^(room[\s-]*temperature|rt|ambient(\s+temperature)?)$", re.I)
_NUMBER = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*(°\s*c|℃|c|k)?\s*$", re.I)
IDENTITY_VERSION = "2"  # 2 (owner, 2026-10-23): the room-temperature band; the match key without processing state
MATCH_FIELDS = ("paper", "alloy", "test_type", "test_temperature", "specimen", "version")


def _text(s: str | None) -> str:
    if s is None:
        return ""
    s = s.replace("℃", "°C").replace("º", "°").replace("˚", "°")
    return " ".join(s.split()).casefold()


def alloy_key(alloy: str | None, composition: str | None = None) -> str:
    for candidate in (composition, alloy):
        if candidate and candidate.strip():
            comp, _ = formula_to_atomic_percent(candidate.replace("-", "").replace(" ", ""))
            if comp is not None:
                return same_alloy_key(comp)
    return "name:" + _text(alloy).replace(" ", "") if alloy and alloy.strip() else ""


def test_type_key(test_type: str | None) -> str:
    t = _text(test_type)
    if t.startswith("tens") or t == "t":
        return "tension"
    if t.startswith("compress") or t == "c":
        return "compression"
    return t


def temperature_key(value: str | None, unit: str | None = None) -> str:
    t = _text(value)
    if not t:
        return ""
    if _RT.match(t):
        return ROOM_TEMPERATURE
    m = _NUMBER.match(t + (" " + _text(unit) if unit and not re.search(r"[a-z°℃]", t) else ""))
    if not m:
        return t
    number, given = float(m.group(1)), (m.group(2) or _text(unit) or "°c").replace(" ", "")
    celsius = round(number - 273.15 if given == "k" else number)
    low, high = ROOM_TEMPERATURE_C
    return ROOM_TEMPERATURE if low <= celsius <= high else f"{celsius:d} °c"


@dataclass(frozen=True)
class Identity:
    paper: str
    alloy: str
    processing_state: str
    test_type: str
    test_temperature: str
    specimen: str  # 'label:<label>' or 'location:<location>'
    version: str = IDENTITY_VERSION

    @property
    def key(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True, ensure_ascii=False,
                                         separators=(",", ":")).encode("utf-8")).hexdigest()

    @property
    def match_key(self) -> str:
        return match_key(self.to_json())

    def to_json(self) -> dict:
        return asdict(self)


def match_key(identity_json: dict) -> str:
    """The key the scorer and the re-report rule match on (owner, 2026-10-23): every identity field but the
    processing state, from a stored identity."""
    picked = {f: identity_json[f] for f in MATCH_FIELDS}
    return hashlib.sha256(json.dumps(picked, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


class IdentityError(ValueError):
    pass


CITED = "cited:"


def cited_identity(citation: str, base: Identity) -> Identity:
    """A record the paper reports from another paper (owner, 2026-10-23, Q-E): its paper is 'cited:<citation>', so it
    never matches an observation of the paper read, nor a compilation record of it."""
    from dataclasses import replace
    return replace(base, paper=CITED + _text(citation))


def identity(paper_doi: str, alloy: str | None, processing_state: str | None, test_type: str | None,
             test_temperature: str | None, specimen_label: str | None, observation_location: str | None, *,
             composition: str | None = None, test_temperature_unit: str | None = None) -> Identity:
    """The identity of one observation. Refused without a paper, or with neither a specimen label nor a location."""
    paper = doi_group_key(paper_doi or "")
    if paper is None:
        raise IdentityError("an observation names its paper")
    label, location = _text(specimen_label), _text(observation_location)
    if not label and not location:
        raise IdentityError("an observation names its specimen label or its location in the source")
    return Identity(paper, alloy_key(alloy, composition), _text(processing_state), test_type_key(test_type),
                    temperature_key(test_temperature, test_temperature_unit),
                    f"label:{label}" if label else f"location:{location}")
