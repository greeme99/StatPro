"""Bounded document persistence interface and local adapters."""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from statpro.domain.identity import input_digest

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_FORMAT = "statpro.document.v1"


class DocumentStoreError(RuntimeError):
    pass


class InvalidDocumentKeyError(DocumentStoreError):
    pass


class DocumentNotFoundError(DocumentStoreError):
    pass


class DocumentConflictError(DocumentStoreError):
    pass


class DocumentCorruptionError(DocumentStoreError):
    pass


@dataclass(frozen=True, slots=True)
class StoredDocument:
    collection: str
    key: str
    storage_version: int
    etag: str
    document: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "collection": self.collection,
            "key": self.key,
            "storage_version": self.storage_version,
            "etag": self.etag,
            "document": _json_clone(self.document),
        }


class DocumentRepository(Protocol):
    def load(self, collection: str, key: str) -> StoredDocument: ...

    def save(
        self,
        collection: str,
        key: str,
        document: dict[str, Any],
        *,
        expected_version: int,
    ) -> StoredDocument: ...

    def list_documents(
        self, collection: str, *, after: str | None, limit: int
    ) -> tuple[StoredDocument, ...]: ...


def validate_document_identifier(value: str, field: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise InvalidDocumentKeyError(
            f"{field} must start with an alphanumeric character and contain only "
            "letters, numbers, '.', '_', or '-'."
        )
    return value


def _json_clone(document: dict[str, Any]) -> dict[str, Any]:
    try:
        encoded = json.dumps(
            document, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        decoded = json.loads(encoded)
    except (TypeError, ValueError) as error:
        raise DocumentStoreError("Document must contain finite JSON values only.") from error
    if not isinstance(decoded, dict):
        raise DocumentStoreError("Document root must be an object.")
    return decoded


def _stored_document(
    collection: str, key: str, storage_version: int, document: dict[str, Any]
) -> StoredDocument:
    normalized = _json_clone(document)
    return StoredDocument(
        collection=collection,
        key=key,
        storage_version=storage_version,
        etag=input_digest(normalized),
        document=normalized,
    )


class InMemoryDocumentRepository:
    """Deterministic adapter for tests and ephemeral local sessions."""

    def __init__(self) -> None:
        self._documents: dict[tuple[str, str], StoredDocument] = {}
        self._lock = threading.RLock()

    def load(self, collection: str, key: str) -> StoredDocument:
        identity = (
            validate_document_identifier(collection, "collection"),
            validate_document_identifier(key, "key"),
        )
        with self._lock:
            stored = self._documents.get(identity)
            if stored is None:
                raise DocumentNotFoundError(f"Document {collection}/{key} does not exist.")
            return _stored_document(
                stored.collection, stored.key, stored.storage_version, stored.document
            )

    def save(
        self,
        collection: str,
        key: str,
        document: dict[str, Any],
        *,
        expected_version: int,
    ) -> StoredDocument:
        collection = validate_document_identifier(collection, "collection")
        key = validate_document_identifier(key, "key")
        if expected_version < 0:
            raise DocumentConflictError("Expected version cannot be negative.")
        identity = (collection, key)
        with self._lock:
            current = self._documents.get(identity)
            actual_version = 0 if current is None else current.storage_version
            if actual_version != expected_version:
                raise DocumentConflictError(
                    f"Expected storage version {expected_version}; found {actual_version}."
                )
            stored = _stored_document(collection, key, actual_version + 1, document)
            self._documents[identity] = stored
            return _stored_document(
                stored.collection, stored.key, stored.storage_version, stored.document
            )

    def list_documents(
        self, collection: str, *, after: str | None, limit: int
    ) -> tuple[StoredDocument, ...]:
        collection = validate_document_identifier(collection, "collection")
        if after is not None:
            validate_document_identifier(after, "after")
        if limit < 1:
            raise DocumentStoreError("List limit must be positive.")
        with self._lock:
            keys = sorted(
                key
                for stored_collection, key in self._documents
                if stored_collection == collection and (after is None or key > after)
            )[:limit]
            return tuple(self.load(collection, key) for key in keys)


class AtomicJsonDocumentRepository:
    """Single-process local adapter using atomic same-directory file replacement."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._lock = threading.RLock()

    def _path(self, collection: str, key: str) -> Path:
        collection = validate_document_identifier(collection, "collection")
        key = validate_document_identifier(key, "key")
        return self._root / collection / f"{key}.json"

    def load(self, collection: str, key: str) -> StoredDocument:
        path = self._path(collection, key)
        with self._lock:
            try:
                envelope = json.loads(path.read_text(encoding="utf-8"))
            except FileNotFoundError as error:
                raise DocumentNotFoundError(f"Document {collection}/{key} does not exist.") from error
            except (OSError, json.JSONDecodeError) as error:
                raise DocumentCorruptionError(f"Cannot read owned document {path}.") from error
            if (
                not isinstance(envelope, dict)
                or envelope.get("format") != _FORMAT
                or envelope.get("collection") != collection
                or envelope.get("key") != key
                or not isinstance(envelope.get("storage_version"), int)
                or not isinstance(envelope.get("document"), dict)
            ):
                raise DocumentCorruptionError(f"Owned document envelope is invalid: {path}.")
            stored = _stored_document(
                collection, key, envelope["storage_version"], envelope["document"]
            )
            if envelope.get("etag") != stored.etag:
                raise DocumentCorruptionError(f"Owned document digest does not match: {path}.")
            return stored

    def save(
        self,
        collection: str,
        key: str,
        document: dict[str, Any],
        *,
        expected_version: int,
    ) -> StoredDocument:
        path = self._path(collection, key)
        if expected_version < 0:
            raise DocumentConflictError("Expected version cannot be negative.")
        with self._lock:
            try:
                current = self.load(collection, key)
            except DocumentNotFoundError:
                current = None
            actual_version = 0 if current is None else current.storage_version
            if actual_version != expected_version:
                raise DocumentConflictError(
                    f"Expected storage version {expected_version}; found {actual_version}."
                )
            stored = _stored_document(collection, key, actual_version + 1, document)
            envelope = {
                "format": _FORMAT,
                "collection": collection,
                "key": key,
                "storage_version": stored.storage_version,
                "etag": stored.etag,
                "document": stored.document,
            }
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    newline="\n",
                    dir=path.parent,
                    prefix=f".{key}.",
                    suffix=".tmp",
                    delete=False,
                ) as stream:
                    json.dump(envelope, stream, ensure_ascii=False, indent=2, allow_nan=False)
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                    temporary_path = Path(stream.name)
                os.replace(temporary_path, path)
            except OSError as error:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)
                raise DocumentStoreError(f"Cannot atomically save document {path}.") from error
            return stored

    def list_documents(
        self, collection: str, *, after: str | None, limit: int
    ) -> tuple[StoredDocument, ...]:
        collection = validate_document_identifier(collection, "collection")
        if after is not None:
            validate_document_identifier(after, "after")
        if limit < 1:
            raise DocumentStoreError("List limit must be positive.")
        directory = self._root / collection
        if not directory.exists():
            return ()
        keys = sorted(
            path.stem
            for path in directory.glob("*.json")
            if _IDENTIFIER.fullmatch(path.stem) and (after is None or path.stem > after)
        )[:limit]
        return tuple(self.load(collection, key) for key in keys)
