"""StatPro statistical analysis core."""

from statpro.analyses.capability import normal_process_capability
from statpro.analyses.doe import (
    FactorDefinition,
    GeneratorDefinition,
    analyze_plackett_burman,
    fractional_factorial_2level,
    full_factorial_2level,
    plackett_burman_design,
)
from statpro.analyses.msa import MeasurementRecord, gage_rr_crossed
from statpro.analyses.spc import individuals_moving_range, xbar_r
from statpro.domain.models import ResultBundle
from statpro.domain.data import DatasetSnapshot, DataType, WorksheetSnapshot
from statpro.version import __version__

__all__ = [
    "FactorDefinition",
    "GeneratorDefinition",
    "analyze_plackett_burman",
    "DatasetSnapshot",
    "DataType",
    "MeasurementRecord",
    "ResultBundle",
    "WorksheetSnapshot",
    "full_factorial_2level",
    "fractional_factorial_2level",
    "plackett_burman_design",
    "gage_rr_crossed",
    "individuals_moving_range",
    "normal_process_capability",
    "xbar_r",
]
