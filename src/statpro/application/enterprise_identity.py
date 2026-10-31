"""Enterprise IdP authorization boundary for regulated FMEA approvals.

The adapter consumes claims only after an injected verifier has validated the
OIDC token signature, issuer, audience, and lifetime.  It never parses or
trusts an unverified JWT payload itself.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from statpro.application.approval import (
    ApprovalAuthenticationError,
    ApprovalAuthorizationError,
    ApprovalPolicy,
    ApprovalPrincipal,
)

FMEA_APPROVAL_PERMISSION = "fmea.approve"


@dataclass(frozen=True, slots=True)
class VerifiedOidcClaims:
    """Claims returned by a cryptographic OIDC verifier, never raw JWT data."""

    tenant_id: str
    audience: str
    issuer: str
    subject: str
    user_id: str
    display_name: str
    roles: tuple[str, ...]
    authentication_methods: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EnterpriseIdentityRecord:
    user_id: str
    assigned_roles: tuple[str, ...]
    active: bool = True


@dataclass(frozen=True, slots=True)
class EntraApprovalConfiguration:
    """Tenant-specific values that are safe to persist.

    Client secrets and signing keys are deliberately absent.  The runtime
    verifier owns secret retrieval and key rotation.
    """

    tenant_id: str
    client_id: str
    discovery_url: str
    jwks_url: str
    issuer: str
    policy_version: str
    required_authentication_method: str = "mfa"
    user_id_claim: str = "employee_id"
    roles_claim: str = "roles"

    @classmethod
    def for_tenant(
        cls, *, tenant_id: str, client_id: str, policy_version: str
    ) -> EntraApprovalConfiguration:
        authority = f"https://login.microsoftonline.com/{tenant_id}/v2.0"
        return cls(
            tenant_id=tenant_id,
            client_id=client_id,
            discovery_url=f"{authority}/.well-known/openid-configuration",
            jwks_url=f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys",
            issuer=authority,
            policy_version=policy_version,
        )


class EntraJwtVerifier:
    """Cryptographically verify tenant-specific Entra access tokens.

    PyJWT is imported lazily so the statistical core keeps its dependency-free
    default installation.  Install the ``identity`` extra on an IdP-enabled
    host.  Client secrets are not required for public-key token validation.
    """

    def __init__(self, configuration: EntraApprovalConfiguration) -> None:
        try:
            import jwt
        except ImportError as error:
            raise RuntimeError(
                "Install StatPro with the 'identity' extra to verify Entra tokens."
            ) from error
        self._jwt = jwt
        self._configuration = configuration
        self._keys = jwt.PyJWKClient(configuration.jwks_url, cache_keys=True)

    def __call__(self, token: str) -> VerifiedOidcClaims:
        configuration = self._configuration
        signing_key = self._keys.get_signing_key_from_jwt(token)
        claims = self._jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=configuration.client_id,
            issuer=configuration.issuer,
            options={"require": ["exp", "iat", "nbf", "iss", "aud", "sub", "tid"]},
        )
        roles = claims.get(configuration.roles_claim, ())
        methods = claims.get("amr", ())
        if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
            raise ValueError("The verified token roles claim is invalid.")
        if not isinstance(methods, list) or not all(isinstance(item, str) for item in methods):
            raise ValueError("The verified token authentication methods claim is invalid.")
        user_id = claims.get(configuration.user_id_claim)
        display_name = claims.get("name")
        if not isinstance(user_id, str) or not isinstance(display_name, str):
            raise TypeError("The verified token is missing mapped user identity claims.")
        return VerifiedOidcClaims(
            tenant_id=str(claims["tid"]),
            audience=configuration.client_id,
            issuer=str(claims["iss"]),
            subject=str(claims["sub"]),
            user_id=user_id,
            display_name=display_name,
            roles=tuple(roles),
            authentication_methods=tuple(methods),
        )


ROLE_PERMISSIONS: Mapping[str, frozenset[str]] = {
    "ROLE_SYS_ADMIN": frozenset({
        "identity.configure", "identity.audit", "fmea.view", "fmea.edit",
        "fmea.review", FMEA_APPROVAL_PERMISSION,
    }),
    "ROLE_RND_QA": frozenset({
        "fmea.view", "fmea.edit", "fmea.review", FMEA_APPROVAL_PERMISSION,
        "quality.evidence.link",
    }),
    "ROLE_SALES_B2G": frozenset({"sales.b2g.view"}),
    "ROLE_SALES_B2B": frozenset({"sales.b2b.view"}),
    "ROLE_PROD_LOGI": frozenset({"production.view", "logistics.view"}),
    "ROLE_GENERAL": frozenset({"common.view"}),
}

# Role assignments transcribed from the user-provided authority master.  Email
# addresses and the example client secret are intentionally not duplicated in
# source control.  Runtime provisioning may replace these records atomically.
PROVIDED_ROLE_ASSIGNMENTS: Mapping[str, tuple[str, ...]] = {
    "M15001": ("ROLE_SYS_ADMIN",),
    "M15024": ("ROLE_SALES_B2G", "ROLE_GENERAL"),
    "M15045": ("ROLE_SALES_B2B", "ROLE_GENERAL"),
    "M15082": ("ROLE_RND_QA", "ROLE_GENERAL"),
    "M15110": ("ROLE_PROD_LOGI", "ROLE_GENERAL"),
}


def provided_reference_identities() -> tuple[EnterpriseIdentityRecord, ...]:
    """Return the non-secret account/role master supplied for this project."""

    return tuple(
        EnterpriseIdentityRecord(user_id=user_id, assigned_roles=roles)
        for user_id, roles in PROVIDED_ROLE_ASSIGNMENTS.items()
    )


class EnterpriseApprovalAuthenticator:
    """Resolve an FMEA approver from verified Entra claims and local policy."""

    def __init__(
        self,
        configuration: EntraApprovalConfiguration,
        identities: tuple[EnterpriseIdentityRecord, ...],
        *,
        token_verifier: Callable[[str], VerifiedOidcClaims],
        policy: ApprovalPolicy | None = None,
    ) -> None:
        self.configuration = configuration
        self.policy = policy or ApprovalPolicy(require_independent_approver=True)
        self._token_verifier = token_verifier
        self._identities: dict[str, EnterpriseIdentityRecord] = {}
        for identity in identities:
            if not identity.user_id or identity.user_id in self._identities:
                raise ValueError("Enterprise identity user IDs must be present and unique.")
            unknown = set(identity.assigned_roles).difference(ROLE_PERMISSIONS)
            if unknown:
                raise ValueError(f"Unknown enterprise roles: {sorted(unknown)!r}.")
            self._identities[identity.user_id] = identity

    def authenticate_bearer(self, authorization: str | None) -> ApprovalPrincipal:
        if not authorization or not authorization.startswith("Bearer "):
            raise ApprovalAuthenticationError("A verified enterprise bearer token is required.")
        token = authorization.removeprefix("Bearer ").strip()
        if not token:
            raise ApprovalAuthenticationError("A verified enterprise bearer token is required.")
        try:
            claims = self._token_verifier(token)
        except Exception as error:
            raise ApprovalAuthenticationError("Enterprise token verification failed.") from error
        return self._principal_from_claims(claims)

    def _principal_from_claims(self, claims: VerifiedOidcClaims) -> ApprovalPrincipal:
        self._validate_authority(claims)
        identity = self._identities.get(claims.user_id)
        if identity is None:
            raise ApprovalAuthorizationError("Identity is not present in the enterprise account master.")
        if not identity.active:
            raise ApprovalAuthorizationError("Enterprise identity is inactive.")
        effective_roles = set(claims.roles).intersection(identity.assigned_roles)
        permissions = set().union(*(ROLE_PERMISSIONS[role] for role in effective_roles))
        if FMEA_APPROVAL_PERMISSION not in permissions:
            raise ApprovalAuthorizationError("Identity is not authorized to approve FMEA studies.")
        if (
            self.configuration.required_authentication_method
            and self.configuration.required_authentication_method
            not in claims.authentication_methods
        ):
            raise ApprovalAuthorizationError("The enterprise approval policy requires MFA.")
        return ApprovalPrincipal(
            user_id=claims.user_id,
            display_name=claims.display_name,
            role="fmea_approver",
            authority=f"microsoft-entra:{claims.tenant_id}",
            authentication_method="oidc_signed_token+mfa",
        )

    def authorization_context(
        self, *, signer_id: str, prior_actors: tuple[str, ...], claims: VerifiedOidcClaims
    ) -> dict[str, Any]:
        matches = tuple(actor for actor in prior_actors if actor == signer_id)
        if self.policy.require_independent_approver and matches:
            raise ApprovalAuthorizationError(
                "Independent approval is required: the enterprise identity appears in prior FMEA audit actors."
            )
        identity = self._identities[signer_id]
        effective_roles = sorted(set(claims.roles).intersection(identity.assigned_roles))
        return {
            "policy": self.policy.to_dict(),
            "policy_version": self.configuration.policy_version,
            "identity_provider": "Microsoft Entra ID",
            "tenant_id": claims.tenant_id,
            "subject": claims.subject,
            "effective_roles": effective_roles,
            "prior_actor_match_count": len(matches),
            "prior_actor_identity_match": bool(matches),
            "actor_identity_limit": (
                "Approval identity is IdP-attested; prior historical actor fields remain self-reported "
                "unless they were created through the same enterprise identity boundary."
            ),
        }

    def verify(self, authorization: str | None) -> tuple[ApprovalPrincipal, VerifiedOidcClaims]:
        if not authorization or not authorization.startswith("Bearer "):
            raise ApprovalAuthenticationError("A verified enterprise bearer token is required.")
        token = authorization.removeprefix("Bearer ").strip()
        try:
            claims = self._token_verifier(token)
        except Exception as error:
            raise ApprovalAuthenticationError("Enterprise token verification failed.") from error
        principal = self._principal_from_claims(claims)
        return principal, claims

    def _validate_authority(self, claims: VerifiedOidcClaims) -> None:
        expected = self.configuration
        if (
            claims.tenant_id != expected.tenant_id
            or claims.audience != expected.client_id
            or claims.issuer != expected.issuer
        ):
            raise ApprovalAuthenticationError("Enterprise token authority does not match configuration.")
        if not claims.subject or not claims.user_id or not claims.display_name:
            raise ApprovalAuthenticationError("Enterprise token is missing required identity claims.")
