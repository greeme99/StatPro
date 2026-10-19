"""Load named JSON contracts shipped with StatPro."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


def result_bundle_schema() -> dict[str, Any]:
    resource = files("statpro.schemas").joinpath("result-bundle.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))
