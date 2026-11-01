from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "compliance" / "oss-policy.json"
PACKAGE_PATH = ROOT / "web" / "package.json"
LOCK_PATH = ROOT / "web" / "package-lock.json"
PYPROJECT_PATH = ROOT / "pyproject.toml"
SBOM_PATH = ROOT / "compliance" / "statpro-sbom.cdx.json"


class GateError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalise_python_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _requirement_name(requirement: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9_.-]+)", requirement)
    if match is None:
        raise GateError(f"Python requirement name cannot be parsed: {requirement}")
    return _normalise_python_name(match.group(1))


def _license_ids(expression: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[A-Za-z0-9.+-]+", expression)
        if token not in {"AND", "OR", "WITH"}
    }


def _validate_npm_boundaries(policy: dict[str, Any], source_root: Path | None = None) -> None:
    product_source = source_root or ROOT / "web" / "src"
    for name, decision in policy["npm_direct_dependencies"].items():
        if decision.get("boundary") != "benchmark-only":
            continue
        import_pattern = re.compile(
            rf"(?:from\s+|import\s*\()?['\"]{re.escape(name)}(?:/|['\"])",
        )
        violations = []
        for path in product_source.rglob("*"):
            if path.suffix not in {".js", ".jsx", ".ts", ".tsx"}:
                continue
            if import_pattern.search(path.read_text(encoding="utf-8")):
                violations.append(path.relative_to(product_source).as_posix())
        if violations:
            raise GateError(
                f"Benchmark-only npm dependency imported by product source: {name} "
                f"({', '.join(sorted(violations))})"
            )


def _validate_policy(
    policy: dict[str, Any], package: dict[str, Any], lock: dict[str, Any], pyproject: dict[str, Any]
) -> None:
    allowed = set(policy["allowed_spdx_licenses"])
    direct_npm = set(package.get("dependencies", {})) | set(package.get("devDependencies", {}))
    registered_npm = set(policy["npm_direct_dependencies"])
    if direct_npm != registered_npm:
        missing = sorted(direct_npm - registered_npm)
        stale = sorted(registered_npm - direct_npm)
        raise GateError(f"npm direct dependency registry mismatch; missing={missing}, stale={stale}")
    _validate_npm_boundaries(policy)

    lock_root = lock["packages"][""]
    for section in ("dependencies", "devDependencies"):
        if package.get(section, {}) != lock_root.get(section, {}):
            raise GateError(f"web/package.json and package-lock.json disagree in {section}")

    for package_path, item in lock["packages"].items():
        if not package_path or "version" not in item:
            continue
        license_expression = item.get("license")
        if not license_expression:
            raise GateError(f"Locked package has no license declaration: {package_path}")
        unapproved = _license_ids(license_expression) - allowed
        if unapproved:
            raise GateError(
                f"Locked package uses an unapproved license: {package_path} "
                f"({license_expression}; unapproved={sorted(unapproved)})"
            )

    declared_python = {
        _requirement_name(requirement)
        for requirements in pyproject["project"].get("optional-dependencies", {}).values()
        for requirement in requirements
    }
    registered_python = set(policy["python_direct_dependencies"])
    if declared_python != registered_python:
        missing = sorted(declared_python - registered_python)
        stale = sorted(registered_python - declared_python)
        raise GateError(f"Python dependency registry mismatch; missing={missing}, stale={stale}")
    for name, decision in policy["python_direct_dependencies"].items():
        unapproved = _license_ids(decision["declared_license"]) - allowed
        if unapproved:
            raise GateError(f"Python dependency {name} has unapproved license IDs: {sorted(unapproved)}")


def _npm_name(package_path: str) -> str:
    return package_path.rsplit("node_modules/", maxsplit=1)[-1]


def _build_sbom(
    policy: dict[str, Any], lock: dict[str, Any], pyproject: dict[str, Any]
) -> dict[str, Any]:
    lock_digest = hashlib.sha256(LOCK_PATH.read_bytes()).hexdigest()
    npm_components: dict[str, dict[str, Any]] = {}
    for package_path, item in lock["packages"].items():
        if not package_path or "version" not in item:
            continue
        name = _npm_name(package_path)
        version = item["version"]
        purl = f"pkg:npm/{name}@{version}"
        component = npm_components.setdefault(
            purl,
            {
                "type": "library",
                "bom-ref": purl,
                "name": name,
                "version": version,
                "scope": "optional",
                "licenses": [{"expression": item["license"]}],
                "purl": purl,
            },
        )
        if not item.get("dev"):
            component["scope"] = "required"

    components = list(npm_components.values())

    optional_dependencies = pyproject["project"].get("optional-dependencies", {})
    python_requirements: dict[str, list[str]] = {}
    for extra, requirements in optional_dependencies.items():
        for requirement in requirements:
            python_requirements.setdefault(_requirement_name(requirement), []).append(extra)
    for name, decision in policy["python_direct_dependencies"].items():
        components.append(
            {
                "type": "library",
                "bom-ref": f"pkg:pypi/{name}?declared=true",
                "name": name,
                "scope": "optional",
                "licenses": [{"expression": decision["declared_license"]}],
                "properties": [
                    {"name": "statpro:resolution", "value": "declared-not-locked"},
                    {"name": "statpro:extras", "value": ",".join(sorted(python_requirements[name]))},
                ],
            }
        )

    components.sort(key=lambda item: (item["bom-ref"], item.get("version", "")))
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{lock_digest[:8]}-{lock_digest[8:12]}-5{lock_digest[13:16]}-a{lock_digest[17:20]}-{lock_digest[20:32]}",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "bom-ref": "statpro",
                "name": pyproject["project"]["name"],
                "version": pyproject["project"]["version"],
            },
            "properties": [
                {"name": "statpro:npm-lock-sha256", "value": lock_digest},
                {"name": "statpro:python-resolution", "value": "requirements-declared-not-locked"},
            ],
        },
        "components": components,
    }


def _serialized_sbom() -> str:
    policy = _load_json(POLICY_PATH)
    package = _load_json(PACKAGE_PATH)
    lock = _load_json(LOCK_PATH)
    with PYPROJECT_PATH.open("rb") as stream:
        pyproject = tomllib.load(stream)
    _validate_policy(policy, package, lock, pyproject)
    return json.dumps(_build_sbom(policy, lock, pyproject), ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate StatPro OSS policy and deterministic SBOM")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Fail unless policy and committed SBOM are current")
    mode.add_argument("--write", action="store_true", help="Validate policy and regenerate the committed SBOM")
    args = parser.parse_args(argv)
    try:
        expected = _serialized_sbom()
        if args.write:
            SBOM_PATH.write_text(expected, encoding="utf-8", newline="\n")
            print(f"Wrote {SBOM_PATH.relative_to(ROOT)}")
            return 0
        if not SBOM_PATH.exists() or SBOM_PATH.read_text(encoding="utf-8") != expected:
            raise GateError("Committed SBOM is missing or stale; run: python tools/oss_gate.py --write")
    except (GateError, KeyError, json.JSONDecodeError) as error:
        print(f"OSS gate failed: {error}", file=sys.stderr)
        return 1
    print("OSS gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
