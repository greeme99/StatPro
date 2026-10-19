"""Shared normalization and identity helpers owned by the analysis boundary."""

from __future__ import annotations

import math
from collections.abc import Iterable

from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest


def finite_values(values: Iterable[object], field: str) -> list[float]:
    converted: list[float] = []
    for index, value in enumerate(values):
        if isinstance(value, bool):
            raise AnalysisInputError(
                "invalid_numeric_value",
                f"Boolean value at index {index} is not a measurement.",
                field,
            )
        try:
            numeric = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as error:
            raise AnalysisInputError(
                "invalid_numeric_value",
                f"Value at index {index} is not numeric.",
                field,
            ) from error
        if not math.isfinite(numeric):
            raise AnalysisInputError(
                "non_finite_value",
                f"Value at index {index} must be finite.",
                field,
            )
        converted.append(numeric)
    return converted
