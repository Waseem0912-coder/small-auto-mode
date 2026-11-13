"""Artifact checks must catch drift and wrong offsets without executing code."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from scripts.verify_context_evidence import verify


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = b"/*\xff*/function demo(){throw new Error('never run');}"
        (self.root / "module.js").write_bytes(self.source)
        self.manifest = {"schema_version": 1, "modules": [{
            "path": "module.js", "length": len(self.source),
            "sha256": hashlib.sha256(self.source).hexdigest(),
            "symbols": [{"name": "demo", "byte_offset": 5, "anchor": "function demo("}],
        }], "artifact": {"size": len(self.source), "sha256": hashlib.sha256(self.source).hexdigest()}}

    def test_verified_bytes_and_latin1_offsets(self):
        result = verify(self.manifest, self.root, self.root / "module.js")
        self.assertTrue(result["ok"])
        self.assertTrue(result["binary_verified"])
        self.assertEqual(result["anchors_verified"], 1)

    def test_equal_length_changed_source_fails(self):
        (self.root / "module.js").write_bytes(self.source.replace(b"demo", b"drft"))
        result = verify(self.manifest, self.root)
        self.assertFalse(result["ok"])
        self.assertEqual(result["anchors_verified"], 0)

    def test_matching_hash_does_not_excuse_bad_offset(self):
        self.manifest["modules"][0]["symbols"][0]["byte_offset"] = 4
        self.assertFalse(verify(self.manifest, self.root)["ok"])

    def test_missing_module_is_failure(self):
        (self.root / "module.js").unlink()
        self.assertFalse(verify(self.manifest, self.root)["ok"])

    def test_path_escape_rejected(self):
        self.manifest["modules"][0]["path"] = "../private.js"
        with self.assertRaises(ValueError):
            verify(self.manifest, self.root)

    def test_unknown_schema_rejected(self):
        self.manifest["schema_version"] = 99
        with self.assertRaises(ValueError):
            verify(self.manifest, self.root)
