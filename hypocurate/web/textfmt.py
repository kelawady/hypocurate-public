"""How text is shown on the screens (step 10a; owner's review of the screenshots, 2026-10-11).

- `units`: escapes a code-written line and writes exponents as superscripts (MPa·µm^0.5 becomes MPa·µm<sup>0.5</sup>).
  Screens only; the stored text, the command line and the workbook keep "^".
- `model_text`: the Analyst's text (written by a language model) in a small safe subset of Markdown: paragraphs, bold
  (`**…**`), bulleted and numbered lists, and simple tables (`| a | b |`, with the `|---|` line dropped). Everything
  is escaped first, so the model's text can never add markup of its own; any other Markdown sign is left as text
  except leading heading marks (`#`), which are dropped. Exponents are written as in `units`.
"""
from __future__ import annotations

import re

from markupsafe import Markup, escape

_EXPONENT = re.compile(r"\^(-?\d+(?:\.\d+)?(?:/\d+)?)")
_BOLD = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_BULLET = re.compile(r"^\s*[-*•]\s+(.*)$")
_NUMBERED = re.compile(r"^\s*\d+[.)]\s+(.*)$")
_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_HEADING = re.compile(r"^\s*#{1,6}\s+")


def _inline(raw: str) -> str:
    """One escaped line with bold and exponents: the only markup added, and only around escaped text."""
    out = str(escape(raw))
    out = _BOLD.sub(r"<strong>\1</strong>", out)
    return _EXPONENT.sub(r"<sup>\1</sup>", out)


def units(line: str) -> Markup:
    return Markup(_EXPONENT.sub(r"<sup>\1</sup>", str(escape(line))))


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _table(rows: list[str]) -> str:
    body = [r for r in rows if not _TABLE_RULE.match(r)]
    head, rest = (body[0], body[1:]) if len(body) > 1 and any(_TABLE_RULE.match(r) for r in rows) else (None, body)
    parts = ['<table class="data model-table">']
    if head is not None:
        parts.append("<thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in _cells(head)) + "</tr></thead>")
    parts.append("<tbody>" + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in _cells(r)) + "</tr>"
                                     for r in rest) + "</tbody></table>")
    return "".join(parts)


def model_text(text: str | None) -> Markup:
    lines = (text or "").replace("\r\n", "\n").split("\n")
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if _TABLE_ROW.match(line):
            rows = []
            while i < len(lines) and (_TABLE_ROW.match(lines[i]) or _TABLE_RULE.match(lines[i])) and lines[i].strip():
                rows.append(lines[i])
                i += 1
            blocks.append(_table(rows))
            continue
        for pattern, tag in ((_BULLET, "ul"), (_NUMBERED, "ol")):
            if pattern.match(line):
                items = []
                while i < len(lines) and pattern.match(lines[i]):
                    items.append(f"<li>{_inline(pattern.match(lines[i]).group(1))}</li>")
                    i += 1
                blocks.append(f"<{tag}>{''.join(items)}</{tag}>")
                break
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not _TABLE_ROW.match(lines[i]) \
                    and not _BULLET.match(lines[i]) and not _NUMBERED.match(lines[i]):
                para.append(_inline(_HEADING.sub("", lines[i]).strip()))
                i += 1
            blocks.append("<p>" + " ".join(para) + "</p>")
    return Markup("".join(blocks))
