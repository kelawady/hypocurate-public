"""Download the frozen source files again from their pinned origins and check them.

A manual tool, not part of the test suite (the suite must not depend on the
network). It never overwrites the frozen copies: it only reports whether each
origin still serves the exact bytes recorded in data/manifest.json.

    python scripts/fetch_sources.py            # check each file at its pinned GitHub URL
    python scripts/fetch_sources.py --zenodo   # also download the Zenodo archive (about 49 MB)
                                               # and check its MD5 and the files inside it

Exit status 0 means every check passed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hypocurate.sources.manifest import load_manifest  # noqa: E402


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "hypocurate-fetch-sources"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def check(label: str, data: bytes, sha256: str, size: int) -> bool:
    digest = hashlib.sha256(data).hexdigest()
    ok = digest == sha256 and len(data) == size
    print(f"{'OK  ' if ok else 'FAIL'} {label}  sha256={digest}  bytes={len(data)}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--zenodo", action="store_true", help="also check the Zenodo archive")
    args = parser.parse_args()

    manifest = load_manifest()
    ok = True
    for source_id, source in manifest["sources"].items():
        for f in source["files"]:
            try:
                data = fetch(f["origin_url"])
            except Exception as e:  # report and carry on: a failed fetch is not a match
                print(f"FAIL {source_id}: {f['path']}  could not fetch: {e}")
                ok = False
                continue
            ok &= check(f"{source_id}: {f['path']} <- {f['origin_url']}", data, f["sha256"], f["bytes"])

    if args.zenodo:
        source = manifest["sources"]["tamu_fcc"]
        z = source["zenodo_archive"]
        archive = fetch(z["url"])
        md5 = hashlib.md5(archive).hexdigest()
        archive_ok = md5 == z["md5"] and len(archive) == z["bytes"]
        print(f"{'OK  ' if archive_ok else 'FAIL'} tamu_fcc: Zenodo archive md5={md5} bytes={len(archive)}")
        ok &= archive_ok
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            for f in source["files"]:
                member = z["member_prefix"] + f["archive_member"]
                ok &= check(f"tamu_fcc: {f['path']} <- Zenodo {member}", zf.read(member), f["sha256"], f["bytes"])

    print("ALL MATCH" if ok else "MISMATCH: do not substitute another source; report it")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
