"""Shared numeric normalization owned by the analysis boundary."""

from __future__ import annotations

import math
from collections.abc import Iterable

from statpro.domain.errors import AnalysisInputError


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    """Evaluate the incomplete-beta continued fraction with bounded iteration."""

    maximum_iterations = 200
    epsilon = 3e-14
    floor = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < floor:
        d = floor
    d = 1.0 / d
    value = d
    for iteration in range(1, maximum_iterations + 1):
        even = 2 * iteration
        numerator = iteration * (b - iteration) * x / ((qam + even) * (a + even))
        d = 1.0 + numerator * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + numerator / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        value *= d * c
        numerator = -(a + iteration) * (qab + iteration) * x / ((a + even) * (qap + even))
        d = 1.0 + numerator * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + numerator / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        delta = d * c
        value *= delta
        if abs(delta - 1.0) <= epsilon:
            return value
    raise AnalysisInputError(
        "distribution_not_converged",
        "The F-distribution probability calculation did not converge.",
        "distribution",
    )


def _regularized_beta(x: float, a: float, b: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _beta_continued_fraction(a, b, x) / a
    return 1.0 - front * _beta_continued_fraction(b, a, 1.0 - x) / b


def f_survival(value: float | None, numerator_df: float, denominator_df: float) -> float | None:
    """Return P(F >= value) with a bounded regularized-beta evaluation."""

    if value is None or numerator_df <= 0.0 or denominator_df <= 0.0:
        return None
    if value <= 0.0:
        return 1.0
    if not math.isfinite(value):
        return 0.0
    transformed = denominator_df / (denominator_df + numerator_df * value)
    return min(1.0, max(0.0, _regularized_beta(
        transformed, denominator_df / 2.0, numerator_df / 2.0
    )))


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
