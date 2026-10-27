"""JSON command-line adapter for the StatPro statistical core."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from statpro.analyses.capability import normal_process_capability
from statpro.analyses.doe import (
    FactorDefinition,
    GeneratorDefinition,
    ResponseObjective,
    analyze_automatic_fractional_factorial_2level,
    analyze_box_behnken,
    analyze_central_composite,
    analyze_fractional_factorial_2level,
    analyze_full_factorial_2level,
    analyze_plackett_burman,
    automatic_fractional_factorial_2level,
    box_behnken_design,
    central_composite_design,
    explore_box_behnken_surface,
    explore_central_composite_surface,
    fractional_factorial_2level,
    full_factorial_2level,
    optimize_full_factorial_desirability,
    plackett_burman_design,
)
from statpro.analyses.msa import MeasurementRecord, gage_rr_crossed
from statpro.analyses.spc import (
    c_chart,
    cusum_chart,
    ewma_chart,
    individuals_moving_range,
    laney_p_prime,
    laney_u_prime,
    np_chart,
    p_chart,
    u_chart,
    xbar_r,
    xbar_s,
)
from statpro.domain.data import import_csv_dataset
from statpro.domain.errors import AnalysisInputError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="statpro")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in (
        "c-chart",
        "cusum",
        "ewma",
        "imr",
        "laney-p-prime",
        "laney-u-prime",
        "np-chart",
        "p-chart",
        "u-chart",
        "xbar-r",
        "xbar-s",
        "capability-normal",
        "doe-full-factorial",
        "doe-central-composite",
        "doe-box-behnken",
        "doe-analyze-box-behnken",
        "doe-explore-box-behnken",
        "doe-analyze-central-composite",
        "doe-explore-central-composite",
        "doe-fractional-factorial",
        "doe-fractional-factorial-auto",
        "doe-analyze-fractional-factorial",
        "doe-analyze-fractional-factorial-auto",
        "doe-plackett-burman",
        "doe-analyze-plackett-burman",
        "doe-analyze-full-factorial",
        "doe-optimize-responses",
        "gage-rr-crossed",
        "dataset-import-csv",
    ):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--input", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "dataset-import-csv":
            dataset = import_csv_dataset(args.input)
            print(json.dumps({"ok": True, "dataset": dataset.to_dict()}, ensure_ascii=False, indent=2))
            return 0
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if args.command == "imr":
            result = individuals_moving_range(
                payload["values"],
                target=payload.get("target"),
                sigma=payload.get("sigma"),
                stage=payload.get("stage", "phase_1"),
                rules=payload.get("rules", "western_electric"),
            )
        elif args.command == "p-chart":
            result = p_chart(payload["nonconforming"], payload["sample_sizes"])
        elif args.command == "np-chart":
            result = np_chart(payload["nonconforming"], payload["sample_sizes"])
        elif args.command == "c-chart":
            result = c_chart(payload["defects"], payload.get("inspection_units"))
        elif args.command == "u-chart":
            result = u_chart(payload["defects"], payload["inspection_units"])
        elif args.command == "ewma":
            result = ewma_chart(
                payload["values"],
                target=payload.get("target"),
                sigma=payload.get("sigma"),
                stage=payload.get("stage", "phase_1"),
                weight=payload.get("weight", 0.2),
                limit_width=payload.get("limit_width", 3.0),
            )
        elif args.command == "cusum":
            result = cusum_chart(
                payload["values"],
                target=payload.get("target"),
                sigma=payload.get("sigma"),
                stage=payload.get("stage", "phase_1"),
                reference_value=payload.get("reference_value", 0.5),
                decision_interval=payload.get("decision_interval", 4.0),
            )
        elif args.command == "laney-p-prime":
            result = laney_p_prime(payload["nonconforming"], payload["sample_sizes"])
        elif args.command == "laney-u-prime":
            result = laney_u_prime(payload["defects"], payload["inspection_units"])
        elif args.command == "xbar-r":
            result = xbar_r(
                payload["subgroups"],
                rules=payload.get("rules", "basic"),
            )
        elif args.command == "xbar-s":
            result = xbar_s(
                payload["subgroups"],
                rules=payload.get("rules", "basic"),
            )
        elif args.command == "capability-normal":
            result = normal_process_capability(
                payload["values"],
                lsl=payload.get("lsl"),
                usl=payload.get("usl"),
                target=payload.get("target"),
            )
        elif args.command in {
            "doe-full-factorial",
            "doe-central-composite",
            "doe-box-behnken",
            "doe-analyze-box-behnken",
            "doe-explore-box-behnken",
            "doe-analyze-central-composite",
            "doe-explore-central-composite",
            "doe-fractional-factorial",
            "doe-fractional-factorial-auto",
            "doe-analyze-fractional-factorial",
            "doe-analyze-fractional-factorial-auto",
            "doe-plackett-burman",
            "doe-analyze-plackett-burman",
            "doe-analyze-full-factorial",
            "doe-optimize-responses",
        }:
            try:
                factors = [FactorDefinition(**factor) for factor in payload["factors"]]
            except TypeError as error:
                raise AnalysisInputError(
                    "invalid_factor_definition",
                    "Each factor requires name, low, and high fields.",
                    "factors",
                ) from error
            if args.command == "doe-box-behnken":
                result = box_behnken_design(
                    factors,
                    center_points=payload.get("center_points"),
                    replicates=payload.get("replicates", 1),
                    randomize=payload.get("randomize", True),
                    seed=payload.get("seed", 0),
                )
            elif args.command == "doe-analyze-box-behnken":
                result = analyze_box_behnken(
                    factors,
                    payload["responses"],
                    response_name=payload.get("response_name", "Response"),
                    center_points=payload.get("center_points"),
                    replicates=payload.get("replicates", 1),
                    randomize=payload.get("randomize", True),
                    seed=payload.get("seed", 0),
                    alpha=payload.get("alpha", 0.05),
                )
            elif args.command == "doe-explore-box-behnken":
                result = explore_box_behnken_surface(
                    factors,
                    payload["responses"],
                    response_name=payload.get("response_name", "Response"),
                    center_points=payload.get("center_points"),
                    replicates=payload.get("replicates", 1),
                    randomize=payload.get("randomize", True),
                    seed=payload.get("seed", 0),
                    alpha=payload.get("alpha", 0.05),
                    plot_factors=payload.get("plot_factors"),
                    hold_values=payload.get("hold_values"),
                    grid_size=payload.get("grid_size", 21),
                    contour_levels=payload.get("contour_levels", 7),
                )
            elif args.command == "doe-analyze-plackett-burman":
                result = analyze_plackett_burman(
                    factors,
                    payload["responses"],
                    response_name=payload.get("response_name", "Response"),
                    runs=payload.get("runs"),
                    replicates=payload.get("replicates", 1),
                    center_points=payload.get("center_points", 0),
                    randomize=payload.get("randomize", True),
                    seed=payload.get("seed", 0),
                    alpha=payload.get("alpha", 0.05),
                )
            elif args.command == "doe-explore-central-composite":
                result = explore_central_composite_surface(
                    factors,
                    payload["responses"],
                    response_name=payload.get("response_name", "Response"),
                    design_type=payload.get("design_type", "rotatable"),
                    center_points=payload.get("center_points", 5),
                    replicates=payload.get("replicates", 1),
                    randomize=payload.get("randomize", True),
                    seed=payload.get("seed", 0),
                    alpha=payload.get("alpha", 0.05),
                    plot_factors=payload.get("plot_factors"),
                    hold_values=payload.get("hold_values"),
                    grid_size=payload.get("grid_size", 21),
                    contour_levels=payload.get("contour_levels", 7),
                )
            elif args.command == "doe-analyze-central-composite":
                result = analyze_central_composite(
                    factors,
                    payload["responses"],
                    response_name=payload.get("response_name", "Response"),
                    design_type=payload.get("design_type", "rotatable"),
                    center_points=payload.get("center_points", 5),
                    replicates=payload.get("replicates", 1),
                    randomize=payload.get("randomize", True),
                    seed=payload.get("seed", 0),
                    alpha=payload.get("alpha", 0.05),
                )
            elif args.command == "doe-central-composite":
                result = central_composite_design(
                    factors,
                    design_type=payload.get("design_type", "rotatable"),
                    center_points=payload.get("center_points", 5),
                    replicates=payload.get("replicates", 1),
                    randomize=payload.get("randomize", True),
                    seed=payload.get("seed", 0),
                )
            elif args.command == "doe-plackett-burman":
                result = plackett_burman_design(
                    factors,
                    runs=payload.get("runs"),
                    replicates=payload.get("replicates", 1),
                    center_points=payload.get("center_points", 0),
                    randomize=payload.get("randomize", True),
                    seed=payload.get("seed", 0),
                )
            elif args.command in {
                "doe-fractional-factorial",
                "doe-analyze-fractional-factorial",
            }:
                try:
                    generators = [
                        GeneratorDefinition(**generator)
                        for generator in payload["generators"]
                    ]
                except TypeError as error:
                    raise AnalysisInputError(
                        "invalid_generator_definition",
                        "Each generator requires factor and terms fields.",
                        "generators",
                    ) from error
                fractional_arguments = {
                    "block_generators": payload.get("block_generators", []),
                    "replicates": payload.get("replicates", 1),
                    "foldover": payload.get("foldover", False),
                    "foldover_factor": payload.get("foldover_factor"),
                    "randomize": payload.get("randomize", True),
                    "seed": payload.get("seed", 0),
                }
                if args.command == "doe-analyze-fractional-factorial":
                    result = analyze_fractional_factorial_2level(
                        factors,
                        generators,
                        payload["responses"],
                        response_name=payload.get("response_name", "Response"),
                        alpha=payload.get("alpha", 0.05),
                        **fractional_arguments,
                    )
                else:
                    result = fractional_factorial_2level(
                        factors,
                        generators,
                        **fractional_arguments,
                    )
            elif args.command in {
                "doe-fractional-factorial-auto",
                "doe-analyze-fractional-factorial-auto",
            }:
                automatic_arguments = {
                    "runs": payload.get("runs"),
                    "minimum_resolution": payload.get("minimum_resolution", 3),
                    "block_generators": payload.get("block_generators", []),
                    "replicates": payload.get("replicates", 1),
                    "foldover": payload.get("foldover", False),
                    "foldover_factor": payload.get("foldover_factor"),
                    "randomize": payload.get("randomize", True),
                    "seed": payload.get("seed", 0),
                }
                if args.command == "doe-analyze-fractional-factorial-auto":
                    result = analyze_automatic_fractional_factorial_2level(
                        factors,
                        payload["responses"],
                        response_name=payload.get("response_name", "Response"),
                        alpha=payload.get("alpha", 0.05),
                        **automatic_arguments,
                    )
                else:
                    result = automatic_fractional_factorial_2level(
                        factors,
                        **automatic_arguments,
                    )
            elif args.command == "doe-optimize-responses":
                try:
                    objectives = [
                        ResponseObjective(**objective)
                        for objective in payload["objectives"]
                    ]
                except TypeError as error:
                    raise AnalysisInputError(
                        "invalid_response_objective",
                        "Each objective requires name, responses, goal, and target fields.",
                        "objectives",
                    ) from error
                result = optimize_full_factorial_desirability(
                    factors,
                    objectives,
                    replicates=payload.get("replicates", 1),
                    center_points=payload.get("center_points", 0),
                    blocks=payload.get("blocks", 1),
                    randomize=payload.get("randomize", True),
                    seed=payload.get("seed", 0),
                    interaction_order=payload.get("interaction_order", 2),
                )
            elif args.command == "doe-analyze-full-factorial":
                result = analyze_full_factorial_2level(
                    factors,
                    payload["responses"],
                    response_name=payload.get("response_name", "Response"),
                    replicates=payload.get("replicates", 1),
                    center_points=payload.get("center_points", 0),
                    blocks=payload.get("blocks", 1),
                    randomize=payload.get("randomize", True),
                    seed=payload.get("seed", 0),
                    interaction_order=payload.get("interaction_order", 2),
                    prediction_points=payload.get("prediction_points", []),
                    optimization_goal=payload.get("optimization_goal"),
                )
            else:
                result = full_factorial_2level(
                    factors,
                    replicates=payload.get("replicates", 1),
                    center_points=payload.get("center_points", 0),
                    blocks=payload.get("blocks", 1),
                    randomize=payload.get("randomize", True),
                    seed=payload.get("seed", 0),
                )
        else:
            try:
                records = [MeasurementRecord(**record) for record in payload["records"]]
            except TypeError as error:
                raise AnalysisInputError(
                    "invalid_measurement_record",
                    "Each record requires part, operator, and measurement fields.",
                    "records",
                ) from error
            result = gage_rr_crossed(
                records,
                study_variation_multiplier=payload.get("study_variation_multiplier", 6.0),
            )
    except AnalysisInputError as error:
        print(json.dumps({"ok": False, "error": error.to_dict()}, ensure_ascii=False, indent=2))
        return 2
    except (OSError, json.JSONDecodeError, KeyError) as error:
        print(
            json.dumps(
                {"ok": False, "error": {"code": "invalid_input_file", "message": str(error)}},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    print(json.dumps({"ok": True, "result": result.to_dict()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
