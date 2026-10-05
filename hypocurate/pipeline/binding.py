"""What a completed Checks result covered (step 6 review, finding 1; re-check finding 1).

No database and no access-layer import, so that the access layer (Inclusion's `set_flags`
reader) and the pipeline's write paths compute the binding the same way."""
from __future__ import annotations

import hashlib


def record_identity(version_fingerprint: str, origin: str, item_index: int) -> str:
    """A record's stable identity: never its database id."""
    return f"{version_fingerprint}|{origin}|{item_index}"


def binding(identities, flags) -> dict:
    """The exact record collection (by stable identity) and the flags raised for it (kind,
    category and the identities of their records)."""
    ids = sorted(identities)
    digest = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()
    flag_lines = sorted(f"{k}|{c}|{','.join(sorted(r))}" for k, c, r in flags)
    return {"records": len(ids), "identities": digest,
            "flags": hashlib.sha256("\n".join(flag_lines).encode("utf-8")).hexdigest()}
