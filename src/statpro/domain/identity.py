"""Canonical content identity owned by the domain boundary."""

from __future__ import annotations

import hashlib
import json


def input_digest(payload: object) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
