"""Statistical analysis implementations."""

from statpro.analyses.capability import normal_process_capability
from statpro.analyses.doe import (
    FactorDefinition,
    GeneratorDefinition,
    analyze_automatic_fractional_factorial_2level,
    analyze_box_behnken,
    analyze_central_composite,
    analyze_fractional_factorial_2level,
    analyze_full_factorial_2level,
    analyze_plackett_burman,
    automatic_fractional_factorial_2level,
    box_behnken_design,
    central_composite_design,
    explore_central_composite_surface,
    fractional_factorial_2level,
    full_factorial_2level,
    plackett_burman_design,
)
from statpro.analyses.spc import (
    c_chart,
    individuals_moving_range,
    np_chart,
    p_chart,
    u_chart,
    xbar_r,
)

__all__ = [
    "FactorDefinition",
    "GeneratorDefinition",
    "analyze_automatic_fractional_factorial_2level",
    "analyze_box_behnken",
    "analyze_central_composite",
    "analyze_fractional_factorial_2level",
    "analyze_full_factorial_2level",
    "analyze_plackett_burman",
    "automatic_fractional_factorial_2level",
    "box_behnken_design",
    "c_chart",
    "central_composite_design",
    "explore_central_composite_surface",
    "fractional_factorial_2level",
    "full_factorial_2level",
    "individuals_moving_range",
    "normal_process_capability",
    "np_chart",
    "p_chart",
    "plackett_burman_design",
    "u_chart",
    "xbar_r",
]
