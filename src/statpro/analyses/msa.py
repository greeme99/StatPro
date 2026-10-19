"""Measurement-system analyses with explicit design validation."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from statistics import fmean
from typing import Sequence

from statpro.analyses.common import finite_values, input_digest
from statpro.domain.errors import AnalysisInputError
from statpro.domain.models import ProvenanceSource, ResultBundle
from statpro.version import ENGINE_VERSION

NIST_GAGE_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 2.4 Gauge R&R studies",
    url="https://www.itl.nist.gov/div898/handbook/mpc/section4/mpc4.htm",
)
NIST_TWO_WAY_ANOVA_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 7.4.3.2 Two-way crossed ANOVA",
    url="https://www.itl.nist.gov/div898/handbook/ppc/section2/ppc232.htm",
)
NIST_VARIANCE_COMPONENTS_SOURCE = ProvenanceSource(
    title="NIST/SEMATECH 7.4.4 Variance components",
    url="https://www.itl.nist.gov/div898/handbook/prc/section4/prc44.htm",
)
NDC_SOURCE = ProvenanceSource(
    title="Minitab: Using the number of distinct categories in a gage R&R study",
    url=(
        "https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-"
        "improvement/measurement-system-analysis/supporting-topics/gage-r-r-and-wheeler-s-"
        "emp-studies/using-the-number-of-distinct-categories-in-a-gage-r-r-study/"
    ),
)


@dataclass(frozen=True, slots=True)
class MeasurementRecord:
    part: str
    operator: str
    measurement: float


def _normalize_records(records: Sequence[MeasurementRecord]) -> list[MeasurementRecord]:
    if len(records) > 100_000:
        raise AnalysisInputError(
            "study_too_large",
            "The bounded Gage R&R implementation supports at most 100,000 measurements.",
            "records",
        )

    normalized: list[MeasurementRecord] = []
    for index, record in enumerate(records):
        part = record.part.strip()
        operator = record.operator.strip()
        if not part:
            raise AnalysisInputError(
                "empty_part_label", f"Record {index + 1} needs a part label.", "records"
            )
        if not operator:
            raise AnalysisInputError(
                "empty_operator_label",
                f"Record {index + 1} needs an operator label.",
                "records",
            )
        measurement = finite_values([record.measurement], f"records[{index}].measurement")[0]
        normalized.append(
            MeasurementRecord(part=part, operator=operator, measurement=measurement)
        )
    return normalized


def gage_rr_crossed(
    records: Sequence[MeasurementRecord], *, study_variation_multiplier: float = 6.0
) -> ResultBundle:
    """Estimate crossed Gage R&R variance components for a balanced replicated study."""

    normalized = _normalize_records(records)
    multiplier = finite_values([study_variation_multiplier], "study_variation_multiplier")[0]
    if multiplier <= 0.0:
        raise AnalysisInputError(
            "invalid_study_variation_multiplier",
            "Study variation multiplier must be greater than zero.",
            "study_variation_multiplier",
        )

    parts = sorted({record.part for record in normalized})
    operators = sorted({record.operator for record in normalized})
    if len(parts) < 2:
        raise AnalysisInputError(
            "insufficient_parts", "Gage R&R requires at least two parts.", "records"
        )
    if len(operators) < 2:
        raise AnalysisInputError(
            "insufficient_operators", "Gage R&R requires at least two operators.", "records"
        )

    cells: dict[tuple[str, str], list[float]] = defaultdict(list)
    for record in normalized:
        cells[(record.part, record.operator)].append(record.measurement)
    expected_cells = [(part, operator) for part in parts for operator in operators]
    missing_cells = sorted(set(expected_cells) - set(cells))
    if missing_cells:
        raise AnalysisInputError(
            "incomplete_crossed_design",
            "Every operator must measure every part; one or more cells are missing.",
            "records",
        )

    replicate_counts = {len(cells[cell]) for cell in expected_cells}
    if len(replicate_counts) != 1:
        raise AnalysisInputError(
            "unbalanced_design",
            "Every part-operator cell must have the same replicate count.",
            "records",
        )
    replicates = next(iter(replicate_counts))
    if replicates < 2:
        raise AnalysisInputError(
            "insufficient_replicates",
            "Each part-operator cell requires at least two repeated measurements.",
            "records",
        )

    part_count = len(parts)
    operator_count = len(operators)
    values = [record.measurement for record in normalized]
    grand_mean = fmean(values)
    cell_means = {cell: fmean(cells[cell]) for cell in expected_cells}
    part_means = {
        part: fmean(record.measurement for record in normalized if record.part == part)
        for part in parts
    }
    operator_means = {
        operator: fmean(
            record.measurement for record in normalized if record.operator == operator
        )
        for operator in operators
    }

    ss_part = operator_count * replicates * sum(
        (part_means[part] - grand_mean) ** 2 for part in parts
    )
    ss_operator = part_count * replicates * sum(
        (operator_means[operator] - grand_mean) ** 2 for operator in operators
    )
    ss_interaction = replicates * sum(
        (
            cell_means[(part, operator)]
            - part_means[part]
            - operator_means[operator]
            + grand_mean
        )
        ** 2
        for part, operator in expected_cells
    )
    ss_repeatability = sum(
        (measurement - cell_means[cell]) ** 2
        for cell in expected_cells
        for measurement in cells[cell]
    )
    ss_total = sum((value - grand_mean) ** 2 for value in values)

    df_part = part_count - 1
    df_operator = operator_count - 1
    df_interaction = df_part * df_operator
    df_repeatability = part_count * operator_count * (replicates - 1)
    df_total = len(normalized) - 1
    ms_part = ss_part / df_part
    ms_operator = ss_operator / df_operator
    ms_interaction = ss_interaction / df_interaction
    ms_repeatability = ss_repeatability / df_repeatability

    raw_variances = {
        "repeatability": ms_repeatability,
        "operator": (ms_operator - ms_interaction) / (part_count * replicates),
        "part_operator_interaction": (ms_interaction - ms_repeatability) / replicates,
        "part_to_part": (ms_part - ms_interaction) / (operator_count * replicates),
    }
    component_variances = {
        name: max(value, 0.0) for name, value in raw_variances.items()
    }
    component_variances["reproducibility"] = (
        component_variances["operator"]
        + component_variances["part_operator_interaction"]
    )
    component_variances["total_gage_rr"] = (
        component_variances["repeatability"] + component_variances["reproducibility"]
    )
    component_variances["total_variation"] = (
        component_variances["total_gage_rr"] + component_variances["part_to_part"]
    )
    total_variance = component_variances["total_variation"]
    if total_variance == 0.0:
        raise AnalysisInputError(
            "zero_total_variation",
            "Gage R&R is undefined when all estimated variation is zero.",
            "records",
        )

    total_standard_deviation = math.sqrt(total_variance)
    component_order = (
        "repeatability",
        "operator",
        "part_operator_interaction",
        "reproducibility",
        "total_gage_rr",
        "part_to_part",
        "total_variation",
    )
    variance_rows = []
    for name in component_order:
        variance = component_variances[name]
        standard_deviation = math.sqrt(variance)
        variance_rows.append(
            {
                "source": name,
                "variance": variance,
                "standard_deviation": standard_deviation,
                "study_variation": multiplier * standard_deviation,
                "contribution_percent": variance / total_variance * 100.0,
                "study_variation_percent": (
                    standard_deviation / total_standard_deviation * 100.0
                ),
            }
        )

    gage_standard_deviation = math.sqrt(component_variances["total_gage_rr"])
    part_standard_deviation = math.sqrt(component_variances["part_to_part"])
    ndc = (
        None
        if gage_standard_deviation == 0.0
        else max(1, math.floor(1.41 * part_standard_deviation / gage_standard_deviation))
    )
    warnings = [
        f"Negative {name} variance estimate was truncated to zero."
        for name, value in raw_variances.items()
        if value < 0.0
    ]
    warnings.append(
        "This method-of-moments result does not perform significance tests, interaction pooling, or REML estimation."
    )
    if ndc is None:
        warnings.append(
            "The number of distinct categories is unbounded because estimated total Gage R&R variation is zero."
        )

    payload = {
        "records": [asdict(record) for record in normalized],
        "study_variation_multiplier": multiplier,
    }
    return ResultBundle(
        analysis_type="msa.gage_rr_crossed",
        engine_version=ENGINE_VERSION,
        input_digest=input_digest(payload),
        parameters={
            "study_variation_multiplier": multiplier,
            "variance_estimation": "balanced_crossed_anova_method_of_moments",
            "negative_variance_policy": "truncate_to_zero",
        },
        tables={
            "study": {
                "measurement_count": len(normalized),
                "part_count": part_count,
                "operator_count": operator_count,
                "replicates_per_cell": replicates,
                "grand_mean": grand_mean,
            },
            "anova": [
                {"source": "part", "df": df_part, "ss": ss_part, "ms": ms_part},
                {
                    "source": "operator",
                    "df": df_operator,
                    "ss": ss_operator,
                    "ms": ms_operator,
                },
                {
                    "source": "part_operator_interaction",
                    "df": df_interaction,
                    "ss": ss_interaction,
                    "ms": ms_interaction,
                },
                {
                    "source": "repeatability",
                    "df": df_repeatability,
                    "ss": ss_repeatability,
                    "ms": ms_repeatability,
                },
                {"source": "total", "df": df_total, "ss": ss_total, "ms": None},
            ],
            "variance_components": variance_rows,
        },
        plots={
            "measurement_variation": {
                "records": [asdict(record) for record in normalized],
                "part_means": part_means,
                "operator_means": operator_means,
            }
        },
        diagnostics={
            "balanced": True,
            "fully_crossed": True,
            "raw_variance_estimates": raw_variances,
            "anova_decomposition_error": ss_total
            - ss_part
            - ss_operator
            - ss_interaction
            - ss_repeatability,
            "negative_variance_policy": "truncate_to_zero",
            "number_of_distinct_categories": ndc,
            "number_of_distinct_categories_unbounded": ndc is None,
        },
        assumptions=(
            "Parts, operators, and their interaction are random effects representative of use.",
            "Residuals are independent, approximately normal, and have constant variance.",
            "Every operator measures every part the same number of times.",
            "The measurement process is stable during the study.",
        ),
        warnings=tuple(warnings),
        provenance=(
            NIST_GAGE_SOURCE,
            NIST_TWO_WAY_ANOVA_SOURCE,
            NIST_VARIANCE_COMPONENTS_SOURCE,
            NDC_SOURCE,
        ),
    )
