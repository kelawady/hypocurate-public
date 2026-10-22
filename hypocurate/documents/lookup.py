"""Open-access lookup, download and the supplement check for one DOI (R2). Network calls go through one function,
`http_get`, which a test replaces with a stub (the suite makes no live calls). Every request becomes one search-log
entry; nothing here writes to the database itself (`documents.store` does).

The contact address is sent to OpenAlex and Unpaywall as their polite-use terms ask (owner, 2026-10-22, register
'unpaywall_contact'). It is not a secret, and logged URLs show `{contact}` in its place."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

from hypocurate.db.models import DOCUMENT_MAX_BYTES

CONTACT_EMAIL = "khalid@eksentricity.ai"  # register 'unpaywall_contact'
OPENALEX_URL = "https://api.openalex.org/works/doi:{doi}?mailto={contact}"
UNPAYWALL_URL = "https://api.unpaywall.org/v2/{doi}?email={contact}"
USER_AGENT = "HypoCurate/pilot-2 (evidence-assembly pilot; mailto:{contact})"
TIMEOUT_S = 60
PAUSE_S = 1.0  # between requests to the same service
DETAIL_MAX = 2000
# A link on a landing page counts as a supplement when its address or text says so (register 'reach_milestones').
SUPPLEMENT_LINK = re.compile(r"""<a\b[^>]*href=["']([^"']+)["'][^>]*>(.*?)</a>""", re.I | re.S)
SUPPLEMENT_WORDS = re.compile(r"supplement|suppl[._-]|\bmmc\d+\b|\besm\b|supporting information", re.I)
NOT_FOUND_BY_AUTOMATIC_CHECK = "not found by automatic check"  # never "none" (owner, 2026-10-22)


@dataclass(frozen=True)
class Response:
    url: str
    status: int | None  # None: no answer (network error)
    body: bytes = b""
    content_type: str = ""
    final_url: str = ""
    error: str | None = None


def http_get(url: str, accept: str = "*/*") -> Response:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT.format(contact=CONTACT_EMAIL),
                                                   "Accept": accept})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as r:
            body = r.read(DOCUMENT_MAX_BYTES + 1)
            return Response(url, r.status, body, r.headers.get("Content-Type", ""), r.geturl())
    except urllib.error.HTTPError as e:
        return Response(url, e.code, b"", e.headers.get("Content-Type", "") if e.headers else "", url, f"HTTP {e.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return Response(url, None, b"", "", url, type(e).__name__ + ": " + str(getattr(e, "reason", e))[:300])


def shown(url: str) -> str:
    """A URL as logged: the contact address replaced, bounded."""
    return url.replace(urllib.parse.quote(CONTACT_EMAIL), "{contact}").replace(CONTACT_EMAIL, "{contact}")[:DETAIL_MAX]


@dataclass(frozen=True)
class LogEntry:
    action: str
    doi_key: str
    outcome: str
    url: str | None = None
    http_status: int | None = None
    detail: str | None = None


@dataclass
class Lookup:
    doi: str
    doi_key: str
    openalex: dict | None = None
    unpaywall: dict | None = None
    log: list[LogEntry] = field(default_factory=list)

    @property
    def is_oa(self) -> bool | None:
        """Unpaywall's flag where it answered, else OpenAlex's; None when neither answered."""
        if self.unpaywall is not None:
            return bool(self.unpaywall.get("is_oa"))
        if self.openalex is not None:
            return bool((self.openalex.get("open_access") or {}).get("is_oa"))
        return None

    @property
    def flag_source(self) -> str | None:
        return "unpaywall" if self.unpaywall is not None else "openalex" if self.openalex is not None else None

    @property
    def flags_disagree(self) -> bool:
        if self.unpaywall is None or self.openalex is None:
            return False
        return bool(self.unpaywall.get("is_oa")) != bool((self.openalex.get("open_access") or {}).get("is_oa"))

    @property
    def oa_status(self) -> str | None:
        if self.unpaywall is not None:
            return self.unpaywall.get("oa_status")
        return (self.openalex or {}).get("open_access", {}).get("oa_status")

    @property
    def license(self) -> str | None:
        best = (self.unpaywall or {}).get("best_oa_location") or (self.openalex or {}).get("best_oa_location") or {}
        return best.get("license")

    def pdf_candidates(self) -> list[tuple[str, str]]:
        """(url, where it came from), Unpaywall's best first, then its other locations, then OpenAlex's; no repeats."""
        found: list[tuple[str, str]] = []
        uw = self.unpaywall or {}
        for loc in [uw.get("best_oa_location")] + list(uw.get("oa_locations") or []):
            if loc and loc.get("url_for_pdf"):
                found.append((loc["url_for_pdf"], "unpaywall"))
        oa = self.openalex or {}
        for loc in [oa.get("best_oa_location")] + list(oa.get("locations") or []):
            if loc and loc.get("is_oa") and loc.get("pdf_url"):
                found.append((loc["pdf_url"], "openalex"))
        seen, out = set(), []
        for url, src in found:
            if url not in seen:
                seen.add(url)
                out.append((url, src))
        return out

    def landing_pages(self) -> list[str]:
        pages = []
        uw, oa = self.unpaywall or {}, self.openalex or {}
        for loc in [uw.get("best_oa_location")] + list(uw.get("oa_locations") or []):
            if loc and loc.get("url_for_landing_page"):
                pages.append(loc["url_for_landing_page"])
        primary = oa.get("primary_location") or {}
        if primary.get("landing_page_url"):
            pages.append(primary["landing_page_url"])
        return list(dict.fromkeys(pages))

    def summary(self) -> str:
        return json.dumps({"is_oa": self.is_oa, "flag_source": self.flag_source, "flags_disagree": self.flags_disagree,
                           "oa_status": self.oa_status, "license": self.license,
                           "pdf_candidates": len(self.pdf_candidates())}, sort_keys=True)


def _json(resp: Response) -> dict | None:
    if resp.status != 200:
        return None
    try:
        data = json.loads(resp.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _bare(doi_key: str) -> str:
    return doi_key.removeprefix("doi:")


def lookup(doi: str, doi_key: str, get=http_get, pause: float = PAUSE_S) -> Lookup:
    """OpenAlex, then Unpaywall, for one DOI."""
    result = Lookup(doi, doi_key)
    bare = urllib.parse.quote(_bare(doi_key), safe="/")
    contact = urllib.parse.quote(CONTACT_EMAIL)
    for action, template, attr in (("openalex_lookup", OPENALEX_URL, "openalex"),
                                   ("unpaywall_lookup", UNPAYWALL_URL, "unpaywall")):
        url = template.format(doi=bare, contact=contact)
        resp = get(url, "application/json")
        data = _json(resp)
        setattr(result, attr, data)
        outcome = "found" if data is not None else "not_found" if resp.status == 404 else "error"
        detail = resp.error if data is None else None
        result.log.append(LogEntry(action, doi_key, outcome, shown(url), resp.status, detail))
        time.sleep(pause)
    return result


@dataclass(frozen=True)
class Download:
    pdf: bytes | None
    url: str | None
    source: str | None  # 'unpaywall' or 'openalex'
    log: tuple[LogEntry, ...]


def download(found: Lookup, get=http_get, pause: float = PAUSE_S,
             candidates: list[tuple[str, str]] | None = None) -> Download:
    """Tries each open-access PDF address in turn (the lookup's, or `candidates`); the first answer that is a PDF
    within the size cap is kept."""
    log = []
    candidates = found.pdf_candidates() if candidates is None else candidates
    for url, source in candidates:
        resp = get(url, "application/pdf")
        time.sleep(pause)
        if resp.status != 200:
            log.append(LogEntry("download", found.doi_key, "refused" if resp.status in (401, 403, 451) else "failed",
                                shown(url), resp.status, resp.error))
            continue
        if not resp.body.startswith(b"%PDF-"):
            log.append(LogEntry("download", found.doi_key, "failed", shown(url), resp.status,
                                f"not a PDF ({resp.content_type[:100] or 'no content type'})"))
            continue
        if len(resp.body) > DOCUMENT_MAX_BYTES:
            log.append(LogEntry("download", found.doi_key, "failed", shown(url), resp.status,
                                f"larger than {DOCUMENT_MAX_BYTES} bytes"))
            continue
        log.append(LogEntry("download", found.doi_key, "ok", shown(url), resp.status, f"{len(resp.body)} bytes"))
        return Download(resp.body, url, source, tuple(log))
    if not candidates:
        log.append(LogEntry("download", found.doi_key, "not_found", None, None, "no open-access PDF address"))
    return Download(None, None, None, tuple(log))


@dataclass(frozen=True)
class SupplementCheck:
    found: bool
    url: str | None
    log: tuple[LogEntry, ...]

    @property
    def value(self) -> str:
        return "yes" if self.found else NOT_FOUND_BY_AUTOMATIC_CHECK


def supplements(found: Lookup, get=http_get, pause: float = PAUSE_S) -> SupplementCheck:
    """Looks on each landing page for a link whose address or text names a supplement (register 'reach_milestones').
    A page that does not answer, or answers with no such link, gives 'not found by automatic check', never 'none'."""
    log = []
    pages = found.landing_pages() or [f"https://doi.org/{_bare(found.doi_key)}"]
    for page in pages:
        resp = get(page, "text/html")
        time.sleep(pause)
        if resp.status != 200:
            log.append(LogEntry("supplement_check", found.doi_key, "error", shown(page), resp.status, resp.error))
            continue
        html = resp.body.decode("utf-8", errors="replace")
        for href, label in SUPPLEMENT_LINK.findall(html):
            if SUPPLEMENT_WORDS.search(href) or SUPPLEMENT_WORDS.search(re.sub(r"<[^>]+>", " ", label)):
                link = urllib.parse.urljoin(resp.final_url or page, href)
                log.append(LogEntry("supplement_check", found.doi_key, "found", shown(page), resp.status,
                                    f"link: {shown(link)}"[:DETAIL_MAX]))
                return SupplementCheck(True, link, tuple(log))
        log.append(LogEntry("supplement_check", found.doi_key, "not_found", shown(page), resp.status,
                            NOT_FOUND_BY_AUTOMATIC_CHECK))
    return SupplementCheck(False, None, tuple(log))


# --- publishers' standard PDF addresses (owner, 2026-10-22: tried automatically before any fetch by hand) -------------
# Only publishers whose open-access PDF address follows from the DOI or the landing page. Elsevier's free-to-read
# (bronze) articles are not here: their PDF address needs a page script, so they stay "not fetchable by a program".
TANDF_PDF = "https://www.tandfonline.com/doi/pdf/{doi}?download=true"
DOI_RESOLVER = "https://doi.org/{doi}"


def publisher_patterns(doi_key: str, get=http_get, pause: float = PAUSE_S) -> tuple[list[tuple[str, str]], list[LogEntry]]:
    """(url, 'pattern:<publisher>') addresses to try for one DOI, and the log of any request made to find them."""
    bare = _bare(doi_key)
    if bare.startswith("10.1080/"):
        return [(TANDF_PDF.format(doi=bare), "pattern:tandf")], []
    if bare.startswith("10.3390/"):
        url = DOI_RESOLVER.format(doi=bare)
        resp = get(url, "text/html")
        time.sleep(pause)
        landing = resp.final_url if resp.status == 200 and "mdpi.com" in (resp.final_url or "") else None
        entry = LogEntry("download", doi_key, "found" if landing else "failed", shown(url), resp.status,
                         f"publisher pattern: landing page {shown(landing)}" if landing
                         else f"publisher pattern: landing page not reached ({resp.error or 'no MDPI address'})")
        return ([(landing.rstrip("/") + "/pdf", "pattern:mdpi")] if landing else []), [entry]
    return [], []


def download_from(doi_key: str, candidates: list[tuple[str, str]], get=http_get, pause: float = PAUSE_S) -> Download:
    """Tries the given addresses, as `download` does."""
    return download(Lookup("", doi_key), get, pause, candidates)
