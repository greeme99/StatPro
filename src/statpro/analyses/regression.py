"""Small, explicit ordinary least squares regression ResultBundles."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from itertools import combinations
from statistics import NormalDist, fmean

from statpro.analyses.common import chi_square_survival, f_survival, finite_values, invert_matrix
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
NIST_REGRESSION_DIAGNOSTICS_SOURCE = ProvenanceSource(
    title="NIST Regression Diagnostics",
    url="https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd44.htm",
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


def _ols_assumption_diagnostics(
    residuals: Sequence[float],
    matrix: Sequence[Sequence[float]],
    inverse_cross_product: Sequence[Sequence[float]],
    *,
    alpha: float,
) -> dict[str, float | int | bool | str | None]:
    """Compute residual diagnostics at the OLS producer boundary."""
    sample_size = len(residuals)
    residual_mean = fmean(residuals)
    centered = [residual - residual_mean for residual in residuals]
    second_moment = fmean(value * value for value in centered)
    normality: dict[str, float | int | bool | str | None] = {
        "residual_normality_method": "jarque_bera_asymptotic",
        "residual_normality_statistic": None,
        "residual_normality_p_value": None,
        "residual_normality_status": "unavailable_zero_variation" if second_moment == 0.0 else "available",
        "reject_residual_normality": None,
    }
    if second_moment > 0.0:
        skewness = fmean(value**3 for value in centered) / second_moment**1.5
        kurtosis = fmean(value**4 for value in centered) / second_moment**2
        statistic = sample_size / 6.0 * (skewness**2 + (kurtosis - 3.0) ** 2 / 4.0)
        p_value = chi_square_survival(statistic, 2)
        normality.update({
            "residual_skewness": skewness,
            "residual_kurtosis": kurtosis,
            "residual_normality_statistic": statistic,
            "residual_normality_p_value": p_value,
            "reject_residual_normality": p_value <= alpha if p_value is not None else None,
        })

    squared_residuals = [residual * residual for residual in residuals]
    squared_mean = fmean(squared_residuals)
    squared_total = sum((value - squared_mean) ** 2 for value in squared_residuals)
    degrees_of_freedom = len(matrix[0]) - 1
    heteroscedasticity: dict[str, float | int | bool | str | None] = {
        "heteroscedasticity_method": "breusch_pagan_lm",
        "heteroscedasticity_statistic": None,
        "heteroscedasticity_p_value": None,
        "heteroscedasticity_degrees_of_freedom": degrees_of_freedom,
        "heteroscedasticity_status": "unavailable_zero_variation" if squared_total == 0.0 else "available",
        "reject_constant_variance": None,
    }
    if squared_total > 0.0:
        cross_response = [
            sum(row[column] * value for row, value in zip(matrix, squared_residuals, strict=True))
            for column in range(len(matrix[0]))
        ]
        coefficients = [
            sum(inverse_cross_product[row][column] * cross_response[column] for column in range(len(matrix[0])))
            for row in range(len(matrix[0]))
        ]
        auxiliary_fitted = [
            sum(value * coefficient for value, coefficient in zip(row, coefficients, strict=True))
            for row in matrix
        ]
        auxiliary_r_squared = max(0.0, min(1.0, 1.0 - sum((actual - fitted) ** 2 for actual, fitted in zip(squared_residuals, auxiliary_fitted, strict=True)) / squared_total))
        statistic = sample_size * auxiliary_r_squared
        p_value = chi_square_survival(statistic, degrees_of_freedom)
        heteroscedasticity.update({
            "heteroscedasticity_auxiliary_r_squared": auxiliary_r_squared,
            "heteroscedasticity_statistic": statistic,
            "heteroscedasticity_p_value": p_value,
            "reject_constant_variance": p_value <= alpha if p_value is not None else None,
        })
    return {**normality, **heteroscedasticity}


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


def categorical_ols(response: Sequence[float], predictors: Mapping[str, Sequence[str]], *, reference_levels: Mapping[str, str], response_name: str = "Response", alpha: float = 0.05) -> ResultBundle:
    """Fit OLS after explicit reference-level dummy coding of categorical X variables."""
    values = finite_values(response, "response")
    expanded: dict[str, list[float]] = {}
    resolved: dict[str, str] = {}
    for name, raw_levels in predictors.items():
        levels = [str(level).strip() for level in raw_levels]
        if len(levels) != len(values) or not all(levels): raise AnalysisInputError("invalid_categorical_predictor", "Categorical values must be non-empty and align with the response.", f"predictors.{name}")
        available = sorted(set(levels)); reference = reference_levels.get(name)
        if reference not in available: raise AnalysisInputError("unknown_categorical_reference", "Reference level must appear in the categorical predictor.", f"reference_levels.{name}")
        resolved[name] = reference
        for level in available:
            if level != reference: expanded[f"{name}[{level}]"] = [1.0 if value == level else 0.0 for value in levels]
    fitted = linear_ols(values, expanded, response_name=response_name, alpha=alpha)
    return ResultBundle(analysis_type="regression.categorical_ols", engine_version=fitted.engine_version, input_digest=input_digest({"response": values, "predictors": predictors, "reference_levels": resolved, "response_name": response_name, "alpha": alpha}), parameters={**fitted.parameters, "reference_levels": resolved, "categorical_predictor_names": list(predictors)}, tables=fitted.tables, plots=fitted.plots, diagnostics=fitted.diagnostics, assumptions=(*fitted.assumptions, "Each categorical predictor is reference-coded; coefficients compare each level with its stated reference."), warnings=fitted.warnings, provenance=fitted.provenance)


def poisson_regression(response: Sequence[float], predictors: Mapping[str, Sequence[float]], *, response_name: str = "Count", alpha: float = 0.05) -> ResultBundle:
    """Fit a bounded Poisson log-link GLM with IRLS for non-negative count Y."""
    values = finite_values(response, "response"); names = list(predictors); columns = {name: finite_values(column, f"predictors.{name}") for name, column in predictors.items()}
    if not columns or any(value < 0 or value != int(value) for value in values) or any(len(column) != len(values) for column in columns.values()): raise AnalysisInputError("invalid_poisson_input", "Poisson regression needs aligned numeric predictors and non-negative integer counts.", "response")
    if len(values) < len(names) + 3: raise AnalysisInputError("insufficient_observations", "Poisson regression needs residual degrees of freedom.", "response")
    matrix = [[1.0, *(columns[name][index] for name in names)] for index in range(len(values))]; coefficients = [0.0] * (len(names) + 1); inverse = None
    for _ in range(100):
        eta = [max(-20.0, min(20.0, sum(value * beta for value, beta in zip(row, coefficients, strict=True)))) for row in matrix]; means = [math.exp(value) for value in eta]
        information = [[sum(means[row_index] * matrix[row_index][left] * matrix[row_index][right] for row_index in range(len(values))) for right in range(len(coefficients))] for left in range(len(coefficients))]
        inverse = invert_matrix(information, field="predictors")
        score = [sum(matrix[row_index][column_index] * (values[row_index] - means[row_index]) for row_index in range(len(values))) for column_index in range(len(coefficients))]
        updated = [coefficients[index] + sum(inverse[index][column] * score[column] for column in range(len(coefficients))) for index in range(len(coefficients))]
        if max(abs(left-right) for left, right in zip(updated, coefficients, strict=True)) < 1e-8: coefficients = updated; break
        coefficients = updated
    else: raise AnalysisInputError("poisson_not_converged", "Poisson fitting did not converge; review separation, scale, and sparse counts.", "predictors")
    means = [math.exp(max(-20.0, min(20.0, sum(value * beta for value, beta in zip(row, coefficients, strict=True))))) for row in matrix]; critical = NormalDist().inv_cdf(1-alpha/2); rows=[]
    for index, term in enumerate(["Intercept", *names]):
        se=math.sqrt(max(0.0, inverse[index][index])); z=coefficients[index]/se if se else None; p=math.erfc(abs(z)/math.sqrt(2)) if z is not None else None; lower,upper=coefficients[index]-critical*se,coefficients[index]+critical*se
        rows.append({"term":term,"coefficient":coefficients[index],"incidence_rate_ratio":math.exp(coefficients[index]),"irr_ci_lower":math.exp(lower),"irr_ci_upper":math.exp(upper),"standard_error":se,"z_value":z,"p_value":p,"significant":p <= alpha if p is not None else False})
    deviance = 2*sum(0.0 if actual == 0 else actual*math.log(actual/mean) - (actual-mean) for actual,mean in zip(values,means,strict=True))
    residual_df = len(values) - len(coefficients)
    pearson_chi_square = sum((actual - mean) ** 2 / mean for actual, mean in zip(values, means, strict=True))
    dispersion_ratio = pearson_chi_square / residual_df
    dispersion_z_value = (pearson_chi_square - residual_df) / math.sqrt(2 * residual_df)
    dispersion_p_value = math.erfc(abs(dispersion_z_value) / math.sqrt(2))
    if dispersion_p_value <= alpha and dispersion_ratio > 1:
        dispersion_status = "overdispersed"
        warnings = ("Pearson dispersion diagnostic indicates overdispersion; Poisson standard errors and p-values may be too optimistic.",)
    elif dispersion_p_value <= alpha and dispersion_ratio < 1:
        dispersion_status = "underdispersed"
        warnings = ("Pearson dispersion diagnostic indicates underdispersion; review the sampling and count-generation mechanism.",)
    else:
        dispersion_status = "consistent"
        warnings = ("Overdispersion or excess zeros can invalidate Poisson standard errors; inspect deviance and process data.",)
    return ResultBundle(analysis_type="regression.poisson", engine_version=ENGINE_VERSION, input_digest=input_digest({"response":values,"predictors":columns,"response_name":response_name,"alpha":alpha}), parameters={"response_name":response_name,"predictor_names":names,"alpha":alpha,"sample_size":len(values)}, tables={"coefficients":{"columns":["term","coefficient","incidence_rate_ratio","irr_ci_lower","irr_ci_upper","standard_error","z_value","p_value","significant"],"rows":rows},"fitted_values":{"columns":["observation","actual","predicted_count"],"rows":[{"observation":index+1,"actual":values[index],"predicted_count":mean} for index,mean in enumerate(means)]}}, plots={}, diagnostics={"deviance":deviance,"residual_degrees_of_freedom":residual_df,"predicted_count_total":sum(means),"pearson_chi_square":pearson_chi_square,"dispersion_ratio":dispersion_ratio,"dispersion_z_value":dispersion_z_value,"dispersion_p_value":dispersion_p_value,"dispersion_status":dispersion_status}, assumptions=("Rows are independent and counts follow a Poisson mean-variance relationship.", "The dispersion diagnostic uses a normal approximation to Pearson chi-square around its residual degrees of freedom."), warnings=warnings, provenance=(NIST_LINEAR_LEAST_SQUARES_SOURCE,))


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


def _ols_information_criteria(result: ResultBundle) -> tuple[float, float]:
    sample_size = int(result.parameters["sample_size"])
    parameter_count = int(result.parameters["parameter_count"])
    residuals = (result.tables["fitted_values"])["rows"]
    residual_ss = sum(float(row["residual"]) ** 2 for row in residuals)
    if residual_ss <= 0.0:
        return (float("inf"), float("inf"))
    log_likelihood = -0.5 * sample_size * (math.log(2.0 * math.pi) + 1.0 + math.log(residual_ss / sample_size))
    aic = -2.0 * log_likelihood + 2.0 * parameter_count
    aicc = aic + (2.0 * parameter_count * (parameter_count + 1) / (sample_size - parameter_count - 1)) if sample_size > parameter_count + 1 else float("inf")
    return (aicc, -2.0 * log_likelihood + parameter_count * math.log(sample_size))


def stepwise_ols(
    response: Sequence[float],
    predictors: Mapping[str, Sequence[float]],
    *,
    response_name: str = "Response",
    interaction_terms: bool = False,
    method: str = "stepwise",
    criterion: str = "aicc",
    alpha_enter: float = 0.05,
    alpha_remove: float = 0.10,
    alpha: float = 0.05,
) -> ResultBundle:
    """Fit a bounded hierarchical OLS model using deterministic term selection."""
    if method not in {"forward", "backward", "stepwise"}:
        raise AnalysisInputError("invalid_selection_method", "Use forward, backward, or stepwise selection.", "method")
    if criterion not in {"aicc", "bic"} or not 0.001 <= alpha_enter <= alpha_remove <= 0.5:
        raise AnalysisInputError("invalid_selection_options", "Check criterion and selection alpha levels.", "selection")
    source = {name: finite_values(values, f"predictors.{name}") for name, values in predictors.items()}
    terms = dict(source)
    dependencies: dict[str, set[str]] = {name: set() for name in source}
    if interaction_terms:
        for left, right in combinations(source, 2):
            name = f"{left}*{right}"
            terms[name] = [a * b for a, b in zip(source[left], source[right], strict=True)]
            dependencies[name] = {left, right}
    if not terms or len(terms) > 20:
        raise AnalysisInputError("too_many_selection_terms", "Use between 1 and 20 candidate main and interaction terms.", "predictors")

    def fit(selected: list[str]) -> ResultBundle | None:
        try:
            return linear_ols(response, {name: terms[name] for name in selected}, response_name=response_name, alpha=alpha)
        except AnalysisInputError:
            return None

    def p_value(result: ResultBundle, term: str) -> float:
        row = next(row for row in result.tables["coefficients"]["rows"] if row["term"] == term)
        return float(row["p_value"]) if row["p_value"] is not None else float("inf")

    selected = list(terms) if method == "backward" else []
    history: list[dict[str, float | str | int]] = []
    while True:
        changed = False
        if method != "backward":
            candidates = [name for name in terms if name not in selected and dependencies[name].issubset(selected)]
            evaluated = [(name, result) for name in candidates if (result := fit([*selected, name])) is not None]
            if evaluated:
                best_name, best_result = min(evaluated, key=lambda item: _ols_information_criteria(item[1])[0 if criterion == "aicc" else 1])
                if p_value(best_result, best_name) <= alpha_enter:
                    selected.append(best_name)
                    aicc, bic = _ols_information_criteria(best_result)
                    history.append({"step": len(history) + 1, "action": "enter", "term": best_name, "aicc": aicc, "bic": bic})
                    changed = True
        if method in {"backward", "stepwise"} and selected:
            current = fit(selected)
            removable = [name for name in selected if not any(name in dependencies[other] for other in selected if other != name)]
            if current and removable:
                worst = max(removable, key=lambda name: p_value(current, name))
                if p_value(current, worst) > alpha_remove:
                    selected.remove(worst)
                    next_result = fit(selected)
                    if next_result:
                        aicc, bic = _ols_information_criteria(next_result)
                        history.append({"step": len(history) + 1, "action": "remove", "term": worst, "aicc": aicc, "bic": bic})
                        changed = True
        if not changed:
            break
    fitted = fit(selected)
    if fitted is None:
        raise AnalysisInputError("selection_no_model", "No selectable model retained residual degrees of freedom.", "predictors")
    aicc, bic = _ols_information_criteria(fitted)
    return ResultBundle(
        analysis_type="regression.stepwise_ols", engine_version=fitted.engine_version,
        input_digest=input_digest({"response": list(response), "predictors": predictors, "response_name": response_name, "interaction_terms": interaction_terms, "method": method, "criterion": criterion, "alpha_enter": alpha_enter, "alpha_remove": alpha_remove, "alpha": alpha}),
        parameters={**fitted.parameters, "selected_terms": selected, "selection_method": method, "selection_criterion": criterion, "interaction_terms": interaction_terms},
        tables={**fitted.tables, "selection_history": {"columns": ["step", "action", "term", "aicc", "bic"], "rows": history}}, plots=fitted.plots,
        diagnostics={**fitted.diagnostics, "aicc": aicc, "bic": bic}, assumptions=(*fitted.assumptions, "Stepwise selection is exploratory and retains lower-order terms required by selected interactions."), warnings=(*fitted.warnings, "Automated selection does not replace engineering knowledge or independent validation."), provenance=fitted.provenance,
    )


def best_subsets_ols(
    response: Sequence[float],
    predictors: Mapping[str, Sequence[float]],
    *,
    response_name: str = "Response",
    top_models_per_size: int = 1,
    alpha: float = 0.05,
) -> ResultBundle:
    """Compare every non-empty OLS subset for at most fifteen numeric predictors."""
    values = finite_values(response, "response")
    columns = {name: finite_values(column, f"predictors.{name}") for name, column in predictors.items()}
    if not columns or any(len(column) != len(values) for column in columns.values()):
        raise AnalysisInputError("invalid_subset_predictors", "Predictors must align with the response.", "predictors")
    if len(columns) > 15:
        raise AnalysisInputError("too_many_subset_predictors", "Best subsets supports at most 15 candidate predictors.", "predictors")
    if not isinstance(top_models_per_size, int) or isinstance(top_models_per_size, bool) or not 1 <= top_models_per_size <= 10:
        raise AnalysisInputError("invalid_subset_count", "Choose between 1 and 10 models per subset size.", "top_models_per_size")
    full = linear_ols(values, columns, response_name=response_name, alpha=alpha)
    full_standard_error = full.diagnostics["residual_standard_error"]
    full_mse = float(full_standard_error) ** 2 if isinstance(full_standard_error, (float, int)) else None
    if full_mse is None or full_mse <= 0:
        raise AnalysisInputError("invalid_full_subset_model", "The full model needs positive residual variation for Mallows' Cp.", "predictors")
    names = list(columns)
    candidates: list[dict[str, object]] = []
    skipped_singular = 0
    for size in range(1, len(names) + 1):
        for subset in combinations(names, size):
            try:
                fitted = linear_ols(values, {name: columns[name] for name in subset}, response_name=response_name, alpha=alpha)
            except AnalysisInputError:
                skipped_singular += 1
                continue
            fitted_rows = fitted.tables["fitted_values"]["rows"]
            residual_ss = sum(float(row["residual"]) ** 2 for row in fitted_rows)
            press = sum((float(row["residual"]) / (1.0 - float(row["leverage"]))) ** 2 for row in fitted_rows if float(row["leverage"]) < 1.0)
            parameter_count = int(fitted.parameters["parameter_count"])
            aicc, bic = _ols_information_criteria(fitted)
            candidates.append({"terms": list(subset), "term_count": size, "r_squared": fitted.diagnostics["r_squared"], "adjusted_r_squared": fitted.diagnostics["adjusted_r_squared"], "press": press, "mallows_cp": residual_ss / float(full_mse) - (len(values) - 2 * parameter_count), "aicc": aicc, "bic": bic})
    if not candidates:
        raise AnalysisInputError("no_subset_models", "No non-singular subset retained residual degrees of freedom.", "predictors")
    ranked: list[dict[str, object]] = []
    for size in range(1, len(names) + 1):
        ranked.extend(sorted((row for row in candidates if row["term_count"] == size), key=lambda row: (float(row["aicc"]), float(row["bic"])))[:top_models_per_size])
    ranked.sort(key=lambda row: (float(row["aicc"]), float(row["bic"])))
    return ResultBundle(
        analysis_type="regression.best_subsets_ols", engine_version=ENGINE_VERSION,
        input_digest=input_digest({"response": values, "predictors": columns, "response_name": response_name, "top_models_per_size": top_models_per_size, "alpha": alpha}),
        parameters={"response_name": response_name, "candidate_predictor_names": names, "top_models_per_size": top_models_per_size, "examined_model_count": len(candidates), "skipped_singular_model_count": skipped_singular},
        tables={"model_comparison": {"columns": ["terms", "term_count", "r_squared", "adjusted_r_squared", "press", "mallows_cp", "aicc", "bic"], "rows": ranked}}, plots={},
        diagnostics={"best_aicc": ranked[0]["aicc"], "best_bic": ranked[0]["bic"], "best_press": min(float(row["press"]) for row in ranked)},
        assumptions=("All candidate terms are numeric, rows are independent, and every eligible non-empty subset is evaluated.",), warnings=("Best-subsets ranking is exploratory; compare process feasibility, validation error, and collinearity before selecting an operating model.",), provenance=(NIST_LINEAR_LEAST_SQUARES_SOURCE,),
    )


def validate_ols(
    response: Sequence[float],
    predictors: Mapping[str, Sequence[float]],
    *,
    response_name: str = "Response",
    method: str = "k_fold",
    folds: int = 5,
    holdout_fraction: float = 0.2,
    alpha: float = 0.05,
) -> ResultBundle:
    """Evaluate OLS on deterministic holdout or k-fold partitions without train/test leakage."""
    values = finite_values(response, "response")
    columns = {name: finite_values(column, f"predictors.{name}") for name, column in predictors.items()}
    if not columns or any(len(column) != len(values) for column in columns.values()):
        raise AnalysisInputError("invalid_validation_predictors", "Predictors must align with the response.", "predictors")
    parameter_count = len(columns) + 1
    if method == "k_fold":
        if not isinstance(folds, int) or isinstance(folds, bool) or folds < 2 or len(values) < folds * 2:
            raise AnalysisInputError("insufficient_validation_observations", "K-fold validation needs at least two observations per fold.", "folds")
        partitions = [list(range(index, len(values), folds)) for index in range(folds)]
    elif method == "holdout":
        if not 0.1 <= holdout_fraction <= 0.5:
            raise AnalysisInputError("invalid_holdout_fraction", "Use a holdout fraction between 0.10 and 0.50.", "holdout_fraction")
        holdout_size = max(1, round(len(values) * holdout_fraction))
        partitions = [list(range(len(values) - holdout_size, len(values)))]
    else:
        raise AnalysisInputError("invalid_validation_method", "Use k_fold or holdout validation.", "method")
    if any(len(values) - len(test_rows) <= parameter_count + 1 for test_rows in partitions):
        raise AnalysisInputError("insufficient_validation_observations", "Each training partition needs residual degrees of freedom.", "response")

    predictions: list[dict[str, float | int]] = []
    fold_rows: list[dict[str, float | int]] = []
    for fold_index, test_rows in enumerate(partitions, start=1):
        test_set = set(test_rows)
        train_rows = [index for index in range(len(values)) if index not in test_set]
        fitted = linear_ols(
            [values[index] for index in train_rows],
            {name: [column[index] for index in train_rows] for name, column in columns.items()},
            response_name=response_name,
            alpha=alpha,
        )
        coefficients = {str(row["term"]): float(row["coefficient"]) for row in fitted.tables["coefficients"]["rows"]}
        fold_errors: list[float] = []
        for index in test_rows:
            predicted = coefficients["Intercept"] + sum(coefficients[name] * columns[name][index] for name in columns)
            error = values[index] - predicted
            fold_errors.append(error)
            predictions.append({"fold": fold_index, "observation": index + 1, "actual": values[index], "predicted": predicted, "residual": error})
        fold_rows.append({"fold": fold_index, "train_size": len(train_rows), "test_size": len(test_rows), "rmse": math.sqrt(sum(error * error for error in fold_errors) / len(fold_errors)), "mae": sum(abs(error) for error in fold_errors) / len(fold_errors)})
    residual_ss = sum(float(row["residual"]) ** 2 for row in predictions)
    mean_actual = fmean(float(row["actual"]) for row in predictions)
    total_ss = sum((float(row["actual"]) - mean_actual) ** 2 for row in predictions)
    return ResultBundle(
        analysis_type="regression.ols_validation", engine_version=ENGINE_VERSION,
        input_digest=input_digest({"response": values, "predictors": columns, "response_name": response_name, "method": method, "folds": folds, "holdout_fraction": holdout_fraction, "alpha": alpha}),
        parameters={"response_name": response_name, "predictor_names": list(columns), "validation_method": method, "fold_count": len(partitions), "sample_size": len(values)},
        tables={"fold_summary": {"columns": ["fold", "train_size", "test_size", "rmse", "mae"], "rows": fold_rows}, "held_out_predictions": {"columns": ["fold", "observation", "actual", "predicted", "residual"], "rows": predictions}}, plots={},
        diagnostics={"rmse": math.sqrt(residual_ss / len(predictions)), "mae": sum(abs(float(row["residual"])) for row in predictions) / len(predictions), "r_squared_pred": 1.0 - residual_ss / total_ss if total_ss else None},
        assumptions=("Validation folds retain the input row order and are deterministic; use time-aware splits when order encodes process time.",), warnings=("Validation estimates prediction error for comparable future observations; review drift, leakage, and process constraints.",), provenance=(NIST_LINEAR_LEAST_SQUARES_SOURCE,),
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
    assumption_diagnostics = _ols_assumption_diagnostics(residuals, matrix, inverse, alpha=normalized_alpha)
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
    influence_thresholds = {
        "leverage": 2.0 * parameter_count / sample_size,
        "standardized_residual": 2.0,
        "studentized_residual": 2.0,
        "cooks_distance": 4.0 / sample_size,
        "dffits": 2.0 * math.sqrt(parameter_count / sample_size),
    }
    for index, (actual, prediction, residual) in enumerate(zip(values, fitted, residuals, strict=True)):
        leverage = sum(
            matrix[index][left] * inverse[left][right] * matrix[index][right]
            for left in range(parameter_count) for right in range(parameter_count)
        )
        prediction_margin = t_critical * math.sqrt(residual_ms * (1.0 + leverage))
        remaining_variance = residual_ms * (1.0 - leverage)
        standardized_residual = residual / math.sqrt(remaining_variance) if remaining_variance > 0.0 else None
        deleted_ss = residual_ss - residual * residual / (1.0 - leverage) if leverage < 1.0 else None
        deleted_ms = deleted_ss / (residual_df - 1) if deleted_ss is not None and residual_df > 1 else None
        studentized_residual = residual / math.sqrt(deleted_ms * (1.0 - leverage)) if deleted_ms is not None and deleted_ms > 0.0 and leverage < 1.0 else None
        cooks_distance = residual * residual * leverage / (parameter_count * residual_ms * (1.0 - leverage) ** 2) if residual_ms > 0.0 and leverage < 1.0 else None
        dffits = studentized_residual * math.sqrt(leverage / (1.0 - leverage)) if studentized_residual is not None and leverage < 1.0 else None
        fitted_rows.append({
            "observation": index + 1, "actual": actual, "fitted": prediction,
            "residual": residual, "leverage": leverage,
            "prediction_interval_lower": prediction - prediction_margin,
            "prediction_interval_upper": prediction + prediction_margin,
            "standardized_residual": standardized_residual,
            "studentized_residual": studentized_residual,
            "cooks_distance": cooks_distance,
            "dffits": dffits,
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
    if assumption_diagnostics["reject_residual_normality"]:
        warnings.append("Residual normality diagnostic rejected the normal-error approximation; treat coefficient and model p-values cautiously.")
    if assumption_diagnostics["reject_constant_variance"]:
        warnings.append("Breusch-Pagan residual diagnostic rejected constant variance; review variance structure and consider an appropriate alternative model.")
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
            "fitted_values": {"columns": ["observation", "actual", "fitted", "residual", "leverage", "prediction_interval_lower", "prediction_interval_upper", "standardized_residual", "studentized_residual", "cooks_distance", "dffits"], "rows": fitted_rows},
            "collinearity": {"columns": ["term", "vif", "tolerance"], "rows": collinearity_rows},
        },
        plots={},
        diagnostics={"r_squared": r_squared, "adjusted_r_squared": adjusted_r_squared, "residual_standard_error": math.sqrt(residual_ms), "residual_degrees_of_freedom": residual_df, "model_f_statistic": model_f, "model_p_value": model_p, "prediction_interval_confidence": 1.0 - normalized_alpha, "maximum_vif": maximum_vif, "influence_thresholds": influence_thresholds, **assumption_diagnostics},
        assumptions=(
            "The response is continuous and observations are aligned by row.",
            "Errors are independent with approximately constant variance.",
            "Coefficient and model inference additionally use the usual normal-error approximation.",
        ),
        warnings=tuple(warnings),
        provenance=(NIST_LINEAR_LEAST_SQUARES_SOURCE, NIST_LEAST_SQUARES_GLOSSARY_SOURCE, NIST_REGRESSION_DIAGNOSTICS_SOURCE),
    )
