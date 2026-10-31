from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.application.approval import (
    ApprovalAuthenticationError,
    ApprovalAuthorizationError,
    LocalApprovalAuthenticator,
    add_identity_file,
    create_approval_identity,
)
from statpro.application.enterprise_identity import (
    EnterpriseApprovalAuthenticator,
    EnterpriseIdentityRecord,
    EntraApprovalConfiguration,
    VerifiedOidcClaims,
    provided_reference_identities,
)


class ApprovalIdentityTests(unittest.TestCase):
    def test_password_reauthentication_returns_the_authorized_identity(self) -> None:
        password = "correct horse battery staple"
        identity = create_approval_identity(
            user_id="quality.approver",
            display_name="Quality Approver",
            password=password,
        )
        authenticator = LocalApprovalAuthenticator((identity,))

        principal = authenticator.authenticate("quality.approver", password)

        self.assertEqual(principal.display_name, "Quality Approver")
        self.assertEqual(principal.role, "fmea_approver")
        with self.assertRaises(ApprovalAuthenticationError):
            authenticator.authenticate("quality.approver", "incorrect password")

    def test_identity_without_approval_role_is_denied(self) -> None:
        identity = create_approval_identity(
            user_id="quality.reviewer",
            display_name="Quality Reviewer",
            password="correct horse battery staple",
            roles=("fmea_reviewer",),
        )
        with self.assertRaises(ApprovalAuthorizationError):
            LocalApprovalAuthenticator((identity,)).authenticate(
                "quality.reviewer", "correct horse battery staple"
            )

    def test_inactive_identity_is_denied_after_reauthentication(self) -> None:
        identity = create_approval_identity(
            user_id="quality.former-approver",
            display_name="Former Approver",
            password="correct horse battery staple",
            active=False,
        )
        with self.assertRaisesRegex(ApprovalAuthorizationError, "inactive"):
            LocalApprovalAuthenticator((identity,)).authenticate(
                "quality.former-approver", "correct horse battery staple"
            )

    def test_configured_independent_approver_rejects_prior_actor(self) -> None:
        password = "correct horse battery staple"
        identity = create_approval_identity(
            user_id="quality.approver",
            display_name="Quality Approver",
            password=password,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "approval-identities.json"
            path.write_text(json.dumps({
                "format": "statpro.approval-identities.v1",
                "identities": [identity],
                "approval_policy": {"require_independent_approver": True},
            }), encoding="utf-8")
            authenticator = LocalApprovalAuthenticator.from_file(path)
            principal = authenticator.authenticate("quality.approver", password)
            with self.assertRaisesRegex(ApprovalAuthorizationError, "Independent approval"):
                authenticator.authorization_context(
                    signer_id=principal.user_id,
                    prior_actors=("quality.engineer", "quality.approver"),
                )

    def test_identity_file_is_atomic_readable_and_contains_no_password(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "approval-identities.json"
            identity = create_approval_identity(
                user_id="quality.approver",
                display_name="Quality Approver",
                password="correct horse battery staple",
            )
            add_identity_file(path, identity)

            content = path.read_text(encoding="utf-8")
            self.assertNotIn("correct horse battery staple", content)
            self.assertEqual(json.loads(content)["format"], "statpro.approval-identities.v1")
            principal = LocalApprovalAuthenticator.from_file(path).authenticate(
                "quality.approver", "correct horse battery staple"
            )
            self.assertEqual(principal.user_id, "quality.approver")
            with self.assertRaises(ValueError):
                add_identity_file(path, identity)


class EnterpriseApprovalIdentityTests(unittest.TestCase):
    tenant_id = "11111111-2222-3333-4444-555555555555"
    client_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    def configuration(self) -> EntraApprovalConfiguration:
        return EntraApprovalConfiguration.for_tenant(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            policy_version="provided-master-2026-11-01",
        )

    def claims(self, **changes: object) -> VerifiedOidcClaims:
        values: dict[str, object] = {
            "tenant_id": self.tenant_id,
            "audience": self.client_id,
            "issuer": f"https://login.microsoftonline.com/{self.tenant_id}/v2.0",
            "subject": "entra-object-qa-001",
            "user_id": "M15082",
            "display_name": "QA Approver",
            "roles": ("ROLE_RND_QA", "ROLE_GENERAL"),
            "authentication_methods": ("pwd", "mfa"),
        }
        values.update(changes)
        return VerifiedOidcClaims(**values)  # type: ignore[arg-type]

    def authenticator(self, claims: VerifiedOidcClaims) -> EnterpriseApprovalAuthenticator:
        return EnterpriseApprovalAuthenticator(
            self.configuration(),
            provided_reference_identities(),
            token_verifier=lambda token: claims if token == "verified" else (_ for _ in ()).throw(ValueError()),
        )

    def test_tenant_configuration_derives_public_metadata_without_secrets(self) -> None:
        configuration = self.configuration()

        self.assertEqual(
            configuration.discovery_url,
            f"https://login.microsoftonline.com/{self.tenant_id}/v2.0/.well-known/openid-configuration",
        )
        self.assertEqual(
            configuration.jwks_url,
            f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys",
        )
        self.assertFalse(hasattr(configuration, "client_secret"))

    def test_verified_qa_role_and_mfa_authorize_fmea_approval(self) -> None:
        claims = self.claims()
        authenticator = self.authenticator(claims)

        principal, verified = authenticator.verify("Bearer verified")
        context = authenticator.authorization_context(
            signer_id=principal.user_id,
            prior_actors=("quality.engineer",),
            claims=verified,
        )

        self.assertEqual(principal.user_id, "M15082")
        self.assertEqual(principal.role, "fmea_approver")
        self.assertEqual(principal.authentication_method, "oidc_signed_token+mfa")
        self.assertEqual(context["effective_roles"], ["ROLE_GENERAL", "ROLE_RND_QA"])
        self.assertEqual(context["policy_version"], "provided-master-2026-11-01")

    def test_role_master_account_state_mfa_and_authority_fail_closed(self) -> None:
        with self.assertRaisesRegex(ApprovalAuthorizationError, "not authorized"):
            self.authenticator(self.claims(user_id="M15024", roles=("ROLE_SALES_B2G",))).verify(
                "Bearer verified"
            )
        inactive = EnterpriseApprovalAuthenticator(
            self.configuration(),
            (EnterpriseIdentityRecord("M15082", ("ROLE_RND_QA",), active=False),),
            token_verifier=lambda _token: self.claims(roles=("ROLE_RND_QA",)),
        )
        with self.assertRaisesRegex(ApprovalAuthorizationError, "inactive"):
            inactive.verify("Bearer verified")
        with self.assertRaisesRegex(ApprovalAuthorizationError, "requires MFA"):
            self.authenticator(self.claims(authentication_methods=("pwd",))).verify(
                "Bearer verified"
            )
        with self.assertRaises(ApprovalAuthenticationError):
            self.authenticator(self.claims(audience="wrong-client")).verify("Bearer verified")

    def test_enterprise_independent_approval_rejects_prior_actor(self) -> None:
        claims = self.claims()
        authenticator = self.authenticator(claims)
        principal, verified = authenticator.verify("Bearer verified")
        with self.assertRaisesRegex(ApprovalAuthorizationError, "Independent approval"):
            authenticator.authorization_context(
                signer_id=principal.user_id,
                prior_actors=("M15082",),
                claims=verified,
            )


if __name__ == "__main__":
    unittest.main()
