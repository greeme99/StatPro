"""Design generation for two-level full factorial experiments."""

from __future__ import annotations

import random
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from itertools import combinations
from math import exp, isfinite, lgamma, log, log1p, sqrt
from statistics import NormalDist
from typing import Sequence

from statpro.analyses.common import finite_values, input_digest
from statpro.domain.errors import AnalysisInputError
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_FACTORIAL_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.3.3.3.1 Two-level full factorial designs",
    url="https://www.itl.nist.gov/div898/handbook/pri/section3/pri3331.htm",
)

NIST_DOE_MODEL_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.4.3 How to model DOE data",
    url="https://www.itl.nist.gov/div898/handbook/pri/section4/pri43.htm",
)

NIST_RESIDUAL_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.2.4 Are the model residuals well-behaved?",
    url="https://www.itl.nist.gov/div898/handbook/pri/section2/pri24.htm",
)


@dataclass(frozen=True, slots=True)
class FactorDefinition:
    name: str
    low: float
    high: float


def _normalize_factors(factors: Sequence[FactorDefinition]) -> list[FactorDefinition]:
    if len(factors) < 2:
        raise AnalysisInputError(
            "insufficient_factors",
            "A two-level full factorial design requires at least two factors.",
            "factors",
        )
    if len(factors) > 12:
        raise AnalysisInputError(
            "too_many_factors",
            "The bounded generator supports at most 12 factors.",
            "factors",
        )

    normalized: list[FactorDefinition] = []
    names: set[str] = set()
    for index, factor in enumerate(factors):
        name = factor.name.strip()
        if not name:
            raise AnalysisInputError(
                "empty_factor_name", f"Factor {index + 1} needs a name.", "factors"
            )
        if name in names:
            raise AnalysisInputError(
                "duplicate_factor_name", f"Factor name '{name}' is duplicated.", "factors"
            )
        low, high = finite_values([factor.low, factor.high], f"factors[{index}]")
        if low >= high:
            raise AnalysisInputError(
                "invalid_factor_levels",
                f"Factor '{name}' low level must be less than its high level.",
                f"factors[{index}]",
            )
        names.add(name)
        normalized.append(FactorDefinition(name=name, low=low, high=high))
    return normalized


def full_factorial_2level(
    factors: Sequence[FactorDefinition],
    *,
    replicates: int = 1,
    center_points: int = 0,
    randomize: bool = True,
    seed: int = 0,
) -> ResultBundle:
    """Generate a bounded, reproducible 2^k full factorial design."""

    normalized = _normalize_factors(factors)
    if isinstance(replicates, bool) or replicates < 1:
        raise AnalysisInputError(
            "invalid_replicates", "Replicates must be a positive integer.", "replicates"
        )
    if isinstance(center_points, bool) or center_points < 0:
        raise AnalysisInputError(
            "invalid_center_points",
            "Center points must be a nonnegative integer.",
            "center_points",
        )
    if not isinstance(replicates, int) or not isinstance(center_points, int):
        raise AnalysisInputError(
            "invalid_run_count", "Replicates and center points must be integers.", "replicates"
        )
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise AnalysisInputError("invalid_seed", "Random seed must be an integer.", "seed")

    factorial_run_count = 2 ** len(normalized)
    total_run_count = factorial_run_count * replicates + center_points
    if total_run_count > 100_000:
        raise AnalysisInputError(
            "design_too_large",
            "The requested design exceeds the 100,000-run safety limit.",
            "factors",
        )

    rows: list[dict[str, object]] = []
    for replicate in range(1, replicates + 1):
        for standard_index in range(factorial_run_count):
            coded = {
                factor.name: (1 if standard_index & (1 << factor_index) else -1)
                for factor_index, factor in enumerate(normalized)
            }
            actual = {
                factor.name: factor.high if coded[factor.name] == 1 else factor.low
                for factor in normalized
            }
            rows.append(
                {
                    "standard_order": standard_index + 1,
                    "replicate": replicate,
                    "point_type": "factorial",
                    "coded": coded,
                    "actual": actual,
                }
            )

    center_actual = {factor.name: (factor.low + factor.high) / 2.0 for factor in normalized}
    center_coded = {factor.name: 0 for factor in normalized}
    for center_index in range(1, center_points + 1):
        rows.append(
            {
                "standard_order": None,
                "replicate": center_index,
                "point_type": "center",
                "coded": center_coded.copy(),
                "actual": center_actual.copy(),
            }
        )

    if randomize:
        random.Random(seed).shuffle(rows)
    for run_order, row in enumerate(rows, start=1):
        row["run_order"] = run_order

    warnings: list[str] = []
    if len(normalized) >= 5:
        warnings.append(
            "NIST recommends considering fractional factorial or screening designs for five or more factors."
        )
    if not randomize:
        warnings.append(
            "Runs are not randomized; time-related nuisance factors may be confounded with factor effects."
        )

    factor_payload = [asdict(factor) for factor in normalized]
    payload = {
        "factors": factor_payload,
        "replicates": replicates,
        "center_points": center_points,
        "randomize": randomize,
        "seed": seed,
    }
    return ResultBundle(
        analysis_type="doe.full_factorial_2level",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={
            "factors": factor_payload,
            "replicates": replicates,
            "center_points": center_points,
            "randomize": randomize,
            "seed": seed,
        },
        tables={"design": rows},
        plots={},
        diagnostics={
            "factor_count": len(normalized),
            "factorial_run_count": factorial_run_count,
            "total_run_count": total_run_count,
            "balanced": True,
            "full_factorial": True,
        },
        assumptions=(
            "Each factor has exactly two quantitative levels.",
            "The experiment can run every high/low factor combination.",
            "The supplied random seed is retained for reproducibility.",
        ),
        warnings=tuple(warnings),
        provenance=(NIST_FACTORIAL_SOURCE,),
    )


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
        numerator = -(a + iteration) * (qab + iteration) * x / (
            (a + even) * (qap + even)
        )
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
        "responses",
    )


