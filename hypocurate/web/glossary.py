"""The explanation texts (PRD 9.7): one file, `hypocurate/web/glossary.json`, keyed by identifier. The information
buttons and the Help page read it; no explanation text is written in a template (step 10a moved the file from
`docs/glossary.json`, because the deployed image holds no `docs/`).

Each entry: `key` (unique), `term`, `screen` (where it appears) and `text` (two or three plain sentences).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

PATH = Path(__file__).resolve().parent / "glossary.json"
FIELDS = ("key", "screen", "term", "text")


class GlossaryError(ValueError):
    pass


def validate(entries: list) -> None:
    if not isinstance(entries, list) or not entries:
        raise GlossaryError("the glossary is a non-empty list")
    seen = set()
    for e in entries:
        if not isinstance(e, dict) or set(e) != set(FIELDS) or not all(isinstance(e[f], str) and e[f].strip()
                                                                       for f in FIELDS):
            raise GlossaryError(f"an entry must have exactly {', '.join(FIELDS)}, each a non-empty text")
        if e["key"] in seen:
            raise GlossaryError(f"duplicate key {e['key']}")
        seen.add(e["key"])


@lru_cache(maxsize=1)
def entries() -> tuple[Mapping[str, str], ...]:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    validate(data)
    return tuple(MappingProxyType(dict(e)) for e in data)


def by_key() -> Mapping[str, Mapping[str, str]]:
    return MappingProxyType({e["key"]: e for e in entries()})


def entry(key: str) -> Mapping[str, str]:
    found = by_key().get(key)
    if found is None:
        raise KeyError(f"no glossary entry {key!r}")
    return found
