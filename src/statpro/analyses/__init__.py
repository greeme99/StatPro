"""Statistical analysis implementations."""

from statpro.analyses.capability import normal_process_capability
from statpro.analyses.doe import (
    FactorDefinition,
    GeneratorDefinition,
    analyze_full_factorial_2level,
    fractional_factorial_2level,
    full_factorial_2level,
    plackett_burman_design,
)
from statpro.analyses.spc import individuals_moving_range, xbar_r

__all__ = [
    "FactorDefinition",
    "GeneratorDefinition",
    "analyze_full_factorial_2level",
    "fractional_factorial_2level",
    "full_factorial_2level",
    "plackett_burman_design",
    "individuals_moving_range",
    "normal_process_capability",
    "xbar_r",
]
