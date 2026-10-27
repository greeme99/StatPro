"""Command-line launcher for the loopback-only StatPro API."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="statpro-api")
    parser.add_argument("--storage", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--approval-identities", type=Path)
    args = parser.parse_args(argv)
    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        parser.error("StatPro API is local-only; host must be a loopback address.")

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