def _regularized_beta(x: float, a: float, b: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = exp(
        lgamma(a + b)
        - lgamma(a)
        - lgamma(b)
        + a * log(x)
        + b * log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _beta_continued_fraction(a, b, x) / a
    return 1.0 - front * _beta_continued_fraction(b, a, 1.0 - x) / b


def _f_survival(value: float, numerator_df: int, denominator_df: int) -> float | None:
    if numerator_df <= 0 or denominator_df <= 0:
        return None
    if value <= 0.0:
        return 1.0
    if not isfinite(value):
        return 0.0
    transformed = denominator_df / (denominator_df + numerator_df * value)
    probability = _regularized_beta(
        transformed, denominator_df / 2.0, numerator_df / 2.0
    )
    return min(1.0, max(0.0, probability))


def analyze_full_factorial_2level(
    factors: Sequence[FactorDefinition],
    responses: Sequence[float],
    *,
    response_name: str = "Response",
    replicates: int = 1,
    center_points: int = 0,
    randomize: bool = True,
    seed: int = 0,
    interaction_order: int = 2,
) -> ResultBundle:
    """Fit an orthogonal coded model to a generated two-level full factorial design."""

    design = full_factorial_2level(
        factors,
        replicates=replicates,
        center_points=center_points,
        randomize=randomize,
        seed=seed,
    )
    rows = design.tables["design"]
    values = finite_values(responses, "responses")
    if len(values) != len(rows):
        raise AnalysisInputError(
            "response_count_mismatch",
            f"Expected {len(rows)} responses in run order, received {len(values)}.",
            "responses",
        )
    normalized_name = response_name.strip()
    if not normalized_name:
        raise AnalysisInputError(
            "empty_response_name", "Response name cannot be empty.", "response_name"
        )
    factor_names = [factor["name"] for factor in design.parameters["factors"]]
    if (
        isinstance(interaction_order, bool)
        or not isinstance(interaction_order, int)
        or not 1 <= interaction_order <= len(factor_names)
    ):
        raise AnalysisInputError(
            "invalid_interaction_order",
            f"Interaction order must be an integer from 1 to {len(factor_names)}.",
            "interaction_order",
        )

    terms = [
        term
        for order in range(1, interaction_order + 1)
        for term in combinations(factor_names, order)
    ]
    if len(terms) + 1 > 256:
        raise AnalysisInputError(
            "model_too_large",
            "The selected model exceeds the 256-coefficient safety limit.",
            "interaction_order",
        )

    coded_columns: dict[tuple[str, ...], list[float]] = {}
    for term in terms:
        coded_columns[term] = [
            float(_product(row["coded"][name] for name in term)) for row in rows
        ]
    intercept = sum(values) / len(values)
    coefficients: dict[tuple[str, ...], float] = {}
    term_sums_of_squares: dict[tuple[str, ...], float] = {}
    for term, column in coded_columns.items():
        denominator = sum(value * value for value in column)
        if denominator == 0.0:
            raise AnalysisInputError(
                "unestimable_term",
                f"Term {':'.join(term)} cannot be estimated from this design.",
                "interaction_order",
            )
        coefficient = (
            sum(x * y for x, y in zip(column, values, strict=True)) / denominator
        )
        coefficients[term] = coefficient
        term_sums_of_squares[term] = coefficient * coefficient * denominator

    fitted = [
        intercept
        + sum(coefficients[term] * coded_columns[term][index] for term in terms)
        for index in range(len(rows))
    ]
    residuals = [
        observed - predicted
        for observed, predicted in zip(values, fitted, strict=True)
    ]
    residual_ss = sum(value * value for value in residuals)
    total_ss = sum((value - intercept) ** 2 for value in values)
    model_ss = sum(term_sums_of_squares.values())
    model_df = len(terms)
    residual_df = len(values) - len(terms) - 1
    total_df = len(values) - 1
    residual_ms = residual_ss / residual_df if residual_df > 0 else None
    model_ms = model_ss / model_df if model_df > 0 else None
    model_f = _f_statistic(model_ms, residual_ms)
    r_squared = 1.0 - residual_ss / total_ss if total_ss > 0.0 else None
    adjusted_r_squared = (
        1.0 - (residual_ss / residual_df) / (total_ss / total_df)
        if total_ss > 0.0 and residual_df > 0
        else None
    )

    grouped: dict[tuple[int, ...], list[float]] = {}
    for row, response in zip(rows, values, strict=True):
        key = tuple(int(row["coded"][name]) for name in factor_names)
        grouped.setdefault(key, []).append(response)
    pure_error_ss = sum(
        sum((value - sum(group) / len(group)) ** 2 for value in group)
        for group in grouped.values()
    )
    pure_error_df = len(values) - len(grouped)
    lack_of_fit_df = residual_df - pure_error_df
    lack_of_fit_ss = max(0.0, residual_ss - pure_error_ss)
    pure_error_ms = pure_error_ss / pure_error_df if pure_error_df > 0 else None
    lack_of_fit_ms = lack_of_fit_ss / lack_of_fit_df if lack_of_fit_df > 0 else None
    lack_of_fit_f = _f_statistic(lack_of_fit_ms, pure_error_ms)

    coefficient_rows: list[dict[str, object]] = [
        {
            "term": "Constant",
            "order": 0,
            "coefficient": intercept,
            "effect": None,
            "sum_of_squares": None,
            "f_value": None,
            "p_value": None,
        }
    ]
    for term in terms:
        term_ms = term_sums_of_squares[term]
        term_f = _f_statistic(term_ms, residual_ms)
        coefficient_rows.append(
            {
                "term": ":".join(term),
                "order": len(term),
                "coefficient": coefficients[term],
                "effect": 2.0 * coefficients[term],
                "sum_of_squares": term_sums_of_squares[term],
                "f_value": term_f,
                "p_value": (
                    _f_survival(term_f, 1, residual_df)
                    if term_f is not None
                    else None
                ),
            }
        )

    model_p = (
        _f_survival(model_f, model_df, residual_df) if model_f is not None else None
    )
    lack_of_fit_p = (
        _f_survival(lack_of_fit_f, lack_of_fit_df, pure_error_df)
        if lack_of_fit_f is not None
        else None
    )
    anova = [
        _anova_row("Model", model_df, model_ss, model_ms, model_f, model_p),
        _anova_row(
            "Residual Error", residual_df, residual_ss, residual_ms, None, None
        ),
        _anova_row(
            "Lack of Fit",
            lack_of_fit_df,
            lack_of_fit_ss,
            lack_of_fit_ms,
            lack_of_fit_f,
            lack_of_fit_p,
        ),
        _anova_row(
            "Pure Error", pure_error_df, pure_error_ss, pure_error_ms, None, None
        ),
        _anova_row("Total", total_df, total_ss, None, None, None),
    ]
    residual_scale = (
        sqrt(residual_ms) if residual_ms is not None and residual_ms > 0.0 else None
    )
    residual_table = [
        {
            "run_order": row["run_order"],
            "standard_order": row["standard_order"],
            "point_type": row["point_type"],
            "observed": observed,
            "fitted": predicted,
            "residual": residual,
            "scaled_residual": residual / residual_scale if residual_scale else None,
        }
        for row, observed, predicted, residual in zip(
            rows, values, fitted, residuals, strict=True
        )
    ]
    sorted_residuals = sorted(residuals)
    normal = NormalDist()
    normal_scores = [
        normal.inv_cdf(index / (len(values) + 1.0))
        for index in range(1, len(values) + 1)
    ]

    warnings = list(design.warnings)
    if residual_df <= 0:
        warnings.append(
            "The selected model is saturated; error variance, F tests, and p-values are unavailable."
        )
    elif residual_ms == 0.0:
        warnings.append(
            "Residual variance is zero; F tests and p-values are undefined for this exact fit."
        )
    if pure_error_df <= 0:
        warnings.append(
            "No replicated factor settings are available, so pure error and lack-of-fit testing are unavailable."
        )
    payload = {
        **design.parameters,
        "responses": values,
        "response_name": normalized_name,
        "interaction_order": interaction_order,
    }
    return ResultBundle(
        analysis_type="doe.full_factorial_2level_analysis",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters=payload,
        tables={
            "coefficients": coefficient_rows,
            "anova": anova,
            "residuals": residual_table,
        },
        plots={
            "effects": {
                "terms": [row["term"] for row in coefficient_rows[1:]],
                "effects": [row["effect"] for row in coefficient_rows[1:]],
            },
            "residuals_vs_fitted": {"fitted": fitted, "residuals": residuals},
            "residuals_vs_run_order": {
                "run_order": [row["run_order"] for row in rows],
                "residuals": residuals,
            },
            "normal_probability": {
                "theoretical_quantiles": normal_scores,
                "ordered_residuals": sorted_residuals,
            },
        },
        diagnostics={
            "response_name": normalized_name,
            "observation_count": len(values),
            "coefficient_count": len(terms) + 1,
            "residual_degrees_of_freedom": residual_df,
            "residual_standard_deviation": residual_scale,
            "r_squared": r_squared,
            "adjusted_r_squared": adjusted_r_squared,
            "pure_error_degrees_of_freedom": pure_error_df,
            "lack_of_fit_degrees_of_freedom": lack_of_fit_df,
        },
        assumptions=(
            "Responses correspond one-for-one to the generated design run order.",
            "The coded model is linear in the selected main effects and interactions.",
            "Residuals are expected to be independent with constant variance and "
            "approximately normal when inferential statistics are interpreted.",
        ),
        warnings=tuple(warnings),
        provenance=(NIST_FACTORIAL_SOURCE, NIST_DOE_MODEL_SOURCE, NIST_RESIDUAL_SOURCE),
    )


def _product(values: Iterable[int]) -> int:
    result = 1
    for value in values:
        result *= int(value)
    return result


def _f_statistic(numerator_ms: float | None, denominator_ms: float | None) -> float | None:
    if numerator_ms is None or denominator_ms is None:
        return None
    if denominator_ms == 0.0:
        return None
    return numerator_ms / denominator_ms


def _anova_row(
    source: str,
    degrees_of_freedom: int,
    sum_of_squares: float,
    mean_square: float | None,
    f_value: float | None,
    p_value: float | None,
) -> dict[str, object]:
    return {
        "source": source,
        "degrees_of_freedom": degrees_of_freedom,
        "sum_of_squares": sum_of_squares,
        "mean_square": mean_square,
        "f_value": f_value,
        "p_value": p_value,
    }
