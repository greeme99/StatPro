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


if __name__ == "__main__":
    unittest.main()
