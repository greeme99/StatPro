"""Command-line launcher for the loopback-only StatPro API."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import replace
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


def load_enterprise_api_authenticator(path: Path | None):
    """Load a non-secret Entra account master for the common API boundary."""

    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid enterprise identity file: {path}") from error
    if not isinstance(payload, dict) or payload.get("format") != "statpro.enterprise-api-identities.v1":
        raise ValueError("Enterprise identity file has an invalid format.")
    if any(key in payload for key in ("password", "client_secret", "private_key")):
        raise ValueError("Enterprise identity file must not contain secrets.")
    configuration = payload.get("configuration")
    identities = payload.get("identities")
    if not isinstance(configuration, dict) or not isinstance(identities, list):
        raise ValueError("Enterprise identity file requires configuration and identities.")
    allowed_configuration = {
        "tenant_id", "client_id", "policy_version", "required_authentication_method",
        "user_id_claim", "roles_claim",
    }
    if set(configuration).difference(allowed_configuration):
        raise ValueError("Enterprise identity configuration contains unsupported fields.")
    required = ("tenant_id", "client_id", "policy_version")
    if not all(isinstance(configuration.get(key), str) and configuration[key] for key in required):
        raise ValueError("Enterprise identity configuration is incomplete.")
    from statpro.application.enterprise_identity import (
        EntraApprovalConfiguration,
        EntraJwtVerifier,
        EnterpriseApprovalAuthenticator,
        EnterpriseIdentityRecord,
    )

    configured = EntraApprovalConfiguration.for_tenant(
        tenant_id=configuration["tenant_id"],
        client_id=configuration["client_id"],
        policy_version=configuration["policy_version"],
    )
    for name in ("required_authentication_method", "user_id_claim", "roles_claim"):
        value = configuration.get(name)
        if value is not None:
            if not isinstance(value, str) or not value:
                raise ValueError(f"Enterprise identity configuration {name} is invalid.")
            configured = replace(configured, **{name: value})
    records: list[EnterpriseIdentityRecord] = []
    for item in identities:
        if not isinstance(item, dict) or set(item).difference({"user_id", "assigned_roles", "active"}):
            raise ValueError("Enterprise identity record is invalid.")
        user_id, roles = item.get("user_id"), item.get("assigned_roles")
        active = item.get("active", True)
        if not isinstance(user_id, str) or not user_id or not isinstance(roles, list):
            raise ValueError("Enterprise identity record is invalid.")
        if not all(isinstance(role, str) and role for role in roles) or not isinstance(active, bool):
            raise ValueError("Enterprise identity record is invalid.")
        records.append(EnterpriseIdentityRecord(user_id, tuple(roles), active))
    return EnterpriseApprovalAuthenticator(
        configured, tuple(records), token_verifier=EntraJwtVerifier(configured)
    )


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


def external_copilot_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """Identify enabled providers that can transmit workspace context off-host."""

    source = os.environ if environ is None else environ
    return any(
        source.get(name, "").strip().casefold() in {"1", "true", "yes", "on"}
        for name in ("STATPRO_COPILOT_EXAONE_ENABLED", "STATPRO_COPILOT_CODEX_ENABLED")
    )


def is_network_storage_path(path: Path) -> bool:
    """Reject UNC roots; mapped drives still require the deployment ACL review."""

    normalized = str(path).replace("/", "\\")
    return normalized.startswith("\\\\")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="statpro-api")
    parser.add_argument("--storage", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--approval-identities", type=Path)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--external-sql-profiles", type=Path)
    parser.add_argument("--enterprise-identities", type=Path)
    parser.add_argument("--require-enterprise-auth", action="store_true")
    parser.add_argument("--allow-external-copilot", action="store_true")
    parser.add_argument("--allow-network-storage", action="store_true")
    args = parser.parse_args(argv)
    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        parser.error("StatPro API is local-only; host must be a loopback address.")
    if args.require_enterprise_auth and args.enterprise_identities is None:
        parser.error("--require-enterprise-auth requires --enterprise-identities.")
    if (
        args.require_enterprise_auth
        and is_network_storage_path(args.storage)
        and not args.allow_network_storage
    ):
        parser.error(
            "Enterprise-authenticated deployments reject UNC storage; use a local protected "
            "volume or explicitly acknowledge --allow-network-storage."
        )
    try:
        load_copilot_env(args.env_file)
        if (
            args.require_enterprise_auth
            and external_copilot_enabled()
            and not args.allow_external_copilot
        ):
            parser.error(
                "Enterprise-authenticated deployments require --allow-external-copilot "
                "before an external Copilot provider can receive workspace context."
            )
        external_sql_profiles = load_external_sql_profiles(args.external_sql_profiles)
        enterprise_api_authenticator = load_enterprise_api_authenticator(args.enterprise_identities)
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        parser.error(str(error))

    import uvicorn

    from statpro.api.app import create_local_app
    from statpro.application.documents import DocumentStoreError, StorageWriterLock

    storage_lock = None
    if args.require_enterprise_auth:
        try:
            storage_lock = StorageWriterLock.acquire(args.storage)
        except DocumentStoreError as error:
            parser.error(str(error))
    try:
        uvicorn.run(
            create_local_app(
                args.storage,
                args.approval_identities,
                external_sql_profiles=external_sql_profiles,
                enterprise_api_authenticator=enterprise_api_authenticator,
            ),
            host=args.host,
            port=args.port,
        )
    finally:
        if storage_lock is not None:
            storage_lock.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
