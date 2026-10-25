"""StatPro statistical analysis core."""

from statpro.analyses.capability import normal_process_capability
from statpro.analyses.doe import (
    FactorDefinition,
    GeneratorDefinition,
    analyze_box_behnken,
    analyze_central_composite,
    analyze_fractional_factorial_2level,
    analyze_plackett_burman,
    box_behnken_design,
    central_composite_design,
    explore_central_composite_surface,
    fractional_factorial_2level,
    full_factorial_2level,
    plackett_burman_design,
)
from statpro.analyses.msa import MeasurementRecord, gage_rr_crossed
from statpro.analyses.spc import (
    c_chart,
    individuals_moving_range,
    np_chart,
    p_chart,
    u_chart,
    xbar_r,
)
from statpro.domain.data import DatasetSnapshot, DataType, WorksheetSnapshot
from statpro.domain.models import ResultBundle
from statpro.version import __version__

__all__ = [
    "DataType",
    "DatasetSnapshot",
    "FactorDefinition",
    "GeneratorDefinition",
    "MeasurementRecord",
    "ResultBundle",
    "WorksheetSnapshot",
    "__version__",
    "analyze_box_behnken",
    "analyze_central_composite",
    "analyze_fractional_factorial_2level",
    "analyze_plackett_burman",
    "box_behnken_design",
    "c_chart",
    "central_composite_design",
    "explore_central_composite_surface",
    "fractional_factorial_2level",
    "full_factorial_2level",
    "gage_rr_crossed",
    "individuals_moving_range",
    "normal_process_capability",
    "np_chart",
    "p_chart",
    "plackett_burman_design",
    "u_chart",
    "xbar_r",
]
