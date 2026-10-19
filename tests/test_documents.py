from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.application.documents import (
    AtomicJsonDocumentRepository,
    DocumentConflictError,
    DocumentCorruptionError,
    InMemoryDocumentRepository,
    InvalidDocumentKeyError,
)


class DocumentRepositoryContractTests(unittest.TestCase):
    def test_memory_adapter_copies_documents_and_checks_versions(self) -> None:
        repository = InMemoryDocumentRepository()
        source = {"value": [1, 2]}
        created = repository.save("runs", "run-1", source, expected_version=0)
        source["value"].append(3)

        loaded = repository.load("runs", "run-1")
        self.assertEqual(created.storage_version, 1)
        self.assertEqual(loaded.document, {"value": [1, 2]})
        with self.assertRaises(DocumentConflictError):
            repository.save("runs", "run-1", {"value": []}, expected_version=0)

    def test_atomic_adapter_round_trips_and_updates_with_expected_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = AtomicJsonDocumentRepository(Path(directory))
            first = repository.save("runs", "run-1", {"value": 1}, expected_version=0)
            second = repository.save("runs", "run-1", {"value": 2}, expected_version=1)
            loaded = repository.load("runs", "run-1")

        self.assertEqual(first.storage_version, 1)
        self.assertEqual(second.storage_version, 2)
        self.assertEqual(loaded.document, {"value": 2})
        self.assertNotEqual(first.etag, second.etag)

    def test_atomic_adapter_fails_closed_for_corrupt_owned_document(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = AtomicJsonDocumentRepository(root)
            repository.save("runs", "run-1", {"value": 1}, expected_version=0)
            path = root / "runs" / "run-1.json"
            envelope = json.loads(path.read_text(encoding="utf-8"))
            envelope["document"]["value"] = 2
            path.write_text(json.dumps(envelope), encoding="utf-8")

            with self.assertRaises(DocumentCorruptionError):
                repository.load("runs", "run-1")

    def test_identifier_validation_prevents_path_traversal(self) -> None:
        repository = InMemoryDocumentRepository()
        with self.assertRaises(InvalidDocumentKeyError):
            repository.save("runs", "../outside", {"value": 1}, expected_version=0)
