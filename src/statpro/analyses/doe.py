"""Design generation for two-level full factorial experiments."""

from __future__ import annotations

import random
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from itertools import combinations
from math import atan2, cos, exp, isfinite, lgamma, log, log1p, sin, sqrt
from statistics import NormalDist, median
from typing import Sequence

from statpro.analyses.common import finite_values, input_digest
from statpro.domain.errors import AnalysisInputError
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_FACTORIAL_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.3.3.3.1 Two-level full factorial designs",
    url="https://www.itl.nist.gov/div898/handbook/pri/section3/pri3331.htm",
)

NIST_FRACTIONAL_FACTORIAL_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.3.3.4.4 Fractional factorial specifications and resolution",
    url="https://www.itl.nist.gov/div898/handbook/pri/section3/pri3344.htm",
)

NIST_MIRROR_FOLDOVER_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.3.3.8.1 Mirror-Image foldover designs",
    url="https://www.itl.nist.gov/div898/handbook/pri/section3/pri3381.htm",
)

NIST_CENTRAL_COMPOSITE_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.3.3.6.1 Central Composite Designs",
    url="https://www.itl.nist.gov/div898/handbook/pri/section3/pri3361.htm",
)

NIST_RESPONSE_SURFACE_MODEL_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.5.3.1.4 Quadratic response-surface optimization",
    url="https://www.itl.nist.gov/div898/handbook/pri/section5/pri5314.htm",
)

MINITAB_CCD_ALPHA_SOURCE = ProvenanceSource(
    title="Minitab public documentation: alpha in a central composite design",
    url=(
        "https://support.minitab.com/en-us/minitab/help-and-how-to/"
        "statistical-modeling/doe/supporting-topics/response-surface-designs/"
        "what-is-alpha-in-a-central-composite-design/"
    ),
)

MINITAB_FRACTIONAL_FACTORIAL_SOURCE = ProvenanceSource(
    title="Minitab public documentation: 2-level factorial generators and alias structure",
    url=(
        "https://support.minitab.com/en-us/minitab/help-and-how-to/"
        "statistical-modeling/doe/how-to/factorial/create-factorial-design/"
        "create-2-level-factorial-specify-generators/examine-the-design/all-statistics/"
    ),
)

NIST_PLACKETT_BURMAN_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.3.3.5 Plackett-Burman designs",
    url="https://www.itl.nist.gov/div898/handbook/pri/section3/pri335.htm",
)

MINITAB_PLACKETT_BURMAN_SOURCE = ProvenanceSource(
    title="Minitab public documentation: Plackett-Burman designs",
    url=(
        "https://support.minitab.com/en-us/minitab/help-and-how-to/"
        "statistical-modeling/doe/supporting-topics/factorial-and-screening-designs/"
        "plackett-burman-designs/"
    ),
)

MINITAB_FACTORIAL_EFFECTS_SOURCE = ProvenanceSource(
    title="Minitab public documentation: methods and formulas for factorial effects plots",
    url=(
        "https://support.minitab.com/en-us/minitab/help-and-how-to/"
        "statistical-modeling/doe/how-to/factorial/analyze-variability/"
        "methods-and-formulas/effects-plots/"
    ),
)

NIST_DOE_MODEL_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.4.3 How to model DOE data",
    url="https://www.itl.nist.gov/div898/handbook/pri/section4/pri43.htm",
)

NIST_RESIDUAL_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.2.4 Are the model residuals well-behaved?",
    url="https://www.itl.nist.gov/div898/handbook/pri/section2/pri24.htm",
)

NIST_FITTED_MODEL_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.6.1.10 Using the Fitted Model",
    url="https://www.itl.nist.gov/div898/handbook/pri/section6/pri61a.htm",
)

NIST_DESIRABILITY_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 5.5.3.2.2 Multiple responses: The desirability approach",
    url="https://www.itl.nist.gov/div898/handbook/pri/section5/pri5322.htm",
)

MINITAB_RESPONSE_OPTIMIZER_SOURCE = ProvenanceSource(
    title="Minitab public documentation: Individual and composite desirability",
    url="https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/using-fitted-models/supporting-topics/response-optimization/what-are-individual-desirability-and-composite-desirability/",
)


@dataclass(frozen=True, slots=True)
class FactorDefinition:
    name: str
    low: float
    high: float


@dataclass(frozen=True, slots=True)
class GeneratorDefinition:
    factor: str
    terms: Sequence[str]


@dataclass(frozen=True, slots=True)
class ResponseObjective:
    name: str
    responses: Sequence[float]
    goal: str
    target: float
    lower: float | None = None
    upper: float | None = None
    weight: float = 1.0
    importance: float = 1.0


