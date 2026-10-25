"""Statistical analysis implementations."""

from statpro.analyses.capability import normal_process_capability
from statpro.analyses.doe import (
    FactorDefinition,
    GeneratorDefinition,
    analyze_box_behnken,
    analyze_central_composite,
    analyze_fractional_factorial_2level,
    analyze_full_factorial_2level,
    analyze_plackett_burman,
    box_behnken_design,
    central_composite_design,
    explore_central_composite_surface,
    fractional_factorial_2level,
    full_factorial_2level,
    plackett_burman_design,
)
from statpro.analyses.spc import individuals_moving_range, xbar_r

__all__ = [
    "FactorDefinition",
    "GeneratorDefinition",
    "analyze_box_behnken",
    "analyze_central_composite",
    "analyze_fractional_factorial_2level",
    "analyze_full_factorial_2level",
    "analyze_plackett_burman",
    "box_behnken_design",
    "central_composite_design",
    "explore_central_composite_surface",
    "fractional_factorial_2level",
    "full_factorial_2level",
    "individuals_moving_range",
    "normal_process_capability",
    "plackett_burman_design",
    "xbar_r",
]
