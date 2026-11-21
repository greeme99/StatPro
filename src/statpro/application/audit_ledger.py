"""Tamper-evident, append-only API audit ledger.

The ledger intentionally stores request digests rather than request bodies, so
quality measurements and credentials do not become duplicated audit data.
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from uuid import uuid4

from statpro.application.documents import (
    DocumentNotFoundError,
    DocumentRepository,
    DocumentStoreError,
)
from statpro.domain.identity import input_digest

AUDIT_EVENTS = "api-audit-events"
AUDIT_HEAD = "api-audit-head"


class AuditLedgerError(DocumentStoreError):
    """The audit stream cannot be written or does not form one valid chain."""


class ApiAuditLedger:
    """Own a hash-chained stream of successful authenticated API operations.

    This provides tamper evidence within the owned document store.  Filesystem
    ACLs and retained/off-host exports remain deployment responsibilities.
    """

    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository

    def append(
        self,
        *,
        actor: str,
        permission: str,
        method: str,
        path: str,
        request_digest: str,
        response_status: int,
        response_etag: str | None,
    ) -> dict[str, Any]:
        try:
            head = self._repository.load(AUDIT_EVENTS, AUDIT_HEAD)
        except DocumentNotFoundError:
            head = None
        sequence = 1 if head is None else int(head.document["sequence"]) + 1
        previous_hash = None if head is None else str(head.document["event_hash"])
        event_id = f"{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}-{uuid4().hex}"
        event = {
            "kind": "statpro.api_audit_event.v1",
            "sequence": sequence,
            "occurred_at": datetime.now(UTC).isoformat(),
            "actor": actor,
            "permission": permission,
            "method": method,
            "path": path,
            "request_digest": request_digest,
            "response_status": response_status,
            "response_etag": response_etag,
            "previous_event_hash": previous_hash,
        }
        event_hash = input_digest(event)
        saved_event = self._repository.save(
            AUDIT_EVENTS, event_id, {**event, "event_hash": event_hash}, expected_version=0
        )
        head_document = {"sequence": sequence, "event_id": event_id, "event_hash": event_hash}
        self._repository.save(
            AUDIT_EVENTS,
            AUDIT_HEAD,
            head_document,
            expected_version=0 if head is None else head.storage_version,
        )
        return saved_event.document

    def verify(self, *, limit: int = 10_000) -> dict[str, Any]:
        """Verify the complete retained chain, including the immutable head claim."""

        try:
            head = self._repository.load(AUDIT_EVENTS, AUDIT_HEAD)
        except DocumentNotFoundError:
            return {"valid": True, "event_count": 0, "head_hash": None}
        events = tuple(
            stored
            for stored in self._repository.list_documents(AUDIT_EVENTS, after=None, limit=limit)
            if stored.key != AUDIT_HEAD
        )
        ordered = sorted(events, key=lambda stored: int(stored.document.get("sequence", -1)))
        previous_hash: str | None = None
        for expected_sequence, stored in enumerate(ordered, 1):
            document = stored.document
            event_hash = document.get("event_hash")
            unsigned = {key: value for key, value in document.items() if key != "event_hash"}
            if (
                document.get("sequence") != expected_sequence
                or document.get("previous_event_hash") != previous_hash
                or not isinstance(event_hash, str)
                or input_digest(unsigned) != event_hash
            ):
                raise AuditLedgerError("API audit ledger integrity verification failed.")
            previous_hash = event_hash
        if (
            head.document.get("sequence") != len(ordered)
            or head.document.get("event_hash") != previous_hash
            or head.document.get("event_id") != ordered[-1].key
        ):
            raise AuditLedgerError("API audit ledger head does not match retained events.")
        return {"valid": True, "event_count": len(ordered), "head_hash": previous_hash}

    def export(self, *, limit: int = 10_000) -> dict[str, Any]:
        """Return a verified, bounded retention artifact for authorized auditors."""

        verification = self.verify(limit=limit)
        events = tuple(
            stored.document
            for stored in self._repository.list_documents(AUDIT_EVENTS, after=None, limit=limit)
            if stored.key != AUDIT_HEAD
        )
        return {
            "report_type": "statpro.api_audit_ledger_export.v1",
            "verification": verification,
            "events": sorted(events, key=lambda event: int(event["sequence"])),
        }


def digest_request_body(body: bytes) -> str:
    """Return a stable request-body digest without retaining sensitive content."""

    return sha256(body).hexdigest()
