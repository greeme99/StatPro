"""Command-line launcher for the loopback-only StatPro API."""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from pathlib import Path

_COPILOT_ENV_KEYS = {
    "STATPRO_COPILOT_LLM_ENABLED",
    "GEMINI_API_KEY",
    "STATPRO_COPILOT_GEMINI_SIMPLE_MODEL",
    "STATPRO_COPILOT_GEMINI_COMPLEX_MODEL",
    "STATPRO_COPILOT_OLLAMA_ENABLED",
    "STATPRO_COPILOT_OLLAMA_URL",
    "STATPRO_COPILOT_OLLAMA_WORKFLOW_MODEL",
    "STATPRO_COPILOT_OLLAMA_CODE_MODEL",
    "STATPRO_COPILOT_LOCAL_LLM_ENABLED",
    "STATPRO_COPILOT_LOCAL_LLM_URL",
    "STATPRO_COPILOT_LOCAL_LLM_MODEL",
}


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
    args = parser.parse_args(argv)
    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        parser.error("StatPro API is local-only; host must be a loopback address.")
    try:
        load_copilot_env(args.env_file)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))

    import uvicorn

    from statpro.api.app import create_local_app

    uvicorn.run(
        create_local_app(args.storage, args.approval_identities),
        host=args.host,
        port=args.port,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
