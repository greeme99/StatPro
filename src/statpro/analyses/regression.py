"""Small, explicit ordinary least squares regression ResultBundles."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from itertools import combinations
from statistics import NormalDist, fmean

from statpro.analyses.common import f_survival, finite_values, invert_matrix
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_LINEAR_LEAST_SQUARES_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH Linear Least Squares Regression",
    url="https://www.itl.nist.gov/div898/handbook/pmd/section1/pmd141.htm",
)
NIST_LEAST_SQUARES_GLOSSARY_SOURCE = ProvenanceSource(
    title="NIST StRD Linear Least Squares Regression Glossary",
    url="https://www.itl.nist.gov/div898/strd/lls/data/LINKS/c-NoInt2.shtml",
)


def _two_sided_t_critical(alpha: float, degrees_of_freedom: int) -> float:
    """Return the positive two-sided Student-t critical value via F(1, df)."""
    lower, upper = 0.0, 1.0
    target_tail = alpha
    while (f_survival(upper * upper, 1, degrees_of_freedom) or 0.0) > target_tail:
        upper *= 2.0
        if upper > 1e6:
            raise AnalysisInputError("distribution_not_converged", "The t critical value search exceeded its bound.", "alpha")
    for _ in range(80):
        midpoint = (lower + upper) / 2.0
        if (f_survival(midpoint * midpoint, 1, degrees_of_freedom) or 0.0) > target_tail:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2.0


def _collinearity_rows(predictors: Mapping[str, Sequence[float]]) -> list[dict[str, float | str]]:
    """Calculate VIF from the inverse correlation matrix of the fitted X terms."""
    names = list(predictors)
    if len(names) == 1:
        return [{"term": names[0], "vif": 1.0, "tolerance": 1.0}]
    centered = {
        name: [value - fmean(values) for value in values]
        for name, values in predictors.items()
    }
    sums_of_squares = {name: sum(value * value for value in values) for name, values in centered.items()}
    correlation = [
        [
            sum(left * right for left, right in zip(centered[left_name], centered[right_name], strict=True))
            / math.sqrt(sums_of_squares[left_name] * sums_of_squares[right_name])
            for right_name in names
        ]
        for left_name in names
    ]
    inverse = invert_matrix(correlation, field="predictors")
    return [
        {"term": name, "vif": inverse[index][index], "tolerance": 1.0 / inverse[index][index]}
        for index, name in enumerate(names)
    ]


def logistic_regression(response: Sequence[float], predictors: Mapping[str, Sequence[float]], *, response_name: str = "Outcome", alpha: float = 0.05) -> ResultBundle:
    """Fit a binary logistic model with bounded IRLS iterations."""
    values = finite_values(response, "response")
    if not predictors or any(value not in (0.0, 1.0) for value in values): raise AnalysisInputError("invalid_binary_response", "Logistic regression requires predictors and a binary 0/1 response.", "response")
    names = list(predictors); columns = {name: finite_values(value, f"predictors.{name}") for name, value in predictors.items()}
    if len(values) < len(names) + 3 or any(len(column) != len(values) for column in columns.values()): raise AnalysisInputError("insufficient_observations", "Response and predictors must align with enough observations.", "predictors")
    if not 0.001 <= alpha <= 0.5 or not response_name.strip(): raise AnalysisInputError("invalid_alpha", "Use a valid response name and alpha.", "alpha")
    matrix = [[1.0, *(columns[name][i] for name in names)] for i in range(len(values))]; coefficients = [0.0] * (len(names) + 1); inverse = None
    for _ in range(50):
        linear = [sum(x * beta for x, beta in zip(row, coefficients, strict=True)) for row in matrix]
        probabilities = [min(1 - 1e-9, max(1e-9, 1 / (1 + math.exp(-max(-35.0, min(35.0, value)))))) for value in linear]
        weights = [p * (1 - p) for p in probabilities]
        information = [[sum(weights[k] * matrix[k][i] * matrix[k][j] for k in range(len(values))) for j in range(len(coefficients))] for i in range(len(coefficients))]
        inverse = invert_matrix(information, field="predictors")
        score = [sum(matrix[k][i] * (values[k] - probabilities[k]) for k in range(len(values))) for i in range(len(coefficients))]
        updated = [coefficients[i] + sum(inverse[i][j] * score[j] for j in range(len(coefficients))) for i in range(len(coefficients))]
        if max(abs(a-b) for a, b in zip(updated, coefficients, strict=True)) < 1e-8: coefficients = updated; break
        coefficients = updated
    else: raise AnalysisInputError("logistic_not_converged", "Logistic fitting did not converge; review separation and scaling.", "predictors")
    probabilities = [min(1 - 1e-9, max(1e-9, 1 / (1 + math.exp(-sum(x * beta for x, beta in zip(row, coefficients, strict=True))))) ) for row in matrix]
    critical = NormalDist().inv_cdf(1 - alpha / 2); rows = []
    for i, term in enumerate(["Intercept", *names]):
        se = math.sqrt(max(0.0, inverse[i][i])); z = coefficients[i] / se if se else None; p = math.erfc(abs(z) / math.sqrt(2)) if z is not None else None
        lower, upper = coefficients[i] - critical * se, coefficients[i] + critical * se
        rows.append({"term": term, "coefficient": coefficients[i], "odds_ratio": math.exp(coefficients[i]), "odds_ratio_ci_lower": math.exp(lower), "odds_ratio_ci_upper": math.exp(upper), "standard_error": se, "z_value": z, "p_value": p, "significant": p <= alpha if p is not None else False})
    classification_threshold = 0.5
    classification_accuracy = sum(
        (1.0 if probability >= classification_threshold else 0.0) == actual
        for probability, actual in zip(probabilities, values, strict=True)
    ) / len(values)
    log_likelihood = sum(
        actual * math.log(probability) + (1.0 - actual) * math.log1p(-probability)
        for probability, actual in zip(probabilities, values, strict=True)
    )
    return ResultBundle(analysis_type="regression.logistic", engine_version=ENGINE_VERSION, input_digest=input_digest({"response":values,"predictors":columns,"response_name":response_name,"alpha":alpha}), parameters={"response_name":response_name,"predictor_names":names,"alpha":alpha,"sample_size":len(values)}, tables={"coefficients":{"columns":["term","coefficient","odds_ratio","odds_ratio_ci_lower","odds_ratio_ci_upper","standard_error","z_value","p_value","significant"],"rows":rows},"fitted_values":{"columns":["observation","actual","predicted_probability"],"rows":[{"observation":i+1,"actual":values[i],"predicted_probability":probabilities[i]} for i in range(len(values))]}}, plots={}, diagnostics={"event_count":sum(values),"predicted_event_count":sum(probabilities),"classification_threshold":classification_threshold,"classification_accuracy":classification_accuracy,"log_likelihood":log_likelihood}, assumptions=("Rows are independent and the response is coded 0 or 1.",), warnings=("Wald inference can be unstable with small samples or separation; review coefficients and event counts.",), provenance=(NIST_LINEAR_LEAST_SQUARES_SOURCE,))


def polynomial_ols(
    response: Sequence[float],
    predictors: Mapping[str, Sequence[float]],
    *,
    response_name: str = "Response",
    degree: int = 2,
    alpha: float = 0.05,
) -> ResultBundle:
    """Fit an OLS model with explicit per-predictor polynomial terms.

    Interaction terms, automatic term selection, and extrapolation assessment
    are intentionally outside this focused polynomial extension.
    """
    if isinstance(degree, bool) or degree not in (2, 3):
        raise AnalysisInputError("invalid_polynomial_degree", "Polynomial degree must be 2 or 3.", "degree")
    if len(predictors) * degree > 20:
        raise AnalysisInputError("too_many_polynomial_terms", "At most 20 expanded polynomial terms are supported.", "predictors")

    source_names = list(predictors)
    expanded_predictors: dict[str, list[float]] = {}
    for name, source_values in predictors.items():
        if not name.strip():
            raise AnalysisInputError("empty_predictor_name", "Predictor names cannot be empty.", "predictors")
        values = finite_values(source_values, f"predictors.{name}")
        for exponent in range(1, degree + 1):
            term_name = name if exponent == 1 else f"{name}^{exponent}"
            term_values = [value**exponent for value in values]
            if any(not math.isfinite(value) for value in term_values):
                raise AnalysisInputError("non_finite_polynomial_term", "Polynomial expansion produced a non-finite value.", f"predictors.{name}")
            expanded_predictors[term_name] = term_values

    fitted = linear_ols(response, expanded_predictors, response_name=response_name, alpha=alpha)
    return ResultBundle(
        analysis_type="regression.polynomial_ols",
        engine_version=fitted.engine_version,
        input_digest=input_digest({"response": list(response), "predictors": predictors, "response_name": response_name, "degree": degree, "alpha": alpha}),
        parameters={
            **fitted.parameters,
            "degree": degree,
            "source_predictor_names": source_names,
            "expanded_predictor_names": list(expanded_predictors),
        },
        tables=fitted.tables,
        plots=fitted.plots,
        diagnostics=fitted.diagnostics,
        assumptions=(*fitted.assumptions, "Polynomial terms model curvature within the observed predictor range; extrapolation requires separate review."),
        warnings=(*fitted.warnings, "Polynomial terms are fitted without interactions or automatic term selection."),
        provenance=fitted.provenance,
    )


def interaction_ols(
    response: Sequence[float],
    predictors: Mapping[str, Sequence[float]],
    *,
    response_name: str = "Response",
    alpha: float = 0.05,
) -> ResultBundle:
    """Fit OLS with all explicit two-factor interactions and no term selection."""
    source_names = list(predictors)
    term_count = len(source_names) + (len(source_names) * (len(source_names) - 1)) // 2
    if term_count > 20:
        raise AnalysisInputError("too_many_interaction_terms", "At most 20 main and two-factor interaction terms are supported.", "predictors")

    normalized = {name: finite_values(values, f"predictors.{name}") for name, values in predictors.items()}
    expanded_predictors = dict(normalized)
    for left, right in combinations(source_names, 2):
        expanded_predictors[f"{left}*{right}"] = [
            left_value * right_value
            for left_value, right_value in zip(normalized[left], normalized[right], strict=True)
        ]

    fitted = linear_ols(response, expanded_predictors, response_name=response_name, alpha=alpha)
    return ResultBundle(
        analysis_type="regression.interaction_ols",
        engine_version=fitted.engine_version,
        input_digest=input_digest({"response": list(response), "predictors": predictors, "response_name": response_name, "interaction_order": 2, "alpha": alpha}),
        parameters={
            **fitted.parameters,
            "interaction_order": 2,
            "source_predictor_names": source_names,
            "expanded_predictor_names": list(expanded_predictors),
        },
        tables=fitted.tables,
        plots=fitted.plots,
        diagnostics=fitted.diagnostics,
        assumptions=(*fitted.assumptions, "Every two-factor interaction is included explicitly; interpretation requires sufficient observations across the joint predictor range."),
        warnings=(*fitted.warnings, "Higher-order interactions and automatic term selection are not included."),
        provenance=fitted.provenance,
    )


def linear_ols(
    response: Sequence[float],
    predictors: Mapping[str, Sequence[float]],
    *,
    response_name: str = "Response",
    alpha: float = 0.05,
) -> ResultBundle:
    """Fit an intercept-inclusive multiple linear OLS model.

    Weighted, robust, logistic, and automatic-selection models are separate
    methods and are not silently substituted here.
    """

    values = finite_values(response, "response")
    if not predictors:
        raise AnalysisInputError("missing_predictors", "At least one predictor is required.", "predictors")
    normalized_name = response_name.strip()
    if not normalized_name:
        raise AnalysisInputError("empty_response_name", "Response name cannot be empty.", "response_name")
    normalized_alpha = finite_values([alpha], "alpha")[0]
    if not 0.001 <= normalized_alpha <= 0.5:
        raise AnalysisInputError("invalid_alpha", "Alpha must be between 0.001 and 0.5.", "alpha")

    predictor_names = list(predictors)
    if len(predictor_names) > 20:
        raise AnalysisInputError("too_many_predictors", "At most 20 predictors are supported.", "predictors")
    if any(not name.strip() for name in predictor_names):
        raise AnalysisInputError("empty_predictor_name", "Predictor names cannot be empty.", "predictors")
    normalized_predictors = {
        name: finite_values(column, f"predictors.{name}")
        for name, column in predictors.items()
    }
    sample_size = len(values)
    if any(len(column) != sample_size for column in normalized_predictors.values()):
        raise AnalysisInputError(
            "predictor_length_mismatch",
            "Every predictor must have the same number of observations as the response.",
            "predictors",
        )
    parameter_count = len(predictor_names) + 1
    residual_df = sample_size - parameter_count
    if residual_df < 1:
        raise AnalysisInputError(
            "insufficient_observations",
            "OLS requires more observations than fitted parameters.",
            "response",
        )

    matrix = [
        [1.0, *(normalized_predictors[name][index] for name in predictor_names)]
        for index in range(sample_size)
    ]
    cross_product = [
        [sum(row[left] * row[right] for row in matrix) for right in range(parameter_count)]
        for left in range(parameter_count)
    ]
    inverse = invert_matrix(cross_product, field="predictors")
    cross_response = [
        sum(row[column] * value for row, value in zip(matrix, values, strict=True))
        for column in range(parameter_count)
    ]
    coefficients = [
        sum(inverse[row][column] * cross_response[column] for column in range(parameter_count))
        for row in range(parameter_count)
    ]
    fitted = [
        sum(value * coefficient for value, coefficient in zip(row, coefficients, strict=True))
        for row in matrix
    ]
    residuals = [actual - prediction for actual, prediction in zip(values, fitted, strict=True)]
    response_mean = fmean(values)
    total_ss = sum((value - response_mean) ** 2 for value in values)
    residual_ss = sum(residual * residual for residual in residuals)
    model_ss = max(0.0, total_ss - residual_ss)
    model_df = parameter_count - 1
    residual_ms = residual_ss / residual_df
    model_ms = model_ss / model_df
    model_f = model_ms / residual_ms if residual_ms > 0.0 else None
    model_p = f_survival(model_f, model_df, residual_df)
    r_squared = 1.0 - residual_ss / total_ss if total_ss > 0.0 else None
    adjusted_r_squared = (
        1.0 - (1.0 - r_squared) * (sample_size - 1) / residual_df
        if r_squared is not None else None
    )
    t_critical = _two_sided_t_critical(normalized_alpha, residual_df)
    collinearity_rows = _collinearity_rows(normalized_predictors)

    terms = ["Intercept", *predictor_names]
    coefficient_rows: list[dict[str, float | str | bool | None]] = []
    for index, (term, coefficient) in enumerate(zip(terms, coefficients, strict=True)):
        standard_error = math.sqrt(max(0.0, residual_ms * inverse[index][index]))
        t_value = coefficient / standard_error if standard_error > 0.0 else None
        p_value = f_survival(t_value * t_value, 1, residual_df) if t_value is not None else None
        coefficient_rows.append({
            "term": term, "coefficient": coefficient, "standard_error": standard_error,
            "t_value": t_value, "p_value": p_value,
            "significant": p_value <= normalized_alpha if p_value is not None else False,
        })
    fitted_rows = []
    for index, (actual, prediction, residual) in enumerate(zip(values, fitted, residuals, strict=True)):
        leverage = sum(
            matrix[index][left] * inverse[left][right] * matrix[index][right]
            for left in range(parameter_count) for right in range(parameter_count)
        )
        prediction_margin = t_critical * math.sqrt(residual_ms * (1.0 + leverage))
        fitted_rows.append({
            "observation": index + 1, "actual": actual, "fitted": prediction,
            "residual": residual, "leverage": leverage,
            "prediction_interval_lower": prediction - prediction_margin,
            "prediction_interval_upper": prediction + prediction_margin,
        })
    warnings = [
        "OLS estimates and inferential p-values assume independent errors with constant variance; inspect residuals before using the model operationally.",
        "Normal equations can be ill-conditioned for poorly scaled or collinear predictors; singular designs are rejected but near-singularity still needs engineering review.",
    ]
    if residual_ms == 0.0:
        warnings.append("Residual variance is zero; F and coefficient t/p statistics are not reported as exact significance claims.")
    if sample_size < 20:
        warnings.append("Small sample size: coefficient and model inference can be unstable.")
    maximum_vif = max(row["vif"] for row in collinearity_rows)
    if maximum_vif >= 10.0:
        warnings.append("High predictor collinearity: at least one VIF is 10 or higher; review redundant X variables before operational use.")
    return ResultBundle(
        analysis_type="regression.linear_ols",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest({"response": values, "predictors": normalized_predictors, "response_name": normalized_name, "alpha": normalized_alpha}),
        parameters={"response_name": normalized_name, "predictor_names": predictor_names, "alpha": normalized_alpha, "sample_size": sample_size, "parameter_count": parameter_count, "intercept": True},
        tables={
            "coefficients": {"columns": ["term", "coefficient", "standard_error", "t_value", "p_value", "significant"], "rows": coefficient_rows},
            "anova": {"columns": ["source", "degrees_of_freedom", "sum_squares", "mean_square", "f_value", "p_value"], "rows": [
                {"source": "Model", "degrees_of_freedom": model_df, "sum_squares": model_ss, "mean_square": model_ms, "f_value": model_f, "p_value": model_p},
                {"source": "Error", "degrees_of_freedom": residual_df, "sum_squares": residual_ss, "mean_square": residual_ms, "f_value": None, "p_value": None},
                {"source": "Total", "degrees_of_freedom": sample_size - 1, "sum_squares": total_ss, "mean_square": None, "f_value": None, "p_value": None},
            ]},
            "fitted_values": {"columns": ["observation", "actual", "fitted", "residual", "leverage", "prediction_interval_lower", "prediction_interval_upper"], "rows": fitted_rows},
            "collinearity": {"columns": ["term", "vif", "tolerance"], "rows": collinearity_rows},
        },
        plots={},
        diagnostics={"r_squared": r_squared, "adjusted_r_squared": adjusted_r_squared, "residual_standard_error": math.sqrt(residual_ms), "residual_degrees_of_freedom": residual_df, "model_f_statistic": model_f, "model_p_value": model_p, "prediction_interval_confidence": 1.0 - normalized_alpha, "maximum_vif": maximum_vif},
        assumptions=(
            "The response is continuous and observations are aligned by row.",
            "Errors are independent with approximately constant variance.",
            "Coefficient and model inference additionally use the usual normal-error approximation.",
        ),
        warnings=tuple(warnings),
        provenance=(NIST_LINEAR_LEAST_SQUARES_SOURCE, NIST_LEAST_SQUARES_GLOSSARY_SOURCE),
    )
