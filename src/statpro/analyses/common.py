"""Shared numeric normalization owned by the analysis boundary."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from statpro.domain.errors import AnalysisInputError


def invert_matrix(matrix: Sequence[Sequence[float]], *, field: str) -> list[list[float]]:
    """Invert a small dense square matrix with partial pivoting."""

    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise AnalysisInputError(
            "invalid_matrix", "The model matrix must be non-empty and square.", field
        )
    augmented = [
        [float(value) for value in row]
        + [1.0 if row_index == column_index else 0.0 for column_index in range(size)]
        for row_index, row in enumerate(matrix)
    ]
    for column in range(size):
        pivot_row = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        pivot = augmented[pivot_row][column]
        if abs(pivot) < 1e-12:
            raise AnalysisInputError(
                "singular_design_matrix",
                "The selected linear model is not estimable from this design.",
                field,
            )
        augmented[column], augmented[pivot_row] = augmented[pivot_row], augmented[column]
        pivot = augmented[column][column]
        augmented[column] = [value / pivot for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            multiplier = augmented[row][column]
            if multiplier != 0.0:
                augmented[row] = [
                    value - multiplier * pivot_value
                    for value, pivot_value in zip(augmented[row], augmented[column], strict=True)
                ]
    return [row[size:] for row in augmented]


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


def _regularized_gamma_lower(shape: float, value: float) -> float:
    """Evaluate the lower regularized gamma P(shape, value)."""

    if value <= 0.0:
        return 0.0
    if shape <= 0.0:
        raise AnalysisInputError("invalid_distribution_parameter", "Gamma shape must be positive.", "distribution")
    epsilon = 3e-14
    floor = 1e-300
    log_front = -value + shape * math.log(value) - math.lgamma(shape)
    if value < shape + 1.0:
        term = 1.0 / shape
        total = term
        for iteration in range(1, 201):
            term *= value / (shape + iteration)
            total += term
            if abs(term) <= abs(total) * epsilon:
                return min(1.0, max(0.0, math.exp(log_front) * total))
    else:
        b = value + 1.0 - shape
        c = 1.0 / floor
        d = 1.0 / max(b, floor)
        fraction = d
        for iteration in range(1, 201):
            numerator = -iteration * (iteration - shape)
            b += 2.0
            d = numerator * d + b
            if abs(d) < floor:
                d = floor
            c = b + numerator / c
            if abs(c) < floor:
                c = floor
            d = 1.0 / d
            delta = d * c
            fraction *= delta
            if abs(delta - 1.0) <= epsilon:
                return min(1.0, max(0.0, 1.0 - math.exp(log_front) * fraction))
    raise AnalysisInputError("distribution_not_converged", "The chi-square probability calculation did not converge.", "distribution")


def chi_square_quantile(probability: float, degrees_of_freedom: float) -> float:
    """Return the lower-tail chi-square quantile using a bounded bisection."""

    if not 0.0 < probability < 1.0 or degrees_of_freedom <= 0.0:
        raise AnalysisInputError("invalid_distribution_parameter", "Chi-square probability must be in (0, 1) and degrees of freedom positive.", "distribution")
    shape = degrees_of_freedom / 2.0
    lower = 0.0
    upper = max(1.0, degrees_of_freedom + 10.0 * math.sqrt(2.0 * degrees_of_freedom))
    while _regularized_gamma_lower(shape, upper / 2.0) < probability:
        upper *= 2.0
        if upper > 1e12:
            raise AnalysisInputError("distribution_not_converged", "The chi-square quantile search exceeded its bound.", "distribution")
    for _ in range(100):
        midpoint = (lower + upper) / 2.0
        if _regularized_gamma_lower(shape, midpoint / 2.0) < probability:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2.0


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
