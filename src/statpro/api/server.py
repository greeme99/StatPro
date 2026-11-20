"""Command-line launcher for the loopback-only StatPro API."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path

_COPILOT_ENV_KEYS = {
    "STATPRO_COPILOT_EXAONE_ENABLED",
    "EXAONE_API_KEY",
    "STATPRO_COPILOT_EXAONE_URL",
    "STATPRO_COPILOT_EXAONE_MODEL",
    "STATPRO_COPILOT_EXAONE_SIMPLE_REASONING_EFFORT",
    "STATPRO_COPILOT_EXAONE_COMPLEX_REASONING_EFFORT",
    "STATPRO_COPILOT_EXAONE_TIMEOUT_SECONDS",
    "STATPRO_COPILOT_CODEX_ENABLED",
    "STATPRO_COPILOT_CODEX_MODEL",
}


def load_external_sql_profiles(path: Path | None):
    """Load administrator-approved PostgreSQL profiles without accepting secrets."""
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid external SQL profile file: {path}") from error
    if not isinstance(payload, list):
        raise ValueError("External SQL profile file must contain a JSON array.")
    from statpro.application.external_sql import PostgreSqlProfile
    profiles = {}
    for index, item in enumerate(payload):
        if not isinstance(item, dict) or "password" in item:
            raise ValueError(f"External SQL profile {index} is invalid or contains a forbidden secret.")
        try:
            profile = PostgreSqlProfile(**item)
        except (TypeError, ValueError) as error:
            raise ValueError(f"External SQL profile {index} is invalid.") from error
        if profile.profile_id in profiles:
            raise ValueError(f"External SQL profile ID is duplicated: {profile.profile_id}")
        profiles[profile.profile_id] = profile
    return profiles


def load_copilot_env(path: Path) -> None:
    """Load only Copilot settings from a local env file without overriding the process."""

    if not path.is_file():
        return
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid environment setting at {path}:{line_number}")
        key, value = (part.strip() for part in line.split("=", 1))
        if key not in _COPILOT_ENV_KEYS:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="statpro-api")
    parser.add_argument("--storage", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--approval-identities", type=Path)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--external-sql-profiles", type=Path)
    args = parser.parse_args(argv)
    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        parser.error("StatPro API is local-only; host must be a loopback address.")
    try:
        load_copilot_env(args.env_file)
        external_sql_profiles = load_external_sql_profiles(args.external_sql_profiles)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))

    import uvicorn

    from statpro.api.app import create_local_app

    uvicorn.run(
        create_local_app(args.storage, args.approval_identities, external_sql_profiles=external_sql_profiles),
        host=args.host,
        port=args.port,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