def _normalize_factors(
    factors: Sequence[FactorDefinition],
    *,
    max_count: int = 12,
    design_name: str = "two-level full factorial design",
) -> list[FactorDefinition]:
    if len(factors) < 2:
        raise AnalysisInputError(
            "insufficient_factors",
            f"A {design_name} requires at least two factors.",
            "factors",
        )
    if len(factors) > max_count:
        raise AnalysisInputError(
            "too_many_factors",
            f"The bounded {design_name} generator supports at most {max_count} factors.",
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


_PLACKETT_BURMAN_RUNS = (12, 20, 24, 28, 32, 36, 40, 44, 48)

_PLACKETT_BURMAN_CYCLIC_SEEDS = {
    12: "++-+++---+-",
    20: "++--++++-+-+----++-",
    24: "+++++-+-++--++--+-+----",
    32: "----+-+-+++-++---+++++--++-+--+",
    36: "-+-+++---+++++-+++--+----+-+-++--+-",
    44: "++--+-+--+++-+++++---+-+++-----+---++-+-++-",
    48: "+++++-++++--+-+-+++--+--++-++---+-+-++----+----",
}

_PLACKETT_BURMAN_28_ROWS = (
    "+-++++----+---+--+++-+-++-+",
    "++-+++-----++--+---++++-++-",
    "-+++++---+---+--+-+-+-++-++",
    "---+-++++--+-+- --++-+++-+-+".replace(" ", ""),
    "---++-++++----++--++--++++-",
    "----+++++-+-+---+--+++-+-++",
    "+++---+-+--+--+-+-+-++-+++-",
    "+++---++-+--+----+++-++--++",
    "+++----++-+--+-+---++-+++-+",
)


def _signs(pattern: str) -> list[int]:
    return [1 if character == "+" else -1 for character in pattern]


def _cyclic_plackett_burman_matrix(runs: int) -> list[list[int]]:
    seed = _signs(_PLACKETT_BURMAN_CYCLIC_SEEDS[runs])
    width = runs - 1
    if len(seed) != width:
        raise RuntimeError(f"Invalid internal Plackett-Burman seed for {runs} runs.")
    matrix = [
        [seed[(row + column) % width] for column in range(width)]
        for row in range(width)
    ]
    matrix.append([-1] * width)
    return matrix


def _plackett_burman_28_matrix() -> list[list[int]]:
    initial_rows = [_signs(pattern) for pattern in _PLACKETT_BURMAN_28_ROWS]
    if any(len(row) != 27 for row in initial_rows):
        raise RuntimeError("Invalid internal 28-run Plackett-Burman rows.")
    matrix: list[list[int]] = []
    for block_shift in range(3):
        for row in initial_rows:
            blocks = (row[:9], row[9:18], row[18:27])
            matrix.append(
                blocks[block_shift]
                + blocks[(block_shift + 1) % 3]
                + blocks[(block_shift + 2) % 3]
            )
    matrix.append([-1] * 27)
    return matrix


def _plackett_burman_40_matrix() -> list[list[int]]:
    base_design = _cyclic_plackett_burman_matrix(20)
    hadamard_20 = [[1, *row] for row in base_design]
    hadamard_40 = [
        [*row, *row] for row in hadamard_20
    ] + [
        [*row, *(-value for value in row)] for row in hadamard_20
    ]
    return [row[1:] for row in hadamard_40]


def _plackett_burman_matrix(runs: int) -> tuple[list[list[int]], str]:
    if runs == 28:
        return _plackett_burman_28_matrix(), "published-28-run-block-construction"
    if runs == 40:
        return _plackett_burman_40_matrix(), "doubled-20-run-hadamard-construction"
    return _cyclic_plackett_burman_matrix(runs), "published-cyclic-seed"


def _verify_screening_matrix(matrix: Sequence[Sequence[int]]) -> tuple[bool, bool]:
    column_count = len(matrix[0])
    balanced = all(sum(row[column] for row in matrix) == 0 for column in range(column_count))
    pairwise_orthogonal = all(
        sum(row[left] * row[right] for row in matrix) == 0
        for left, right in combinations(range(column_count), 2)
    )
    return balanced, pairwise_orthogonal


def plackett_burman_design(
    factors: Sequence[FactorDefinition],
    *,
    runs: int | None = None,
    replicates: int = 1,
    center_points: int = 0,
    randomize: bool = True,
    seed: int = 0,
) -> ResultBundle:
    """Generate a bounded Plackett-Burman main-effects screening design."""

    normalized = _normalize_factors(
        factors,
        max_count=47,
        design_name="Plackett-Burman screening design",
    )
    if runs is not None and (isinstance(runs, bool) or not isinstance(runs, int)):
        raise AnalysisInputError("invalid_runs", "Runs must be an integer.", "runs")
    if runs is None:
        runs = next(
            (candidate for candidate in _PLACKETT_BURMAN_RUNS if len(normalized) < candidate),
            None,
        )
        if runs is None:
            raise AnalysisInputError(
                "too_many_factors",
                "No supported Plackett-Burman design can hold the requested factors.",
                "factors",
            )
    elif runs not in _PLACKETT_BURMAN_RUNS:
        raise AnalysisInputError(
            "unsupported_runs",
            "Runs must be one of 12, 20, 24, 28, 32, 36, 40, 44, or 48; "
            "use a two-level factorial design for 8 or 16 runs.",
            "runs",
        )
    if len(normalized) >= runs:
        raise AnalysisInputError(
            "too_many_factors_for_runs",
            "The factor count must be less than the selected run count.",
            "factors",
        )
    if isinstance(replicates, bool) or not isinstance(replicates, int) or replicates < 1:
        raise AnalysisInputError(
            "invalid_replicates", "Replicates must be a positive integer.", "replicates"
        )
    if (
        isinstance(center_points, bool)
        or not isinstance(center_points, int)
        or center_points < 0
    ):
        raise AnalysisInputError(
            "invalid_center_points",
            "Center points must be a nonnegative integer.",
            "center_points",
        )
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise AnalysisInputError("invalid_seed", "Random seed must be an integer.", "seed")

    full_matrix, construction = _plackett_burman_matrix(runs)
    balanced, pairwise_orthogonal = _verify_screening_matrix(full_matrix)
    if not balanced or not pairwise_orthogonal:
        raise RuntimeError(f"Internal {runs}-run Plackett-Burman matrix verification failed.")

    factor_names = [factor.name for factor in normalized]
    active_matrix = [row[: len(normalized)] for row in full_matrix]
    rows: list[dict[str, object]] = []
    for replicate in range(1, replicates + 1):
        for standard_index, matrix_row in enumerate(active_matrix, start=1):
            coded = dict(zip(factor_names, matrix_row, strict=True))
            actual = {
                factor.name: factor.high if coded[factor.name] == 1 else factor.low
                for factor in normalized
            }
            rows.append(
                {
                    "standard_order": standard_index,
                    "replicate": replicate,
                    "point_type": "factorial",
                    "coded": coded,
                    "actual": actual,
                }
            )

    center_coded = {factor.name: 0 for factor in normalized}
    center_actual = {factor.name: (factor.low + factor.high) / 2 for factor in normalized}
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

    warnings = [
        "Resolution III screening aliases main effects with two-factor interactions; "
        "interpret effects only when interactions are reasonably negligible.",
        "Confirm selected factors with a follow-up factorial or response-surface experiment.",
    ]
    if center_points:
        warnings.append(
            "Center points can indicate aggregate curvature but cannot identify separate quadratic terms."
        )
    if not randomize:
        warnings.append(
            "Runs are not randomized; time-related nuisance factors may be confounded with factor effects."
        )

    factor_payload = [asdict(factor) for factor in normalized]
    payload = {
        "factors": factor_payload,
        "runs": runs,
        "replicates": replicates,
        "center_points": center_points,
        "randomize": randomize,
        "seed": seed,
    }
    return ResultBundle(
        analysis_type="doe.plackett_burman",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters=payload,
        tables={"design": rows},
        plots={},
        diagnostics={
            "factor_count": len(normalized),
            "base_run_count": runs,
            "total_run_count": runs * replicates + center_points,
            "available_factor_columns": runs - 1,
            "unused_factor_columns": runs - 1 - len(normalized),
            "resolution": 3,
            "resolution_label": "III",
            "balanced": balanced,
            "pairwise_orthogonal": pairwise_orthogonal,
            "screening_only": True,
            "construction": construction,
        },
        assumptions=(
            "Two-factor and higher-order interactions are negligible during screening.",
            "Each factor has exactly two quantitative levels.",
            "The supplied random seed is retained for reproducibility.",
        ),
        warnings=tuple(warnings),
        provenance=(NIST_PLACKETT_BURMAN_SOURCE, MINITAB_PLACKETT_BURMAN_SOURCE),
    )


def analyze_plackett_burman(
    factors: Sequence[FactorDefinition],
    responses: Sequence[float],
    *,
    response_name: str = "Response",
    runs: int | None = None,
    replicates: int = 1,
    center_points: int = 0,
    randomize: bool = True,
    seed: int = 0,
    alpha: float = 0.05,
) -> ResultBundle:
    """Estimate Plackett-Burman main effects and prepare confirmation candidates."""

    design = plackett_burman_design(
        factors,
        runs=runs,
        replicates=replicates,
        center_points=center_points,
        randomize=randomize,
        seed=seed,
    )
    rows = design.tables["design"]
    values = finite_values(responses, "responses")
    normalized_name = response_name.strip()
    if not normalized_name:
        raise AnalysisInputError(
            "empty_response_name", "Response name cannot be empty.", "response_name"
        )
    normalized_alpha = finite_values([alpha], "alpha")[0]
    if not 0.001 <= normalized_alpha <= 0.5:
        raise AnalysisInputError(
            "invalid_alpha", "Alpha must be between 0.001 and 0.5.", "alpha"
        )

    factor_payload = design.parameters["factors"]
    factor_names = [str(factor["name"]) for factor in factor_payload]
    terms = [(name,) for name in factor_names]
    intercept, coefficients, coded_columns, term_sums_of_squares = (
        _fit_orthogonal_model(rows, factor_names, values, terms, field="responses")
    )
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
    model_ss = sum(term_sums_of_squares.values())
    total_ss = sum((value - intercept) ** 2 for value in values)
    residual_df = len(values) - len(terms) - 1
    residual_ms = residual_ss / residual_df if residual_df > 0 else None
    residual_scale = (
        sqrt(residual_ms) if residual_ms is not None and residual_ms > 0.0 else None
    )

    raw_effects = [2.0 * coefficients[term] for term in terms]
    inference_method = "residual_error" if residual_df > 0 else "lenth_pse"
    lenth_pse: float | None = None
    margin_of_error: float | None = None
    t_critical: float | None = None
    if residual_df <= 0:
        absolute_effects = [abs(effect) for effect in raw_effects]
        initial_scale = 1.5 * median(absolute_effects)
        retained = [effect for effect in absolute_effects if effect < 2.5 * initial_scale]
        if not retained:
            retained = absolute_effects
        lenth_pse = 1.5 * median(retained)
        t_critical = _two_sided_t_critical(
            normalized_alpha, max(len(raw_effects) / 3.0, 1.0)
        )
        margin_of_error = t_critical * lenth_pse
    else:
        t_critical = _two_sided_t_critical(normalized_alpha, float(residual_df))

    coefficient_rows: list[dict[str, object]] = []
    pareto_rows: list[dict[str, object]] = []
    confirmation_rows: list[dict[str, object]] = []
    factors_by_name = {str(factor["name"]): factor for factor in factor_payload}
    for term, effect in zip(terms, raw_effects, strict=True):
        name = term[0]
        column_ss = sum(value * value for value in coded_columns[term])
        effect_standard_error = (
            2.0 * sqrt(residual_ms / column_ss)
            if residual_ms is not None and residual_ms > 0.0
            else None
        )
        standardized_effect = effect / effect_standard_error if effect_standard_error else None
        p_value = (
            _f_survival(standardized_effect * standardized_effect, 1, residual_df)
            if standardized_effect is not None
            else None
        )
        significant = (
            p_value <= normalized_alpha
            if p_value is not None
            else bool(margin_of_error is not None and abs(effect) > margin_of_error)
        )
        coefficient_rows.append(
            {
                "term": name,
                "coefficient": coefficients[term],
                "effect": effect,
                "sum_of_squares": term_sums_of_squares[term],
                "standard_error": effect_standard_error,
                "standardized_effect": standardized_effect,
                "p_value": p_value,
                "significant": significant,
            }
        )
        pareto_rows.append(
            {
                "term": name,
                "coefficient": coefficients[term],
                "effect": effect,
                "absolute_effect": abs(effect),
                "display_value": (
                    abs(standardized_effect)
                    if standardized_effect is not None
                    else abs(effect)
                ),
                "standard_error": effect_standard_error,
                "standardized_effect": standardized_effect,
                "p_value": p_value,
                "significant": significant,
            }
        )
        if significant:
            factor = factors_by_name[name]
            confirmation_rows.append(
                {
                    "factor": name,
                    "effect": effect,
                    "direction_for_increase": "high" if effect > 0 else "low",
                    "suggested_level": factor["high"] if effect > 0 else factor["low"],
                    "opposite_level": factor["low"] if effect > 0 else factor["high"],
                    "selection_method": inference_method,
                }
            )

    pareto_rows.sort(
        key=lambda row: (-float(row["display_value"]), str(row["term"]))
    )
    model_df = len(terms)
    model_ms = model_ss / model_df
    model_f = _f_statistic(model_ms, residual_ms)
    anova = [
        _anova_row(
            "Main Effects",
            model_df,
            model_ss,
            model_ms,
            model_f,
            _f_survival(model_f, model_df, residual_df) if model_f is not None else None,
        ),
        _anova_row("Residual Error", residual_df, residual_ss, residual_ms, None, None),
        _anova_row("Total", len(values) - 1, total_ss, None, None, None),
    ]
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
    factorial_values = [
        value
        for row, value in zip(rows, values, strict=True)
        if row["point_type"] == "factorial"
    ]
    center_values = [
        value
        for row, value in zip(rows, values, strict=True)
        if row["point_type"] == "center"
    ]
    curvature = (
        [
            {
                "factorial_mean": sum(factorial_values) / len(factorial_values),
                "center_mean": sum(center_values) / len(center_values),
                "difference": sum(center_values) / len(center_values)
                - sum(factorial_values) / len(factorial_values),
                "center_point_count": len(center_values),
            }
        ]
        if center_values
        else []
    )

    warnings = list(design.warnings)
    if inference_method == "lenth_pse":
        warnings.append(
            "The main-effects model has no residual degrees of freedom; significance "
            "flags use Lenth's sparse-effects PSE, not replicated error."
        )
    else:
        warnings.append(
            "Residual-error tests assume omitted effects and interactions are "
            "negligible; screening aliases can inflate this error term."
        )
        if residual_ms == 0.0:
            warnings.append(
                "Residual variance is zero; standardized effects, F tests, and "
                "p-values are undefined for this exact fit."
            )
    if not confirmation_rows:
        warnings.append(
            "No effect crossed the selected screening threshold; do not promote a "
            "factor solely from its rank."
        )
    if center_values:
        warnings.append(
            "The center-point difference is descriptive aggregate curvature; this "
            "screening model does not estimate individual quadratic terms."
        )

    payload = {
        **design.parameters,
        "responses": values,
        "response_name": normalized_name,
        "alpha": normalized_alpha,
    }
    return ResultBundle(
        analysis_type="doe.plackett_burman_analysis",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters=payload,
        tables={
            "coefficients": coefficient_rows,
            "anova": anova,
            "residuals": residual_table,
            "ranked_effects": pareto_rows,
            "confirmation_candidates": confirmation_rows,
            "curvature": curvature,
        },
        plots={
            "pareto": {
                "terms": [row["term"] for row in pareto_rows],
                "values": [row["display_value"] for row in pareto_rows],
                "scale": "standardized_effect" if residual_df > 0 else "effect",
                "reference_line": t_critical if residual_df > 0 else margin_of_error,
            },
            "residuals_vs_run_order": {
                "run_order": [row["run_order"] for row in rows],
                "residuals": residuals,
            },
        },
        diagnostics={
            **design.diagnostics,
            "response_name": normalized_name,
            "observation_count": len(values),
            "residual_degrees_of_freedom": residual_df,
            "residual_standard_deviation": residual_scale,
            "r_squared": 1.0 - residual_ss / total_ss if total_ss > 0.0 else None,
            "alpha": normalized_alpha,
            "inference_method": inference_method,
            "lenth_pse": lenth_pse,
            "pareto_reference_line": t_critical if residual_df > 0 else margin_of_error,
            "confirmation_candidate_count": len(confirmation_rows),
        },
        assumptions=(
            "Responses correspond one-for-one to the generated design run order.",
            "Two-factor and higher-order interactions are negligible relative to the "
            "main effects during screening.",
            "Lenth inference, when used, assumes sparse active effects and is a "
            "screening rule rather than replicated-error evidence.",
            "Confirmation candidates require an independent follow-up experiment "
            "before process decisions.",
        ),
        warnings=tuple(warnings),
        provenance=(
            NIST_PLACKETT_BURMAN_SOURCE,
            NIST_DOE_MODEL_SOURCE,
            MINITAB_FACTORIAL_EFFECTS_SOURCE,
        ),
    )


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


def _effect_label(word: frozenset[str], factor_order: Mapping[str, int]) -> str:
    if not word:
        return "I"
    return "*".join(sorted(word, key=factor_order.__getitem__))


def _defining_relation(
    generator_words: Sequence[frozenset[str]],
) -> list[frozenset[str]]:
    relation: list[frozenset[str]] = [frozenset()]
    for generator_word in generator_words:
        relation += [word.symmetric_difference(generator_word) for word in relation]
    return relation


def _roman_resolution(resolution: int) -> str:
    labels = {
        2: "II",
        3: "III",
        4: "IV",
        5: "V",
        6: "VI",
        7: "VII",
        8: "VIII",
        9: "IX",
        10: "X",
        11: "XI",
        12: "XII",
    }
    return labels.get(resolution, str(resolution))


def fractional_factorial_2level(
    factors: Sequence[FactorDefinition],
    generators: Sequence[GeneratorDefinition],
    *,
    replicates: int = 1,
    foldover: bool = False,
    randomize: bool = True,
    seed: int = 0,
) -> ResultBundle:
    """Generate a regular positive 2^(k-p) fractional factorial design.

    Generator right-hand sides intentionally reference base factors only. This keeps the
    defining contrast subgroup explicit and rejects ambiguous recursive specifications.
    """

    normalized = _normalize_factors(factors)
    if not generators:
        raise AnalysisInputError(
            "missing_generators",
            "A fractional factorial design requires at least one generator.",
            "generators",
        )
    if len(generators) > 8:
        raise AnalysisInputError(
            "too_many_generators",
            "At most 8 generators are supported to bound alias-table growth.",
            "generators",
        )
    if isinstance(replicates, bool) or not isinstance(replicates, int) or replicates < 1:
        raise AnalysisInputError(
            "invalid_replicates", "Replicates must be a positive integer.", "replicates"
        )
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise AnalysisInputError("invalid_seed", "Random seed must be an integer.", "seed")

    factor_names = [factor.name for factor in normalized]
    factor_by_name = {factor.name: factor for factor in normalized}
    generated_names: list[str] = []
    raw_generators: list[tuple[str, list[str]]] = []
    for index, generator in enumerate(generators):
        if not isinstance(generator.factor, str):
            raise AnalysisInputError(
                "unknown_generated_factor",
                f"Generator {index + 1} must name one of the supplied factors.",
                f"generators[{index}].factor",
            )
        if not isinstance(generator.terms, Sequence) or isinstance(
            generator.terms, (str, bytes)
        ) or any(
            not isinstance(term, str) for term in generator.terms
        ):
            raise AnalysisInputError(
                "invalid_generator_terms",
                "Generator terms must be an array of factor names.",
                f"generators[{index}].terms",
            )
        factor = generator.factor.strip()
        terms = [term.strip() for term in generator.terms]
        if not factor or factor not in factor_by_name:
            raise AnalysisInputError(
                "unknown_generated_factor",
                f"Generator {index + 1} must name one of the supplied factors.",
                f"generators[{index}].factor",
            )
        if factor in generated_names:
            raise AnalysisInputError(
                "duplicate_generator_factor",
                f"Factor '{factor}' has more than one generator.",
                f"generators[{index}].factor",
            )
        if len(terms) < 2:
            raise AnalysisInputError(
                "generator_too_short",
                "Each generator must contain at least two base-factor terms.",
                f"generators[{index}].terms",
            )
        if any(not term for term in terms) or len(set(terms)) != len(terms):
            raise AnalysisInputError(
                "invalid_generator_terms",
                "Generator terms must be nonempty and unique.",
                f"generators[{index}].terms",
            )
        generated_names.append(factor)
        raw_generators.append((factor, terms))

    base_names = [name for name in factor_names if name not in generated_names]
    if len(base_names) < 2:
        raise AnalysisInputError(
            "insufficient_base_factors",
            "At least two independent base factors are required.",
            "generators",
        )
    base_name_set = set(base_names)
    for index, (factor, terms) in enumerate(raw_generators):
        unknown_terms = [term for term in terms if term not in base_name_set]
        if unknown_terms:
            raise AnalysisInputError(
                "generator_requires_base_factors",
                (
                    f"Generator for '{factor}' may reference base factors only; "
                    f"invalid terms: {', '.join(unknown_terms)}."
                ),
                f"generators[{index}].terms",
            )

    base_run_count = 2 ** len(base_names)
    total_run_count = base_run_count * replicates
    if total_run_count * (2 if foldover else 1) > 100_000:
        raise AnalysisInputError(
            "design_too_large",
            "The requested design exceeds the 100,000-run safety limit.",
            "factors",
        )

    factor_order = {name: index for index, name in enumerate(factor_names)}
    normalized_generators = [
        {"factor": factor, "terms": terms, "expression": f"{factor}={'*'.join(terms)}"}
        for factor, terms in raw_generators
    ]
    generator_words = [
        frozenset((factor, *terms)) for factor, terms in raw_generators
    ]
    relation = _defining_relation(generator_words)
    non_identity_words = relation[1:]
    resolution = min(len(word) for word in non_identity_words)
    if resolution < 3:
        raise AnalysisInputError(
            "resolution_too_low",
            "Generators must define a resolution III or higher design.",
            "generators",
        )
    relation_labels = [
        _effect_label(word, factor_order)
        for word in sorted(
            non_identity_words,
            key=lambda item: (len(item), _effect_label(item, factor_order)),
        )
    ]

    if foldover and resolution != 3:
        raise AnalysisInputError(
            "mirror_foldover_requires_resolution_iii",
            "A full mirror-image foldover is supported only for resolution III designs; "
            "for this design it would not provide the documented main-effect de-aliasing benefit.",
            "foldover",
        )
    effective_relation = (
        [word for word in relation if len(word) % 2 == 0] if foldover else relation
    )
    effective_non_identity_words = effective_relation[1:]
    augmented_resolution = (
        min(len(word) for word in effective_non_identity_words)
        if effective_non_identity_words
        else len(factor_names) + 1
    )
    effective_relation_labels = [
        _effect_label(word, factor_order)
        for word in sorted(
            effective_non_identity_words,
            key=lambda item: (len(item), _effect_label(item, factor_order)),
        )
    ]

    rows: list[dict[str, object]] = []
    for replicate in range(1, replicates + 1):
        replicate_rows: list[dict[str, object]] = []
        for standard_index in range(base_run_count):
            coded = {
                name: (1 if standard_index & (1 << index) else -1)
                for index, name in enumerate(base_names)
            }
            for factor, terms in raw_generators:
                coded[factor] = 1
                for term in terms:
                    coded[factor] *= coded[term]
            ordered_coded = {name: coded[name] for name in factor_names}
            actual = {
                name: (
                    factor_by_name[name].high
                    if ordered_coded[name] == 1
                    else factor_by_name[name].low
                )
                for name in factor_names
            }
            replicate_rows.append(
                {
                    "standard_order": standard_index + 1,
                    "replicate": replicate,
                    "fraction_phase": "original",
                    "point_type": "factorial",
                    "coded": ordered_coded,
                    "actual": actual,
                }
            )
        rows.extend(replicate_rows)
        if foldover:
            for original in replicate_rows:
                original_coded = original["coded"]
                folded_coded = {name: -original_coded[name] for name in factor_names}
                folded_actual = {
                    name: (
                        factor_by_name[name].high
                        if folded_coded[name] == 1
                        else factor_by_name[name].low
                    )
                    for name in factor_names
                }
                rows.append(
                    {
                        "standard_order": original["standard_order"],
                        "replicate": replicate,
                        "fraction_phase": "foldover",
                        "point_type": "factorial",
                        "coded": folded_coded,
                        "actual": folded_actual,
                    }
                )

    if randomize:
        random.Random(seed).shuffle(rows)
    for run_order, row in enumerate(rows, start=1):
        row["run_order"] = run_order

    def aliases_for(word: frozenset[str]) -> list[str]:
        aliases = {
            word.symmetric_difference(defining_word)
            for defining_word in effective_relation
        }
        return [
            _effect_label(alias, factor_order)
            for alias in sorted(
                aliases, key=lambda item: (len(item), _effect_label(item, factor_order))
            )
        ]

    main_effect_aliases = [
        {"effect": name, "alias_set": aliases_for(frozenset((name,)))}
        for name in factor_names
    ]
    two_factor_aliases = [
        {
            "effect": f"{left}*{right}",
            "alias_set": aliases_for(frozenset((left, right))),
        }
        for left, right in combinations(factor_names, 2)
    ]

    warnings: list[str] = []
    if resolution == 3:
        warnings.append(
            "Resolution III aliases main effects with two-factor interactions; "
            "use it for screening with that limitation explicit."
        )
    elif resolution == 4:
        warnings.append(
            "Resolution IV keeps main effects clear of two-factor interactions, "
            "but two-factor interactions can alias each other."
        )
    if not randomize:
        warnings.append(
            "Runs are not randomized; time-related nuisance factors may be confounded with factor effects."
        )
    if foldover:
        warnings.append(
            "The mirror-image foldover clears main effects from two-factor interactions, "
            "but two-factor interactions can remain aliased with one another."
        )

    factor_payload = [asdict(factor) for factor in normalized]
    payload = {
        "factors": factor_payload,
        "generators": normalized_generators,
        "replicates": replicates,
        "foldover": foldover,
        "randomize": randomize,
        "seed": seed,
    }
    return ResultBundle(
        analysis_type="doe.fractional_factorial_2level",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters=payload,
        tables={
            "design": rows,
            "generators": normalized_generators,
            "defining_relation": [
                {
                    "identity": "I",
                    "words": effective_relation_labels,
                    "expression": "I"
                    + (
                        " = " + " = ".join(effective_relation_labels)
                        if effective_relation_labels
                        else ""
                    ),
                }
            ],
            "original_defining_relation": [
                {
                    "identity": "I",
                    "words": relation_labels,
                    "expression": "I = " + " = ".join(relation_labels),
                }
            ],
            "main_effect_aliases": main_effect_aliases,
            "two_factor_aliases": two_factor_aliases,
        },
        plots={},
        diagnostics={
            "factor_count": len(factor_names),
            "base_factor_count": len(base_names),
            "generated_factor_count": len(generated_names),
            "fraction": f"1/{2 ** len(generated_names)}",
            "design_notation": f"2^({len(factor_names)}-{len(generated_names)})",
            "resolution": resolution,
            "resolution_label": _roman_resolution(resolution),
            "factorial_run_count": base_run_count,
            "total_run_count": total_run_count * (2 if foldover else 1),
            "original_run_count": total_run_count,
            "foldover_run_count": total_run_count if foldover else 0,
            "main_effects_clear_of_two_factor_interactions": foldover or resolution >= 4,
            "augmented_resolution": augmented_resolution,
            "balanced": True,
            "orthogonal": True,
            "regular_fraction": True,
        },
        assumptions=(
            "Each factor has exactly two quantitative levels.",
            "Every generator is a positive product of independent base-factor columns.",
            "Alias sets follow the complete defining contrast subgroup for this regular fraction.",
            "The supplied random seed is retained for reproducibility.",
        ),
        warnings=tuple(warnings),
        provenance=(
            NIST_FRACTIONAL_FACTORIAL_SOURCE,
            MINITAB_FRACTIONAL_FACTORIAL_SOURCE,
            *((NIST_MIRROR_FOLDOVER_SOURCE,) if foldover else ()),
        ),
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


def _f_survival(value: float, numerator_df: float, denominator_df: float) -> float | None:
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


def _two_sided_t_critical(alpha: float, degrees_of_freedom: float) -> float:
    """Invert the two-sided t tail through the F(1, df) relationship."""

    lower = 0.0
    upper = 1.0
    while (_f_survival(upper * upper, 1.0, degrees_of_freedom) or 0.0) > alpha:
        upper *= 2.0
        if upper > 1_000_000.0:
            raise AnalysisInputError(
                "distribution_not_converged",
                "The t-distribution critical value calculation did not converge.",
                "alpha",
            )
    for _ in range(100):
        midpoint = (lower + upper) / 2.0
        tail = _f_survival(midpoint * midpoint, 1.0, degrees_of_freedom)
        if tail is None or tail > alpha:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2.0


def _model_terms(
    factor_names: Sequence[str], interaction_order: int
) -> list[tuple[str, ...]]:
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
    return terms


def _fit_orthogonal_model(
    rows: Sequence[Mapping[str, object]],
    factor_names: Sequence[str],
    values: Sequence[float],
    terms: Sequence[tuple[str, ...]],
    *,
    field: str,
) -> tuple[
    float,
    dict[tuple[str, ...], float],
    dict[tuple[str, ...], list[float]],
    dict[tuple[str, ...], float],
]:
    if len(values) != len(rows):
        raise AnalysisInputError(
            "response_count_mismatch",
            f"Expected {len(rows)} responses in run order, received {len(values)}.",
            field,
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
    return intercept, coefficients, coded_columns, term_sums_of_squares


def analyze_fractional_factorial_2level(
    factors: Sequence[FactorDefinition],
    generators: Sequence[GeneratorDefinition],
    responses: Sequence[float],
    *,
    response_name: str = "Response",
    replicates: int = 1,
    foldover: bool = False,
    randomize: bool = True,
    seed: int = 0,
    alpha: float = 0.05,
) -> ResultBundle:
    """Estimate main effects for a regular fraction or its full mirror foldover.

    The bounded first analysis scope fits one representative per main-effect alias chain.
    It does not silently fit mutually aliased interaction columns.
    """

    design = fractional_factorial_2level(
        factors,
        generators,
        replicates=replicates,
        foldover=foldover,
        randomize=randomize,
        seed=seed,
    )
    rows = design.tables["design"]
    values = finite_values(responses, "responses")
    normalized_name = response_name.strip()
    if not normalized_name:
        raise AnalysisInputError(
            "empty_response_name", "Response name cannot be empty.", "response_name"
        )
    normalized_alpha = finite_values([alpha], "alpha")[0]
    if not 0.001 <= normalized_alpha <= 0.5:
        raise AnalysisInputError(
            "invalid_alpha", "Alpha must be between 0.001 and 0.5.", "alpha"
        )

    factor_names = [str(factor["name"]) for factor in design.parameters["factors"]]
    terms = [(name,) for name in factor_names]
    intercept, coefficients, coded_columns, term_sums_of_squares = (
        _fit_orthogonal_model(rows, factor_names, values, terms, field="responses")
    )
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
    model_ss = sum(term_sums_of_squares.values())
    total_ss = sum((value - intercept) ** 2 for value in values)
    residual_df = len(values) - len(terms) - 1
    residual_ms = residual_ss / residual_df if residual_df > 0 else None
    residual_scale = (
        sqrt(residual_ms) if residual_ms is not None and residual_ms > 0.0 else None
    )

    raw_effects = [2.0 * coefficients[term] for term in terms]
    inference_method = (
        "inference_unavailable_zero_residual"
        if residual_df > 0 and residual_ms == 0.0
        else "residual_error"
        if residual_df > 0
        else "lenth_pse"
    )
    lenth_pse: float | None = None
    reference_line: float | None = None
    t_critical: float | None = None
    if residual_df > 0 and residual_ms == 0.0:
        reference_line = None
    elif residual_df > 0:
        t_critical = _two_sided_t_critical(normalized_alpha, float(residual_df))
        reference_line = t_critical
    else:
        absolute_effects = [abs(effect) for effect in raw_effects]
        initial_scale = 1.5 * median(absolute_effects)
        retained = [effect for effect in absolute_effects if effect < 2.5 * initial_scale]
        if not retained:
            retained = absolute_effects
        lenth_pse = 1.5 * median(retained)
        t_critical = _two_sided_t_critical(
            normalized_alpha, max(len(raw_effects) / 3.0, 1.0)
        )
        reference_line = t_critical * lenth_pse

    aliases = {
        str(row["effect"]): list(row["alias_set"])
        for row in design.tables["main_effect_aliases"]
    }
    coefficient_rows: list[dict[str, object]] = []
    ranked_rows: list[dict[str, object]] = []
    for term, effect in zip(terms, raw_effects, strict=True):
        name = term[0]
        column_ss = sum(value * value for value in coded_columns[term])
        standard_error = (
            2.0 * sqrt(residual_ms / column_ss)
            if residual_ms is not None and residual_ms > 0.0
            else None
        )
        standardized_effect = effect / standard_error if standard_error else None
        p_value = (
            _f_survival(standardized_effect * standardized_effect, 1, residual_df)
            if standardized_effect is not None
            else None
        )
        significant = (
            p_value <= normalized_alpha
            if p_value is not None
            else bool(
                residual_df <= 0
                and reference_line is not None
                and abs(effect) > reference_line
            )
        )
        alias_set = aliases[name]
        row = {
            "term": name,
            "coefficient": coefficients[term],
            "effect": effect,
            "sum_of_squares": term_sums_of_squares[term],
            "standard_error": standard_error,
            "standardized_effect": standardized_effect,
            "p_value": p_value,
            "significant": significant,
            "alias_set": alias_set,
            "clear_of_two_factor_interactions": bool(
                design.diagnostics["main_effects_clear_of_two_factor_interactions"]
            ),
        }
        coefficient_rows.append(row)
        ranked_rows.append(
            {
                **row,
                "absolute_effect": abs(effect),
                "display_value": (
                    abs(standardized_effect)
                    if standardized_effect is not None
                    else abs(effect)
                ),
            }
        )
    ranked_rows.sort(key=lambda row: (-float(row["display_value"]), str(row["term"])))

    residual_rows = [
        {
            "run_order": int(row["run_order"]),
            "fraction_phase": str(row["fraction_phase"]),
            "observed": observed,
            "fitted": predicted,
            "residual": residual,
        }
        for row, observed, predicted, residual in zip(
            rows, values, fitted, residuals, strict=True
        )
    ]
    warnings = list(design.warnings)
    warnings.append(
        "Only main-effect representatives are fitted; reported effects inherit the displayed "
        "alias sets unless the foldover diagnostic marks them clear of two-factor interactions."
    )
    if residual_df > 0 and replicates == 1:
        warnings.append(
            "Residual error is model residual rather than replicated pure error; omitted interactions "
            "can inflate it, so significance is screening evidence only."
        )
    if residual_df > 0 and residual_ms == 0.0:
        warnings.append(
            "The selected model has zero residual variation, so standard errors and p-values "
            "are not reported without an independent error estimate."
        )
    if residual_df <= 0:
        warnings.append(
            "The saturated main-effects model uses Lenth's sparse-effects PSE; this depends on the "
            "assumption that most effects are negligible."
        )

    payload = {
        **design.parameters,
        "responses": values,
        "response_name": normalized_name,
        "alpha": normalized_alpha,
        "model_scope": "main_effect_representatives",
    }
    return ResultBundle(
        analysis_type="doe.fractional_factorial_2level_analysis",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters=payload,
        tables={
            "coefficients": coefficient_rows,
            "ranked_effects": ranked_rows,
            "residuals": residual_rows,
            "defining_relation": design.tables["defining_relation"],
            "main_effect_aliases": design.tables["main_effect_aliases"],
        },
        plots={
            "effects": {
                "terms": [str(row["term"]) for row in ranked_rows],
                "effects": [float(row["effect"]) for row in ranked_rows],
                "display_values": [float(row["display_value"]) for row in ranked_rows],
                "reference_line": reference_line,
            },
            "residuals_vs_fitted": {"fitted": fitted, "residuals": residuals},
            "residuals_vs_run_order": {
                "run_order": [int(row["run_order"]) for row in rows],
                "residuals": residuals,
            },
        },
        diagnostics={
            **design.diagnostics,
            "response_name": normalized_name,
            "observation_count": len(values),
            "coefficient_count": len(terms) + 1,
            "residual_degrees_of_freedom": residual_df,
            "residual_standard_deviation": residual_scale,
            "r_squared": 1.0 - residual_ss / total_ss if total_ss > 0.0 else None,
            "model_sum_of_squares": model_ss,
            "residual_sum_of_squares": residual_ss,
            "inference_method": inference_method,
            "lenth_pse": lenth_pse,
            "pareto_reference_line": reference_line,
            "alpha": normalized_alpha,
            "model_scope": "main_effect_representatives",
        },
        assumptions=(
            "Responses correspond one-for-one to the generated design run order.",
            "Only one representative from each main-effect alias chain is estimated.",
            "Effects not separated by the design are interpreted jointly, not as unique causes.",
            "Residual inference assumes independent, constant-variance, approximately normal errors.",
        ),
        warnings=tuple(warnings),
        provenance=(
            *design.provenance,
            NIST_DOE_MODEL_SOURCE,
            MINITAB_FACTORIAL_EFFECTS_SOURCE,
        ),
    )


def central_composite_design(
    factors: Sequence[FactorDefinition],
    *,
    design_type: str = "rotatable",
    center_points: int = 5,
    replicates: int = 1,
    randomize: bool = True,
    seed: int = 0,
) -> ResultBundle:
    """Generate a bounded full-factorial central composite design."""

    normalized = _normalize_factors(
        factors,
        max_count=6,
        design_name="central composite response-surface design",
    )
    if design_type not in {"rotatable", "face_centered"}:
        raise AnalysisInputError(
            "invalid_ccd_type",
            "Central composite design type must be 'rotatable' or 'face_centered'.",
            "design_type",
        )
    if (
        isinstance(center_points, bool)
        or not isinstance(center_points, int)
        or center_points < 1
    ):
        raise AnalysisInputError(
            "invalid_center_points",
            "A central composite design requires at least one center point.",
            "center_points",
        )
    if isinstance(replicates, bool) or not isinstance(replicates, int) or replicates < 1:
        raise AnalysisInputError(
            "invalid_replicates", "Replicates must be a positive integer.", "replicates"
        )
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise AnalysisInputError("invalid_seed", "Random seed must be an integer.", "seed")

    factor_names = [factor.name for factor in normalized]
    factorial_runs = 2 ** len(normalized)
    alpha = factorial_runs ** 0.25 if design_type == "rotatable" else 1.0
    base_coded: list[tuple[str, dict[str, float]]] = []
    for standard_index in range(factorial_runs):
        base_coded.append(
            (
                "factorial",
                {
                    name: (1.0 if standard_index & (1 << index) else -1.0)
                    for index, name in enumerate(factor_names)
                },
            )
        )
    for active_name in factor_names:
        for sign in (-1.0, 1.0):
            base_coded.append(
                (
                    "axial",
                    {
                        name: sign * alpha if name == active_name else 0.0
                        for name in factor_names
                    },
                )
            )

    factor_by_name = {factor.name: factor for factor in normalized}

    def actual_values(coded: Mapping[str, float]) -> dict[str, float]:
        return {
            name: (
                (factor_by_name[name].low + factor_by_name[name].high) / 2.0
                + coded[name]
                * (factor_by_name[name].high - factor_by_name[name].low)
                / 2.0
            )
            for name in factor_names
        }

    rows: list[dict[str, object]] = []
    for replicate in range(1, replicates + 1):
        for standard_index, (point_type, coded) in enumerate(base_coded, start=1):
            rows.append(
                {
                    "standard_order": standard_index,
                    "replicate": replicate,
                    "point_type": point_type,
                    "coded": coded,
                    "actual": actual_values(coded),
                }
            )
    center_coded = {name: 0.0 for name in factor_names}
    for center_index in range(1, center_points + 1):
        rows.append(
            {
                "standard_order": None,
                "replicate": center_index,
                "point_type": "center",
                "coded": center_coded.copy(),
                "actual": actual_values(center_coded),
            }
        )
    if len(rows) > 100_000:
        raise AnalysisInputError(
            "design_too_large",
            "The requested design exceeds the 100,000-run safety limit.",
            "replicates",
        )
    if randomize:
        random.Random(seed).shuffle(rows)
    for run_order, row in enumerate(rows, start=1):
        row["run_order"] = run_order

    warnings = [
        "The supplied low/high levels define the factorial cube; rotatable axial points can lie outside those levels.",
        "Verify every generated setting is physically safe and feasible before running the experiment.",
    ]
    if design_type == "face_centered":
        warnings.append(
            "A face-centered CCD keeps axial points at the stated low/high levels but is not rotatable."
        )
    if not randomize:
        warnings.append(
            "Runs are not randomized; time-related nuisance factors may be confounded with model terms."
        )

    factor_payload = [asdict(factor) for factor in normalized]
    payload = {
        "factors": factor_payload,
        "design_type": design_type,
        "center_points": center_points,
        "replicates": replicates,
        "randomize": randomize,
        "seed": seed,
    }
    return ResultBundle(
        analysis_type="doe.central_composite",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters=payload,
        tables={"design": rows},
        plots={},
        diagnostics={
            "factor_count": len(normalized),
            "factorial_run_count": factorial_runs,
            "axial_run_count": 2 * len(normalized),
            "center_point_count": center_points,
            "total_run_count": len(rows),
            "alpha": alpha,
            "rotatable": design_type == "rotatable",
            "quadratic_model_estimable": len(rows)
            >= 1 + 2 * len(normalized) + len(normalized) * (len(normalized) - 1) // 2,
        },
        assumptions=(
            "All factors are quantitative and can be operated at every generated setting.",
            "The stated low/high levels map to coded -1/+1 in the factorial cube.",
            "The factorial portion is a complete two-level factorial.",
            "The supplied random seed is retained for reproducibility.",
        ),
        warnings=tuple(warnings),
        provenance=(
            NIST_CENTRAL_COMPOSITE_SOURCE,
            MINITAB_CCD_ALPHA_SOURCE,
        ),
    )


def _invert_matrix(matrix: Sequence[Sequence[float]], *, field: str) -> list[list[float]]:
    size = len(matrix)
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
                "The selected response-surface model is not estimable from this design.",
                field,
            )
        augmented[column], augmented[pivot_row] = (
            augmented[pivot_row],
            augmented[column],
        )
        pivot = augmented[column][column]
        augmented[column] = [value / pivot for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            multiplier = augmented[row][column]
            if multiplier == 0.0:
                continue
            augmented[row] = [
                value - multiplier * pivot_value
                for value, pivot_value in zip(
                    augmented[row], augmented[column], strict=True
                )
            ]
    return [row[size:] for row in augmented]


def _quadratic_model_columns(
    rows: Sequence[Mapping[str, object]], factor_names: Sequence[str]
) -> tuple[list[dict[str, object]], list[list[float]]]:
    terms: list[dict[str, object]] = [{"term": "Constant", "kind": "constant"}]
    terms.extend({"term": name, "kind": "linear", "factors": (name,)} for name in factor_names)
    terms.extend(
        {
            "term": f"{left}*{right}",
            "kind": "interaction",
            "factors": (left, right),
        }
        for left, right in combinations(factor_names, 2)
    )
    terms.extend(
        {"term": f"{name}^2", "kind": "square", "factors": (name, name)}
        for name in factor_names
    )
    matrix: list[list[float]] = []
    for row in rows:
        coded = row["coded"]
        values = [1.0]
        values.extend(float(coded[name]) for name in factor_names)
        values.extend(
            float(coded[left]) * float(coded[right])
            for left, right in combinations(factor_names, 2)
        )
        values.extend(float(coded[name]) ** 2 for name in factor_names)
        matrix.append(values)
    return terms, matrix


def analyze_central_composite(
    factors: Sequence[FactorDefinition],
    responses: Sequence[float],
    *,
    response_name: str = "Response",
    design_type: str = "rotatable",
    center_points: int = 5,
    replicates: int = 1,
    randomize: bool = True,
    seed: int = 0,
    alpha: float = 0.05,
) -> ResultBundle:
    """Fit a complete coded second-order model to a generated CCD."""

    design = central_composite_design(
        factors,
        design_type=design_type,
        center_points=center_points,
        replicates=replicates,
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
    normalized_alpha = finite_values([alpha], "alpha")[0]
    if not 0.001 <= normalized_alpha <= 0.5:
        raise AnalysisInputError(
            "invalid_alpha", "Alpha must be between 0.001 and 0.5.", "alpha"
        )

    factor_payload = design.parameters["factors"]
    factor_names = [str(factor["name"]) for factor in factor_payload]
    terms, matrix = _quadratic_model_columns(rows, factor_names)
    coefficient_count = len(terms)
    xtx = [
        [
            sum(row[left] * row[right] for row in matrix)
            for right in range(coefficient_count)
        ]
        for left in range(coefficient_count)
    ]
    xty = [
        sum(row[column] * value for row, value in zip(matrix, values, strict=True))
        for column in range(coefficient_count)
    ]
    inverse = _invert_matrix(xtx, field="responses")
    coefficients = [
        sum(inverse[row][column] * xty[column] for column in range(coefficient_count))
        for row in range(coefficient_count)
    ]
    fitted = [
        sum(value * coefficient for value, coefficient in zip(row, coefficients, strict=True))
        for row in matrix
    ]
    residuals = [
        observed - predicted
        for observed, predicted in zip(values, fitted, strict=True)
    ]
    intercept = sum(values) / len(values)
    total_ss = sum((value - intercept) ** 2 for value in values)
    residual_ss = sum(value * value for value in residuals)
    model_ss = max(0.0, total_ss - residual_ss)
    model_df = coefficient_count - 1
    residual_df = len(values) - coefficient_count
    residual_ms = residual_ss / residual_df if residual_df > 0 else None
    model_ms = model_ss / model_df if model_df > 0 else None
    model_f = _f_statistic(model_ms, residual_ms)

    coefficient_rows: list[dict[str, object]] = []
    for index, (term, coefficient) in enumerate(zip(terms, coefficients, strict=True)):
        standard_error = (
            sqrt(max(0.0, residual_ms * inverse[index][index]))
            if residual_ms is not None and residual_ms > 0.0
            else None
        )
        t_value = coefficient / standard_error if standard_error else None
        p_value = (
            _f_survival(t_value * t_value, 1, residual_df)
            if t_value is not None
            else None
        )
        coefficient_rows.append(
            {
                **term,
                "coefficient": coefficient,
                "standard_error": standard_error,
                "t_value": t_value,
                "p_value": p_value,
                "significant": p_value <= normalized_alpha if p_value is not None else False,
            }
        )

    grouped: dict[tuple[float, ...], list[float]] = {}
    for row, response in zip(rows, values, strict=True):
        key = tuple(float(row["coded"][name]) for name in factor_names)
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
    anova = [
        {
            "source": "Model",
            "degrees_of_freedom": model_df,
            "sum_of_squares": model_ss,
            "mean_square": model_ms,
            "f_value": model_f,
            "p_value": _f_survival(model_f, model_df, residual_df) if model_f is not None else None,
        },
        {
            "source": "Error",
            "degrees_of_freedom": residual_df,
            "sum_of_squares": residual_ss,
            "mean_square": residual_ms,
            "f_value": None,
            "p_value": None,
        },
        {
            "source": "Lack of Fit",
            "degrees_of_freedom": lack_of_fit_df,
            "sum_of_squares": lack_of_fit_ss,
            "mean_square": lack_of_fit_ms,
            "f_value": lack_of_fit_f,
            "p_value": (
                _f_survival(lack_of_fit_f, lack_of_fit_df, pure_error_df)
                if lack_of_fit_f is not None
                else None
            ),
        },
        {
            "source": "Pure Error",
            "degrees_of_freedom": pure_error_df,
            "sum_of_squares": pure_error_ss,
            "mean_square": pure_error_ms,
            "f_value": None,
            "p_value": None,
        },
        {
            "source": "Total",
            "degrees_of_freedom": len(values) - 1,
            "sum_of_squares": total_ss,
            "mean_square": None,
            "f_value": None,
            "p_value": None,
        },
    ]
    residual_table = [
        {
            "run_order": int(row["run_order"]),
            "point_type": str(row["point_type"]),
            "observed": observed,
            "fitted": predicted,
            "residual": residual,
        }
        for row, observed, predicted, residual in zip(
            rows, values, fitted, residuals, strict=True
        )
    ]

    warnings = list(design.warnings)
    if residual_df <= 0:
        warnings.append(
            "The quadratic model has no residual degrees of freedom; standard errors and p-values are unavailable."
        )
    elif residual_ms == 0.0:
        warnings.append(
            "The fitted model has zero residual variation; inferential statistics require an independent error estimate."
        )
    if pure_error_df <= 0:
        warnings.append(
            "No replicated design setting is available, so pure error and lack of fit cannot be separated."
        )

    payload = {
        **design.parameters,
        "responses": values,
        "response_name": normalized_name,
        "alpha": normalized_alpha,
    }
    return ResultBundle(
        analysis_type="doe.central_composite_analysis",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters=payload,
        tables={
            "coefficients": coefficient_rows,
            "anova": anova,
            "residuals": residual_table,
            "design": rows,
        },
        plots={
            "residuals_vs_fitted": {"fitted": fitted, "residuals": residuals},
            "residuals_vs_run_order": {
                "run_order": [int(row["run_order"]) for row in rows],
                "residuals": residuals,
            },
        },
        diagnostics={
            **design.diagnostics,
            "response_name": normalized_name,
            "observation_count": len(values),
            "coefficient_count": coefficient_count,
            "residual_degrees_of_freedom": residual_df,
            "residual_standard_deviation": (
                sqrt(residual_ms) if residual_ms is not None and residual_ms > 0.0 else None
            ),
            "r_squared": 1.0 - residual_ss / total_ss if total_ss > 0.0 else None,
            "adjusted_r_squared": (
                1.0
                - (residual_ss / residual_df) / (total_ss / (len(values) - 1))
                if residual_df > 0 and total_ss > 0.0
                else None
            ),
            "pure_error_degrees_of_freedom": pure_error_df,
            "lack_of_fit_degrees_of_freedom": lack_of_fit_df,
        },
        assumptions=(
            "Responses correspond one-for-one to the generated design run order.",
            "A complete coded second-order model adequately represents the response in the explored region.",
            "Residuals are independent with constant variance and approximately normal for inference.",
            "A non-significant lack-of-fit result requires replicated settings with nonzero pure error.",
        ),
        warnings=tuple(warnings),
        provenance=(
            *design.provenance,
            NIST_RESPONSE_SURFACE_MODEL_SOURCE,
            NIST_RESIDUAL_SOURCE,
        ),
    )


def _symmetric_eigenvalues(matrix: Sequence[Sequence[float]]) -> list[float]:
    """Return eigenvalues of a small real symmetric matrix with Jacobi rotations."""

    values = [[float(value) for value in row] for row in matrix]
    size = len(values)
    if size == 0:
        return []
    scale = max(1.0, max(abs(value) for row in values for value in row))
    tolerance = 1e-12 * scale
    for _ in range(100 * size * size):
        pivot_row, pivot_column = max(
            ((row, column) for row in range(size) for column in range(row + 1, size)),
            key=lambda item: abs(values[item[0]][item[1]]),
            default=(0, 0),
        )
        if pivot_row == pivot_column or abs(values[pivot_row][pivot_column]) <= tolerance:
            break
        app = values[pivot_row][pivot_row]
        aqq = values[pivot_column][pivot_column]
        apq = values[pivot_row][pivot_column]
        angle = 0.5 * atan2(2.0 * apq, aqq - app)
        cosine = cos(angle)
        sine = sin(angle)
        for index in range(size):
            if index in {pivot_row, pivot_column}:
                continue
            aip = values[index][pivot_row]
            aiq = values[index][pivot_column]
            rotated_p = cosine * aip - sine * aiq
            rotated_q = sine * aip + cosine * aiq
            values[index][pivot_row] = values[pivot_row][index] = rotated_p
            values[index][pivot_column] = values[pivot_column][index] = rotated_q
        values[pivot_row][pivot_row] = (
            cosine * cosine * app - 2.0 * sine * cosine * apq + sine * sine * aqq
        )
        values[pivot_column][pivot_column] = (
            sine * sine * app + 2.0 * sine * cosine * apq + cosine * cosine * aqq
        )
        values[pivot_row][pivot_column] = values[pivot_column][pivot_row] = 0.0
    return sorted(values[index][index] for index in range(size))


def explore_central_composite_surface(
    factors: Sequence[FactorDefinition],
    responses: Sequence[float],
    *,
    response_name: str = "Response",
    design_type: str = "rotatable",
    center_points: int = 5,
    replicates: int = 1,
    randomize: bool = True,
    seed: int = 0,
    alpha: float = 0.05,
    plot_factors: Sequence[str] | None = None,
    hold_values: Mapping[str, float] | None = None,
    grid_size: int = 21,
) -> ResultBundle:
    """Classify a quadratic stationary point and evaluate a two-factor surface grid."""

    if (
        isinstance(grid_size, bool)
        or not isinstance(grid_size, int)
        or not 5 <= grid_size <= 51
        or grid_size % 2 == 0
    ):
        raise AnalysisInputError(
            "invalid_grid_size",
            "Surface grid size must be an odd integer between 5 and 51.",
            "grid_size",
        )
    analysis = analyze_central_composite(
        factors,
        responses,
        response_name=response_name,
        design_type=design_type,
        center_points=center_points,
        replicates=replicates,
        randomize=randomize,
        seed=seed,
        alpha=alpha,
    )
    factor_payload = analysis.parameters["factors"]
    factor_names = [str(factor["name"]) for factor in factor_payload]
    selected = list(plot_factors) if plot_factors is not None else factor_names[:2]
    if len(selected) != 2 or len(set(selected)) != 2 or any(name not in factor_names for name in selected):
        raise AnalysisInputError(
            "invalid_plot_factors",
            "Surface exploration requires two distinct factor names from the fitted model.",
            "plot_factors",
        )
    normalized_holds: dict[str, float] = {}
    for name, value in (hold_values or {}).items():
        if name not in factor_names:
            raise AnalysisInputError(
                "unknown_hold_factor", f"Unknown hold factor '{name}'.", "hold_values"
            )
        if name in selected:
            raise AnalysisInputError(
                "plotted_factor_held",
                f"Plotted factor '{name}' cannot also have a hold value.",
                "hold_values",
            )
        normalized_value = finite_values([value], f"hold_values.{name}")[0]
        if not -1.0 <= normalized_value <= 1.0:
            raise AnalysisInputError(
                "hold_value_out_of_range",
                "Hold values must remain inside the coded factorial cube [-1, 1].",
                "hold_values",
            )
        normalized_holds[name] = normalized_value

    coefficient_rows = analysis.tables["coefficients"]
    coefficient_by_term = {
        str(row["term"]): float(row["coefficient"]) for row in coefficient_rows
    }
    linear = [coefficient_by_term[name] for name in factor_names]
    quadratic = [[0.0 for _ in factor_names] for _ in factor_names]
    for index, name in enumerate(factor_names):
        quadratic[index][index] = coefficient_by_term[f"{name}^2"]
    for left_index, right_index in combinations(range(len(factor_names)), 2):
        interaction = coefficient_by_term[
            f"{factor_names[left_index]}*{factor_names[right_index]}"
        ]
        quadratic[left_index][right_index] = interaction / 2.0
        quadratic[right_index][left_index] = interaction / 2.0

    eigenvalues = _symmetric_eigenvalues(quadratic)
    eigen_tolerance = 1e-9 * max(1.0, *(abs(value) for value in eigenvalues))
    if all(value > eigen_tolerance for value in eigenvalues):
        classification = "minimum"
    elif all(value < -eigen_tolerance for value in eigenvalues):
        classification = "maximum"
    elif any(value > eigen_tolerance for value in eigenvalues) and any(
        value < -eigen_tolerance for value in eigenvalues
    ):
        classification = "saddle"
    else:
        classification = "ridge"

    def predict(coded: Mapping[str, float]) -> float:
        prediction = coefficient_by_term["Constant"]
        prediction += sum(coefficient_by_term[name] * coded[name] for name in factor_names)
        prediction += sum(
            coefficient_by_term[f"{left}*{right}"] * coded[left] * coded[right]
            for left, right in combinations(factor_names, 2)
        )
        prediction += sum(
            coefficient_by_term[f"{name}^2"] * coded[name] * coded[name]
            for name in factor_names
        )
        return prediction

    factor_by_name = {str(factor["name"]): factor for factor in factor_payload}

    def actual(coded: Mapping[str, float]) -> dict[str, float]:
        return {
            name: (
                (float(factor_by_name[name]["low"]) + float(factor_by_name[name]["high"]))
                / 2.0
                + coded[name]
                * (float(factor_by_name[name]["high"]) - float(factor_by_name[name]["low"]))
                / 2.0
            )
            for name in factor_names
        }

    stationary_coded: dict[str, float] | None = None
    try:
        inverse = _invert_matrix(quadratic, field="responses")
        stationary_values = [
            -0.5 * sum(inverse[row][column] * linear[column] for column in range(len(linear)))
            for row in range(len(linear))
        ]
        stationary_coded = dict(zip(factor_names, stationary_values, strict=True))
    except AnalysisInputError as error:
        if error.detail.code != "singular_design_matrix":
            raise

    stationary_row = {
        "classification": classification,
        "available": stationary_coded is not None,
        "coded": stationary_coded,
        "actual": actual(stationary_coded) if stationary_coded is not None else None,
        "predicted_response": predict(stationary_coded) if stationary_coded is not None else None,
        "inside_factorial_cube": (
            all(abs(value) <= 1.0 + 1e-12 for value in stationary_coded.values())
            if stationary_coded is not None
            else None
        ),
    }
    canonical_rows = [
        {"axis": index, "eigenvalue": value}
        for index, value in enumerate(eigenvalues, start=1)
    ]

    grid_values = [-1.0 + 2.0 * index / (grid_size - 1) for index in range(grid_size)]
    grid: list[dict[str, object]] = []
    x_name, y_name = selected
    for y_index, y_value in enumerate(grid_values):
        for x_index, x_value in enumerate(grid_values):
            coded = {
                name: normalized_holds.get(name, 0.0) for name in factor_names
            }
            coded[x_name] = x_value
            coded[y_name] = y_value
            actual_values = actual(coded)
            grid.append(
                {
                    "x_index": x_index,
                    "y_index": y_index,
                    "x_coded": x_value,
                    "y_coded": y_value,
                    "x_actual": actual_values[x_name],
                    "y_actual": actual_values[y_name],
                    "predicted_response": predict(coded),
                }
            )
    grid_minimum = min(grid, key=lambda row: float(row["predicted_response"]))
    grid_maximum = max(grid, key=lambda row: float(row["predicted_response"]))

    warnings = list(analysis.warnings)
    if stationary_coded is None:
        warnings.append(
            "The quadratic coefficient matrix is singular, so a unique stationary point is unavailable."
        )
    elif not stationary_row["inside_factorial_cube"]:
        warnings.append(
            "The stationary point lies outside the coded factorial cube; treat it as extrapolation and do not use it without confirmation runs."
        )
    if classification in {"saddle", "ridge"}:
        warnings.append(
            "The stationary point is not a unique maximum or minimum; inspect the canonical directions and bounded surface grid."
        )
    warnings.append(
        "Grid extrema describe only the selected two-factor slice with all other factors held at the reported coded values."
    )

    payload = {
        **analysis.parameters,
        "plot_factors": selected,
        "hold_values": normalized_holds,
        "grid_size": grid_size,
    }
    return ResultBundle(
        analysis_type="doe.central_composite_surface",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters=payload,
        tables={
            **analysis.tables,
            "stationary_point": [stationary_row],
            "canonical_axes": canonical_rows,
            "surface_grid": grid,
            "surface_slice_extrema": [
                {"kind": "minimum", **grid_minimum},
                {"kind": "maximum", **grid_maximum},
            ],
        },
        plots={
            **analysis.plots,
            "response_surface": {
                "x_factor": x_name,
                "y_factor": y_name,
                "x_coded": grid_values,
                "y_coded": grid_values,
                "predicted_response": [
                    [
                        float(grid[y_index * grid_size + x_index]["predicted_response"])
                        for x_index in range(grid_size)
                    ]
                    for y_index in range(grid_size)
                ],
                "hold_values": {
                    name: normalized_holds.get(name, 0.0)
                    for name in factor_names
                    if name not in selected
                },
            },
        },
        diagnostics={
            **analysis.diagnostics,
            "stationary_classification": classification,
            "stationary_point_available": stationary_coded is not None,
            "stationary_point_inside_factorial_cube": stationary_row[
                "inside_factorial_cube"
            ],
            "canonical_eigenvalues": eigenvalues,
            "surface_grid_size": grid_size,
            "surface_grid_point_count": len(grid),
            "plot_factors": selected,
        },
        assumptions=(
            *analysis.assumptions,
            "The response-surface grid is evaluated inside the coded factorial cube for two selected factors.",
            "All unplotted factors are held at explicitly reported coded values, defaulting to zero.",
        ),
        warnings=tuple(warnings),
        provenance=analysis.provenance,
    )


def individual_desirability(
    prediction: float,
    *,
    goal: str,
    target: float,
    lower: float | None = None,
    upper: float | None = None,
    weight: float = 1.0,
) -> float:
    """Convert one fitted response to a bounded Derringer-Suich desirability."""

    value = finite_values([prediction], "prediction")[0]
    normalized_target = finite_values([target], "target")[0]
    normalized_weight = finite_values([weight], "weight")[0]
    if not 0.1 <= normalized_weight <= 10.0:
        raise AnalysisInputError(
            "invalid_desirability_weight",
            "Desirability weight must be between 0.1 and 10.",
            "weight",
        )
    if goal == "maximize":
        if lower is None:
            raise AnalysisInputError(
                "missing_desirability_bound",
                "A maximize objective requires a lower bound.",
                "lower",
            )
        normalized_lower = finite_values([lower], "lower")[0]
        if normalized_lower >= normalized_target:
            raise AnalysisInputError(
                "invalid_desirability_bounds",
                "A maximize objective requires lower < target.",
                "lower",
            )
        if value <= normalized_lower:
            return 0.0
        if value >= normalized_target:
            return 1.0
        return ((value - normalized_lower) / (normalized_target - normalized_lower)) ** normalized_weight
    if goal == "minimize":
        if upper is None:
            raise AnalysisInputError(
                "missing_desirability_bound",
                "A minimize objective requires an upper bound.",
                "upper",
            )
        normalized_upper = finite_values([upper], "upper")[0]
        if normalized_target >= normalized_upper:
            raise AnalysisInputError(
                "invalid_desirability_bounds",
                "A minimize objective requires target < upper.",
                "upper",
            )
        if value <= normalized_target:
            return 1.0
        if value >= normalized_upper:
            return 0.0
        return ((normalized_upper - value) / (normalized_upper - normalized_target)) ** normalized_weight
    if goal == "target":
        if lower is None or upper is None:
            raise AnalysisInputError(
                "missing_desirability_bound",
                "A target objective requires lower and upper bounds.",
                "lower",
            )
        normalized_lower, normalized_upper = finite_values(
            [lower, upper], "desirability_bounds"
        )
        if not normalized_lower < normalized_target < normalized_upper:
            raise AnalysisInputError(
                "invalid_desirability_bounds",
                "A target objective requires lower < target < upper.",
                "target",
            )
        if value <= normalized_lower or value >= normalized_upper:
            return 0.0
        if value == normalized_target:
            return 1.0
        if value < normalized_target:
            return ((value - normalized_lower) / (normalized_target - normalized_lower)) ** normalized_weight
        return ((normalized_upper - value) / (normalized_upper - normalized_target)) ** normalized_weight
    raise AnalysisInputError(
        "invalid_optimization_goal",
        "Response goal must be 'maximize', 'minimize', or 'target'.",
        "goal",
    )


def composite_desirability(
    desirabilities: Sequence[float], importances: Sequence[float]
) -> float:
    """Combine individual desirabilities using an importance-weighted geometric mean."""

    values = finite_values(desirabilities, "desirabilities")
    weights = finite_values(importances, "importances")
    if not values or len(values) != len(weights):
        raise AnalysisInputError(
            "invalid_desirability_inputs",
            "Desirabilities and importances must be non-empty and have equal length.",
            "desirabilities",
        )
    if any(value < 0.0 or value > 1.0 for value in values):
        raise AnalysisInputError(
            "invalid_desirability_value",
            "Individual desirabilities must be between 0 and 1.",
            "desirabilities",
        )
    if any(weight < 0.1 or weight > 10.0 for weight in weights):
        raise AnalysisInputError(
            "invalid_desirability_importance",
            "Response importance must be between 0.1 and 10.",
            "importances",
        )
    if any(value == 0.0 for value in values):
        return 0.0
    return exp(
        sum(weight * log(value) for value, weight in zip(values, weights, strict=True))
        / sum(weights)
    )


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
    prediction_points: Sequence[Mapping[str, float]] = (),
    optimization_goal: str | None = None,
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
    normalized_name = response_name.strip()
    if not normalized_name:
        raise AnalysisInputError(
            "empty_response_name", "Response name cannot be empty.", "response_name"
        )
    factor_names = [factor["name"] for factor in design.parameters["factors"]]

    normalized_prediction_points = _normalize_prediction_points(
        prediction_points, design.parameters["factors"]
    )
    if optimization_goal not in {None, "maximize", "minimize"}:
        raise AnalysisInputError(
            "invalid_optimization_goal",
            "Optimization goal must be 'maximize', 'minimize', or omitted.",
            "optimization_goal",
        )

    terms = _model_terms(factor_names, interaction_order)
    intercept, coefficients, coded_columns, term_sums_of_squares = (
        _fit_orthogonal_model(
            rows,
            factor_names,
            values,
            terms,
            field="responses",
        )
    )

    fitted = [
        intercept
        + sum(coefficients[term] * coded_columns[term][index] for term in terms)
        for index in range(len(rows))
    ]
    residuals = [
        observed - predicted
        for observed, predicted in zip(values, fitted, strict=True)
    ]

    prediction_rows = [
        {
            "point": index,
            "actual": point["actual"],
            "coded": point["coded"],
            "predicted_response": _predict_response(
                point["coded"], intercept, coefficients
            ),
        }
        for index, point in enumerate(normalized_prediction_points, start=1)
    ]
    optimization_rows: list[dict[str, object]] = []
    if optimization_goal is not None:
        candidates = _factorial_vertex_candidates(design.parameters["factors"])
        scored = [
            {
                **candidate,
                "predicted_response": _predict_response(
                    candidate["coded"], intercept, coefficients
                ),
            }
            for candidate in candidates
        ]
        best = (
            max(scored, key=lambda row: row["predicted_response"])
            if optimization_goal == "maximize"
            else min(scored, key=lambda row: row["predicted_response"])
        )
        optimization_rows.append(
            {
                "goal": optimization_goal,
                "standard_order": best["standard_order"],
                "actual": best["actual"],
                "coded": best["coded"],
                "predicted_response": best["predicted_response"],
                "candidate_count": len(scored),
            }
        )
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
    if prediction_rows:
        warnings.append(
            "Predictions are fitted means inside the experimental region and do not include confidence or prediction intervals."
        )
    if optimization_rows:
        warnings.append(
            "Optimization compares all factorial vertices for the selected fitted model; confirm the setting experimentally before use."
        )
    payload = {
        **design.parameters,
        "responses": values,
        "response_name": normalized_name,
        "interaction_order": interaction_order,
        "prediction_points": [point["actual"] for point in normalized_prediction_points],
        "optimization_goal": optimization_goal,
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
            "predictions": prediction_rows,
            "optimization": optimization_rows,
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
            "prediction_count": len(prediction_rows),
            "optimization_goal": optimization_goal,
            "optimization_candidate_count": (
                optimization_rows[0]["candidate_count"] if optimization_rows else 0
            ),
        },
        assumptions=(
            "Responses correspond one-for-one to the generated design run order.",
            "The coded model is linear in the selected main effects and interactions.",
            "Residuals are expected to be independent with constant variance and "
            "approximately normal when inferential statistics are interpreted.",
            "Prediction points are restricted to the fitted experimental region.",
            "For this multilinear two-level model, maximum and minimum searches evaluate every factorial vertex.",
        ),
        warnings=tuple(warnings),
        provenance=(
            NIST_FACTORIAL_SOURCE,
            NIST_DOE_MODEL_SOURCE,
            NIST_RESIDUAL_SOURCE,
            NIST_FITTED_MODEL_SOURCE,
        ),
    )


def optimize_full_factorial_desirability(
    factors: Sequence[FactorDefinition],
    objectives: Sequence[ResponseObjective],
    *,
    replicates: int = 1,
    center_points: int = 0,
    randomize: bool = True,
    seed: int = 0,
    interaction_order: int = 2,
) -> ResultBundle:
    """Fit shared-design response models and maximize composite desirability."""

    design = full_factorial_2level(
        factors,
        replicates=replicates,
        center_points=center_points,
        randomize=randomize,
        seed=seed,
    )
    rows = design.tables["design"]
    factor_parameters = design.parameters["factors"]
    factor_names = [str(factor["name"]) for factor in factor_parameters]
    terms = _model_terms(factor_names, interaction_order)
    normalized_objectives = _normalize_response_objectives(objectives)

    models: list[dict[str, object]] = []
    fitted_models: list[tuple[float, dict[tuple[str, ...], float]]] = []
    for index, objective in enumerate(normalized_objectives):
        intercept, coefficients, _, _ = _fit_orthogonal_model(
            rows,
            factor_names,
            objective["responses"],
            terms,
            field=f"objectives[{index}].responses",
        )
        fitted_models.append((intercept, coefficients))
        models.append(
            {
                "response": objective["name"],
                "intercept": intercept,
                "coefficients": [
                    {
                        "term": ":".join(term),
                        "order": len(term),
                        "coefficient": coefficients[term],
                    }
                    for term in terms
                ],
            }
        )

    evaluation_count = 0

    def score(coded: Mapping[str, float]) -> dict[str, object]:
        nonlocal evaluation_count
        evaluation_count += 1
        response_rows: list[dict[str, object]] = []
        desirabilities: list[float] = []
        importances: list[float] = []
        for objective, (intercept, coefficients) in zip(
            normalized_objectives, fitted_models, strict=True
        ):
            prediction = _predict_response(coded, intercept, coefficients)
            desirability = individual_desirability(
                prediction,
                goal=objective["goal"],
                lower=objective["lower"],
                target=objective["target"],
                upper=objective["upper"],
                weight=objective["weight"],
            )
            desirabilities.append(desirability)
            importances.append(objective["importance"])
            response_rows.append(
                {
                    "response": objective["name"],
                    "goal": objective["goal"],
                    "prediction": prediction,
                    "desirability": desirability,
                    "lower": objective["lower"],
                    "target": objective["target"],
                    "upper": objective["upper"],
                    "weight": objective["weight"],
                    "importance": objective["importance"],
                }
            )
        return {
            "coded": dict(coded),
            "actual": _coded_to_actual(coded, factor_parameters),
            "composite_desirability": composite_desirability(
                desirabilities, importances
            ),
            "responses": response_rows,
        }

    vertices = _factorial_vertex_candidates(factor_parameters)
    vertex_scores = [score(candidate["coded"]) for candidate in vertices]
    center_score = score({name: 0.0 for name in factor_names})
    ranked_vertices = sorted(
        vertex_scores,
        key=lambda row: (
            -float(row["composite_desirability"]),
            tuple(float(row["coded"][name]) for name in factor_names),
        ),
    )
    start_scores = [center_score, *ranked_vertices[:16]]
    local_solutions = [
        _pattern_search_desirability(start, factor_names, score)
        for start in start_scores
    ]
    best = max(
        local_solutions,
        key=lambda row: (
            float(row["composite_desirability"]),
            -sum(abs(float(row["coded"][name])) for name in factor_names),
        ),
    )

    solution = {
        "solution": 1,
        "actual": best["actual"],
        "coded": best["coded"],
        "composite_desirability": best["composite_desirability"],
        "candidate_evaluations": evaluation_count,
        "search_method": "deterministic_multistart_pattern",
    }
    warnings = list(design.warnings)
    warnings.extend(
        [
            "The bounded multistart pattern search is deterministic but does not prove a global optimum.",
            "Response optimization uses fitted means; verify model assumptions and run confirmation experiments at the proposed setting.",
        ]
    )
    if float(best["composite_desirability"]) == 0.0:
        warnings.append(
            "Every retained search solution has zero composite desirability because at least one response is outside its acceptable bounds."
        )

    payload = {
        **design.parameters,
        "interaction_order": interaction_order,
        "objectives": normalized_objectives,
    }
    return ResultBundle(
        analysis_type="doe.full_factorial_2level_desirability",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters=payload,
        tables={
            "solution": [solution],
            "response_desirabilities": best["responses"],
            "models": models,
        },
        plots={
            "desirability": {
                "responses": [row["response"] for row in best["responses"]],
                "individual": [row["desirability"] for row in best["responses"]],
                "composite": best["composite_desirability"],
            }
        },
        diagnostics={
            "response_count": len(normalized_objectives),
            "coefficient_count_per_response": len(terms) + 1,
            "vertex_count": len(vertices),
            "search_start_count": len(start_scores),
            "candidate_evaluations": evaluation_count,
            "search_tolerance": 1e-6,
            "global_optimum_proven": False,
        },
        assumptions=(
            "Every response vector corresponds one-for-one to the same generated design run order.",
            "Each response uses the same coded main-effect and interaction term structure.",
            "Individual desirabilities use one shared shape weight on both sides of a target objective.",
            "Composite desirability is the importance-weighted geometric mean of individual desirabilities.",
            "Search is restricted to the fitted experimental region.",
        ),
        warnings=tuple(warnings),
        provenance=(
            NIST_FACTORIAL_SOURCE,
            NIST_DOE_MODEL_SOURCE,
            NIST_DESIRABILITY_SOURCE,
            MINITAB_RESPONSE_OPTIMIZER_SOURCE,
        ),
    )


def _normalize_response_objectives(
    objectives: Sequence[ResponseObjective],
) -> list[dict[str, object]]:
    if not objectives or len(objectives) > 10:
        raise AnalysisInputError(
            "invalid_response_objective_count",
            "Response optimization requires between 1 and 10 objectives.",
            "objectives",
        )
    normalized: list[dict[str, object]] = []
    names: set[str] = set()
    for index, objective in enumerate(objectives):
        name = objective.name.strip()
        if not name:
            raise AnalysisInputError(
                "empty_response_name",
                f"Objective {index + 1} needs a response name.",
                f"objectives[{index}].name",
            )
        if name in names:
            raise AnalysisInputError(
                "duplicate_response_name",
                f"Response name '{name}' is duplicated.",
                f"objectives[{index}].name",
            )
        values = finite_values(
            objective.responses, f"objectives[{index}].responses"
        )
        target = finite_values([objective.target], f"objectives[{index}].target")[0]
        lower = (
            None
            if objective.lower is None
            else finite_values([objective.lower], f"objectives[{index}].lower")[0]
        )
        upper = (
            None
            if objective.upper is None
            else finite_values([objective.upper], f"objectives[{index}].upper")[0]
        )
        weight, importance = finite_values(
            [objective.weight, objective.importance],
            f"objectives[{index}].desirability",
        )
        individual_desirability(
            target,
            goal=objective.goal,
            lower=lower,
            target=target,
            upper=upper,
            weight=weight,
        )
        composite_desirability([1.0], [importance])
        names.add(name)
        normalized.append(
            {
                "name": name,
                "responses": values,
                "goal": objective.goal,
                "lower": lower,
                "target": target,
                "upper": upper,
                "weight": weight,
                "importance": importance,
            }
        )
    return normalized


def _pattern_search_desirability(
    start: Mapping[str, object],
    factor_names: Sequence[str],
    score: Callable[[Mapping[str, float]], dict[str, object]],
) -> dict[str, object]:
    current = dict(start)
    step = 0.5
    iterations = 0
    while step >= 1e-6 and iterations < 200:
        iterations += 1
        best = current
        for name in factor_names:
            for direction in (-1.0, 1.0):
                coded = dict(current["coded"])
                candidate = max(-1.0, min(1.0, float(coded[name]) + direction * step))
                if candidate == coded[name]:
                    continue
                coded[name] = candidate
                evaluated = score(coded)
                if float(evaluated["composite_desirability"]) > float(
                    best["composite_desirability"]
                ) + 1e-12:
                    best = evaluated
        if best is current:
            step /= 2.0
        else:
            current = best
    return current


def _coded_to_actual(
    coded: Mapping[str, float], factors: Sequence[Mapping[str, object]]
) -> dict[str, float]:
    return {
        str(factor["name"]): float(factor["low"])
        + (float(coded[str(factor["name"])]) + 1.0)
        * (float(factor["high"]) - float(factor["low"]))
        / 2.0
        for factor in factors
    }


def _normalize_prediction_points(
    points: Sequence[Mapping[str, float]], factors: Sequence[Mapping[str, object]]
) -> list[dict[str, dict[str, float]]]:
    if len(points) > 100:
        raise AnalysisInputError(
            "too_many_prediction_points",
            "At most 100 prediction points can be evaluated in one analysis.",
            "prediction_points",
        )
    names = [str(factor["name"]) for factor in factors]
    expected = set(names)
    normalized: list[dict[str, dict[str, float]]] = []
    for index, point in enumerate(points):
        if not isinstance(point, Mapping) or set(point) != expected:
            raise AnalysisInputError(
                "invalid_prediction_point",
                f"Prediction point {index + 1} must contain exactly: {', '.join(names)}.",
                f"prediction_points[{index}]",
            )
        actual: dict[str, float] = {}
        coded: dict[str, float] = {}
        for factor in factors:
            name = str(factor["name"])
            low = float(factor["low"])
            high = float(factor["high"])
            value = finite_values([point[name]], f"prediction_points[{index}].{name}")[0]
            if value < low or value > high:
                raise AnalysisInputError(
                    "prediction_outside_design_region",
                    f"Prediction value for '{name}' must be between {low} and {high}.",
                    f"prediction_points[{index}].{name}",
                )
            actual[name] = value
            coded[name] = -1.0 + 2.0 * (value - low) / (high - low)
        normalized.append({"actual": actual, "coded": coded})
    return normalized


def _factorial_vertex_candidates(
    factors: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for standard_index in range(2 ** len(factors)):
        coded = {
            str(factor["name"]): (
                1.0 if standard_index & (1 << factor_index) else -1.0
            )
            for factor_index, factor in enumerate(factors)
        }
        actual = {
            str(factor["name"]): (
                float(factor["high"])
                if coded[str(factor["name"])] == 1.0
                else float(factor["low"])
            )
            for factor in factors
        }
        candidates.append(
            {
                "standard_order": standard_index + 1,
                "actual": actual,
                "coded": coded,
            }
        )
    return candidates


def _predict_response(
    coded: Mapping[str, float],
    intercept: float,
    coefficients: Mapping[tuple[str, ...], float],
) -> float:
    return intercept + sum(
        coefficient * _product(coded[name] for name in term)
        for term, coefficient in coefficients.items()
    )


def _product(values: Iterable[float]) -> float:
    result = 1.0
    for value in values:
        result *= value
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
