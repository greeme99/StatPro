"""Approved PostgreSQL connection profiles and Windows-only secret lookup."""

from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import replace
from dataclasses import dataclass
from typing import TYPE_CHECKING

from statpro.domain.data import DatasetSource, DatasetSnapshot, DataType, import_csv_bytes
from statpro.domain.errors import AnalysisInputError
from statpro.domain.identity import input_digest

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class ExternalSqlConfigurationError(ValueError):
    pass


class CredentialUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PostgreSqlProfile:
    profile_id: str
    host: str
    port: int
    database: str
    user: str
    credential_target: str
    allowed_schema: str
    allowed_table: str
    connect_timeout_seconds: int = 10
    statement_timeout_seconds: int = 30
    row_limit: int = 1_000_000

    def __post_init__(self) -> None:
        if not self.host or self.host.casefold() in {"localhost", "127.0.0.1", "::1"}:
            raise ExternalSqlConfigurationError("A non-loopback PostgreSQL host is required.")
        if not 1 <= self.port <= 65535 or self.row_limit < 1:
            raise ExternalSqlConfigurationError("PostgreSQL profile limits are invalid.")
        if not all(value and value.replace("_", "").isalnum() for value in (self.allowed_schema, self.allowed_table)):
            raise ExternalSqlConfigurationError("Allowed schema and table must be simple identifiers.")

    def to_dict(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


class WindowsCredentialManager:
    """Resolves a named Generic Credential without persisting its secret elsewhere."""

    def password(self, target: str) -> str:
        try:
            import win32cred
            credential = win32cred.CredRead(target, win32cred.CRED_TYPE_GENERIC)
            secret = credential["CredentialBlob"].decode("utf-16-le")
        except (ImportError, OSError, KeyError, UnicodeError) as error:
            raise CredentialUnavailableError("Windows Credential Manager secret is unavailable.") from error
        if not secret:
            raise CredentialUnavailableError("Windows Credential Manager secret is empty.")
        return secret


def open_read_only_postgres(profile: PostgreSqlProfile, credentials: WindowsCredentialManager):
    """Open one TLS-verified PostgreSQL session and force read-only operation."""

    import psycopg

    connection = psycopg.connect(
        host=profile.host, port=profile.port, dbname=profile.database, user=profile.user,
        password=credentials.password(profile.credential_target), sslmode="verify-full",
        connect_timeout=profile.connect_timeout_seconds,
    )
    with connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION READ ONLY")
        cursor.execute("SET statement_timeout = %s", (profile.statement_timeout_seconds * 1000,))
    return connection


def import_approved_postgres_table(
    profile: PostgreSqlProfile,
    credentials: WindowsCredentialManager,
    *,
    type_hints: Mapping[str, DataType] | None = None,
    missing_tokens: Sequence[str] = ("",),
) -> DatasetSnapshot:
    """Read one allow-listed PostgreSQL table into the shared worksheet contract."""
    connection = open_read_only_postgres(profile, credentials)
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM "{profile.allowed_schema}"."{profile.allowed_table}" LIMIT %s', (profile.row_limit + 1,))
            headers = [str(column.name) for column in cursor.description or ()]
            if not headers:
                raise AnalysisInputError("external_sql_empty_table", "The approved PostgreSQL table has no columns.", "profile_id")
            rows = cursor.fetchmany(profile.row_limit + 1)
            if len(rows) > profile.row_limit:
                raise AnalysisInputError("dataset_too_large", "The approved PostgreSQL table exceeds its configured row limit.", "profile_id")
    except AnalysisInputError:
        raise
    except Exception as error:
        raise AnalysisInputError("external_sql_read_failed", "The approved PostgreSQL table could not be read.", "profile_id") from error
    finally:
        connection.close()
    source_identity = f"postgresql://{profile.host}:{profile.port}/{profile.database}#{profile.allowed_schema}.{profile.allowed_table}"
    source_digest = hashlib.sha256(repr((headers, rows)).encode("utf-8")).hexdigest()
    missing_token = f"__statpro_postgres_null_{source_digest}__"
    observed_text = {str(value) for row in rows for value in row if value is not None}
    while missing_token in observed_text:
        missing_token += "_"
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(headers)
    for row_index, row in enumerate(rows):
        normalized: list[str] = []
        for column_index, value in enumerate(row):
            if value is None:
                normalized.append(missing_token)
            elif isinstance(value, (bytes, bytearray, memoryview)):
                raise AnalysisInputError("external_sql_binary_not_supported", "Binary PostgreSQL values are not imported.", f"rows[{row_index}][{headers[column_index]}]")
            else:
                normalized.append(str(value))
        writer.writerow(normalized)
    parsed = import_csv_bytes(stream.getvalue().encode("utf-8"), location=source_identity, type_hints=type_hints, missing_tokens=(*missing_tokens, missing_token), error_field="profile_id")
    digest = input_digest({"columns": [column.to_dict() for column in parsed.columns], "format": "postgresql-approved-table", "profile_id": profile.profile_id, "schema": profile.allowed_schema, "table": profile.allowed_table})
    return replace(parsed, dataset_id=f"ds_{digest[:16]}", digest=digest, source=DatasetSource(kind="postgresql", location=source_identity, media_type="application/x-postgresql-table", content_digest=source_digest))
