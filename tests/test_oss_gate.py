from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("oss_gate", ROOT / "tools" / "oss_gate.py")
assert SPEC is not None and SPEC.loader is not None
oss_gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oss_gate)


class OssGateTests(unittest.TestCase):
    def test_repository_policy_and_sbom_are_current(self) -> None:
        self.assertEqual(oss_gate.main(["--check"]), 0)

    def test_license_expression_extracts_every_choice(self) -> None:
        self.assertEqual(oss_gate._license_ids("MIT AND ISC"), {"MIT", "ISC"})
        self.assertEqual(
            oss_gate._license_ids("(Apache-2.0 OR MPL-2.0)"),
            {"Apache-2.0", "MPL-2.0"},
        )

    def test_unregistered_direct_dependency_fails_closed(self) -> None:
        policy = {
            "allowed_spdx_licenses": ["MIT"],
            "npm_direct_dependencies": {},
            "python_direct_dependencies": {},
        }
        package = {"dependencies": {"react": "1"}}
        lock = {"packages": {"": {"dependencies": {"react": "1"}}}}
        pyproject = {"project": {"optional-dependencies": {}}}
        with self.assertRaisesRegex(oss_gate.GateError, "registry mismatch"):
            oss_gate._validate_policy(policy, package, lock, pyproject)

    def test_unapproved_transitive_license_fails_closed(self) -> None:
        policy = {
            "allowed_spdx_licenses": ["MIT"],
            "npm_direct_dependencies": {},
            "python_direct_dependencies": {},
        }
        package: dict[str, object] = {}
        lock = {
            "packages": {
                "": {},
                "node_modules/example": {"version": "1.0.0", "license": "GPL-3.0-only"},
            }
        }
        pyproject = {"project": {"optional-dependencies": {}}}
        with self.assertRaisesRegex(oss_gate.GateError, "unapproved license"):
            oss_gate._validate_policy(policy, package, lock, pyproject)

    def test_benchmark_only_dependency_cannot_enter_product_source(self) -> None:
        policy = {
            "npm_direct_dependencies": {
                "echarts": {"boundary": "benchmark-only"},
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            source_root = Path(directory)
            (source_root / "chart.ts").write_text(
                'import { init } from "echarts/core";\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(oss_gate.GateError, "Benchmark-only"):
                oss_gate._validate_npm_boundaries(policy, source_root)

    def test_sbom_component_references_are_unique(self) -> None:
        policy = oss_gate._load_json(oss_gate.POLICY_PATH)
        lock = oss_gate._load_json(oss_gate.LOCK_PATH)
        with oss_gate.PYPROJECT_PATH.open("rb") as stream:
            import tomllib

            pyproject = tomllib.load(stream)
        sbom = oss_gate._build_sbom(policy, lock, pyproject)
        references = [component["bom-ref"] for component in sbom["components"]]
        self.assertEqual(len(references), len(set(references)))


if __name__ == "__main__":
    unittest.main()
