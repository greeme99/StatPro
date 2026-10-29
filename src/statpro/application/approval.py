"""Local approval identities and password reauthentication."""

from __future__ import annotations

import base64
import getpass
import hashlib
import hmac
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from statpro.application.documents import validate_document_identifier

_FORMAT = "statpro.approval-identities.v1"
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_ROLE = "fmea_approver"
_POLICY_KEY = "approval_policy"


class ApprovalAuthenticationError(RuntimeError):
    """Credentials did not establish a known local identity."""


class ApprovalAuthorizationError(RuntimeError):
    """The authenticated identity lacks the required authority."""


class ApprovalConfigurationError(RuntimeError):
    """Approval authentication has not been configured."""


@dataclass(frozen=True, slots=True)
class ApprovalPolicy:
    """Organization-selected local approval controls.

    This deliberately contains no IdP protocol details.  An organization may
    enable independent approval in its local identity file, while a future IdP
    adapter can supply the same policy decision from its own authority.
    """

    require_independent_approver: bool = False

    def to_dict(self) -> dict[str, bool]:
        return {"require_independent_approver": self.require_independent_approver}


@dataclass(frozen=True, slots=True)
class ApprovalPrincipal:
    user_id: str
    display_name: str
    role: str
    authority: str = "statpro-local"
    authentication_method: str = "password"


def create_approval_identity(
    *,
    user_id: str,
    display_name: str,
    password: str,
    roles: tuple[str, ...] = (_ROLE,),
    active: bool = True,
) -> dict[str, object]:
    """Create a serializable scrypt verifier without retaining the password."""

    user_id = validate_document_identifier(user_id, "user_id")
    display_name = display_name.strip()
    if not display_name:
        raise ValueError("display_name is required.")
    if len(password) < 12:
        raise ValueError("password must contain at least 12 characters.")
    if not roles:
        raise ValueError("at least one role is required.")
    if not isinstance(active, bool):
        raise ValueError("active must be a boolean.")
    roles = tuple(validate_document_identifier(role, "role") for role in roles)
    salt = os.urandom(16)
    verifier = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P
    )
    return {
        "user_id": user_id,
        "display_name": display_name,
        "roles": list(dict.fromkeys(roles)),
        "active": active,
        "password": {
            "algorithm": "scrypt",
            "salt_base64": base64.b64encode(salt).decode("ascii"),
            "verifier_base64": base64.b64encode(verifier).decode("ascii"),
            "n": _SCRYPT_N,
            "r": _SCRYPT_R,
            "p": _SCRYPT_P,
        },
    }


class LocalApprovalAuthenticator:
    """Read-only local identity verifier used only at approval time."""

    def __init__(
        self,
        identities: tuple[dict[str, object], ...],
        *,
        policy: ApprovalPolicy | None = None,
    ) -> None:
        self._identities: dict[str, dict[str, object]] = {}
        self.policy = policy or ApprovalPolicy()
        for identity in identities:
            user_id = validate_document_identifier(str(identity.get("user_id", "")), "user_id")
            if user_id in self._identities:
                raise ValueError("Approval identity user IDs must be unique.")
            if not isinstance(identity.get("display_name"), str) or not identity["display_name"].strip():
                raise ValueError("Approval identity display_name is required.")
            active = identity.get("active", True)
            if not isinstance(active, bool):
                raise ValueError("Approval identity active must be a boolean.")
            self._identities[user_id] = identity

    @classmethod
    def from_file(cls, path: Path) -> LocalApprovalAuthenticator:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Cannot read approval identity file {path}.") from error
        if (
            not isinstance(payload, dict)
            or payload.get("format") != _FORMAT
            or not isinstance(payload.get("identities"), list)
        ):
            raise ValueError("Approval identity file has an invalid format.")
        identities = tuple(payload["identities"])
        if not all(isinstance(identity, dict) for identity in identities):
            raise ValueError("Approval identities must be objects.")
        raw_policy = payload.get(_POLICY_KEY, {})
        if not isinstance(raw_policy, dict):
            raise ValueError("Approval policy must be an object.")
        independent = raw_policy.get("require_independent_approver", False)
        if not isinstance(independent, bool):
            raise ValueError("Approval policy require_independent_approver must be a boolean.")
        return cls(identities, policy=ApprovalPolicy(independent))

    def authenticate(self, user_id: str, password: str) -> ApprovalPrincipal:
        identity = self._identities.get(user_id)
        if identity is None:
            hashlib.scrypt(
                password.encode("utf-8"), salt=b"\0" * 16,
                n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P,
            )
            raise ApprovalAuthenticationError("Approval credentials are invalid.")
        try:
            credential = identity["password"]
            assert isinstance(credential, dict)
            if credential["algorithm"] != "scrypt":
                raise ValueError
            n, r, p = int(credential["n"]), int(credential["r"]), int(credential["p"])
            if (n, r, p) != (_SCRYPT_N, _SCRYPT_R, _SCRYPT_P):
                raise ValueError
            salt = base64.b64decode(str(credential["salt_base64"]), validate=True)
            expected = base64.b64decode(str(credential["verifier_base64"]), validate=True)
            if len(salt) != 16 or len(expected) != 64:
                raise ValueError
            actual = hashlib.scrypt(
                password.encode("utf-8"),
                salt=salt, n=n, r=r, p=p,
            )
            roles = identity["roles"]
            if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
                raise ValueError
        except (AssertionError, KeyError, TypeError, ValueError) as error:
            raise ApprovalAuthenticationError("Approval identity record is invalid.") from error
        if not hmac.compare_digest(actual, expected):
            raise ApprovalAuthenticationError("Approval credentials are invalid.")
        if _ROLE not in roles:
            raise ApprovalAuthorizationError("Identity is not authorized to approve FMEA studies.")
        if not identity.get("active", True):
            raise ApprovalAuthorizationError("Approval identity is inactive.")
        return ApprovalPrincipal(
            user_id=user_id,
            display_name=str(identity["display_name"]),
            role=_ROLE,
        )

    def authorization_context(
        self, *, signer_id: str, prior_actors: tuple[str, ...]
    ) -> dict[str, object]:
        """Return an auditable policy decision without treating actor text as IdP proof."""

        matching_events = tuple(actor for actor in prior_actors if actor == signer_id)
        if self.policy.require_independent_approver and matching_events:
            raise ApprovalAuthorizationError(
                "Independent approval is required: the approval identity appears in prior FMEA audit actors."
            )
        return {
            "policy": self.policy.to_dict(),
            "prior_actor_match_count": len(matching_events),
            "prior_actor_identity_match": bool(matching_events),
            "actor_identity_limit": "Prior FMEA actor fields are self-reported unless an external identity provider attests them.",
        }


def add_identity_file(path: Path, identity: dict[str, object]) -> None:
    """Add one identity through atomic replacement; existing IDs are never overwritten."""

    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("format") != _FORMAT or not isinstance(payload.get("identities"), list):
            raise ValueError("Approval identity file has an invalid format.")
    else:
        payload = {"format": _FORMAT, "identities": []}
    identities = payload["identities"]
    assert isinstance(identities, list)
    if any(item.get("user_id") == identity["user_id"] for item in identities):
        raise ValueError("Approval identity already exists.")
    identities.append(identity)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="statpro-approval-user")
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--display-name", required=True)
    args = parser.parse_args()
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Confirm password: "):
        parser.error("Passwords do not match.")
    add_identity_file(
        args.file,
        create_approval_identity(
            user_id=args.user_id, display_name=args.display_name, password=password
        ),
    )
    print(f"Added approval identity {args.user_id!r} to {args.file}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
