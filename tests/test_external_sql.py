from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, "src")

from statpro.application.external_sql import (
    CredentialUnavailableError,
    PostgreSqlProfile,
    WindowsCredentialManager,
    open_read_only_postgres,
    import_approved_postgres_table,
)


class ExternalSqlContractTests(unittest.TestCase):
    def profile(self) -> PostgreSqlProfile:
        return PostgreSqlProfile(
            profile_id="production", host="db.example.test", port=5432,
            database="quality", user="reader", credential_target="StatPro/production",
            allowed_schema="public", allowed_table="measurements",
        )

    def test_public_profile_omits_connection_and_credential_metadata(self) -> None:
        public = self.profile().to_public_dict()

        self.assertEqual(public["profile_id"], "production")
        self.assertEqual(public["allowed_table"], "measurements")
        self.assertNotIn("host", public)
        self.assertNotIn("user", public)
        self.assertNotIn("database", public)
        self.assertNotIn("credential_target", public)

    def test_profile_persists_a_credential_reference_not_a_secret(self) -> None:
        profile = self.profile()
        self.assertEqual(profile.to_dict()["credential_target"], "StatPro/production")
        self.assertNotIn("password", profile.to_dict())

    def test_windows_credential_failure_is_fail_closed(self) -> None:
        with patch.dict(sys.modules, {"win32cred": None}):
            with self.assertRaises(CredentialUnavailableError):
                WindowsCredentialManager().password("StatPro/missing")

    def test_connection_requires_tls_read_only_and_timeout(self) -> None:
        executed: list[tuple[str, tuple[object, ...] | None]] = []
        class Cursor:
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def execute(self, sql, params=None): executed.append((sql, params))
        class Connection:
            def cursor(self): return Cursor()
        connect = unittest.mock.Mock(return_value=Connection())
        credentials = SimpleNamespace(password=lambda _: "secret")
        with patch.dict(sys.modules, {"psycopg": SimpleNamespace(connect=connect)}):
            open_read_only_postgres(self.profile(), credentials)
        self.assertEqual(connect.call_args.kwargs["sslmode"], "verify-full")
        self.assertEqual(executed, [("SET TRANSACTION READ ONLY", None), ("SET statement_timeout = %s", (30000,))])

    def test_imports_only_the_approved_table_with_the_configured_row_limit(self) -> None:
        executed: list[tuple[str, tuple[object, ...] | None]] = []
        class Cursor:
            description = [SimpleNamespace(name="value"), SimpleNamespace(name="part")]
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def execute(self, sql, params=None): executed.append((sql, params))
            def fetchmany(self, count): self.count = count; return [(10.5, "A"), (None, "B")]
        class Connection:
            def __init__(self): self.cursor_value = Cursor(); self.closed = False
            def cursor(self): return self.cursor_value
            def close(self): self.closed = True
        connection = Connection()
        with patch("statpro.application.external_sql.open_read_only_postgres", return_value=connection):
            dataset = import_approved_postgres_table(self.profile(), SimpleNamespace())
        self.assertEqual(dataset.source.kind, "postgresql")
        self.assertEqual(dataset.columns[0].values, (10.5, None))
        self.assertIn(('SELECT * FROM "public"."measurements" LIMIT %s', (1_000_001,)), executed)
        self.assertTrue(connection.closed)
