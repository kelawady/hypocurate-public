"""Step 8b fix round 1, finding 5: wrong-type answer shapes for every role's validator tests.

`variants(answer)` yields the answer with each position (the whole answer, every value of every object and every
item of every list) replaced in turn by each value of `WRONG`: valid JSON of every type, including the nested
lists and objects that once raised TypeError at a membership test. A validator must refuse each with its own
code and never raise anything else.
"""
from __future__ import annotations

import json
from typing import Any, Iterator

WRONG = [None, True, 0, 1.5, "", "x", [], ["x"], [[]], {}, {"a": 1}, {"class": []}]


def _paths(o: Any, path: tuple = ()) -> Iterator[tuple]:
    yield path
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _paths(v, path + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _paths(v, path + (i,))


def _replaced(o: Any, path: tuple, value: Any) -> Any:
    if not path:
        return value
    copy = json.loads(json.dumps(o))
    cur = copy
    for k in path[:-1]:
        cur = cur[k]
    cur[path[-1]] = value
    return copy


def variants(answer: Any) -> Iterator[tuple[tuple, Any, Any]]:
    """(path, wrong value, the answer with that value at that path)."""
    for path in list(_paths(answer)):
        for value in WRONG:
            yield path, value, _replaced(answer, path, value)
