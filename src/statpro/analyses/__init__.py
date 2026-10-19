"""Statistical analysis implementations."""

from statpro.analyses.capability import normal_process_capability
from statpro.analyses.doe import FactorDefinition, full_factorial_2level
from statpro.analyses.spc import individuals_moving_range, xbar_r

__all__ = [
    "FactorDefinition",
    "full_factorial_2level",
    "individuals_moving_range",
    "normal_process_capability",
    "xbar_r",
]
