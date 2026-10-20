"""JSON command-line adapter for the StatPro statistical core."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from statpro.analyses.capability import normal_process_capability
from statpro.analyses.doe import (
    FactorDefinition,
    analyze_full_factorial_2level,
    full_factorial_2level,
)
from statpro.analyses.msa import MeasurementRecord, gage_rr_crossed
from statpro.analyses.spc import individuals_moving_range, xbar_r
from statpro.domain.errors import AnalysisInputError
from statpro.domain.data import import_csv_dataset


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="statpro")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in (
        "imr",
        "xbar-r",
        "capability-normal",
        "doe-full-factorial",
        "doe-analyze-full-factorial",
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
            result = individuals_moving_range(payload["values"], target=payload.get("target"))
        elif args.command == "xbar-r":
            result = xbar_r(payload["subgroups"])
        elif args.command == "capability-normal":
            result = normal_process_capability(
                payload["values"],
                lsl=payload.get("lsl"),
                usl=payload.get("usl"),
                target=payload.get("target"),
            )
        elif args.command in {"doe-full-factorial", "doe-analyze-full-factorial"}:
            try:
                factors = [FactorDefinition(**factor) for factor in payload["factors"]]
            except TypeError as error:
                raise AnalysisInputError(
                    "invalid_factor_definition",
                    "Each factor requires name, low, and high fields.",
                    "factors",
                ) from error
            if args.command == "doe-analyze-full-factorial":
                result = analyze_full_factorial_2level(
                    factors,
                    payload["responses"],
                    response_name=payload.get("response_name", "Response"),
                    replicates=payload.get("replicates", 1),
                    center_points=payload.get("center_points", 0),
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
