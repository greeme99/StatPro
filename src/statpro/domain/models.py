"""Versioned result contracts for reproducible statistical analyses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProvenanceSource:
    title: str
    url: str
    authority: str = "public-reference"


@dataclass(frozen=True, slots=True)
class ResultBundle:
    analysis_type: str
    engine_version: str
    input_digest: str
    parameters: dict[str, Any]
    tables: dict[str, Any]
    plots: dict[str, Any]
    diagnostics: dict[str, Any]
    assumptions: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    provenance: tuple[ProvenanceSource, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_type": self.analysis_type,
            "engine_version": self.engine_version,
            "input_digest": self.input_digest,
            "parameters": self.parameters,
            "tables": self.tables,
            "plots": self.plots,
            "diagnostics": self.diagnostics,
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
            "provenance": [asdict(source) for source in self.provenance],
        }
