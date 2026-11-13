#!/usr/bin/env python3
"""Verify locally supplied inspection artifacts; never execute or print their source."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def verify(manifest, extracted, binary=None):
    """Check exact artifact identity and byte anchors, not behavioral equivalence."""
    errors, modules_verified, anchors_verified = [], 0, 0
    root = Path(extracted).resolve(strict=True)
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported evidence schema")
    records = manifest["modules"]
    if not isinstance(records, list) or not records:
        raise ValueError("evidence must contain modules")
    seen = set()
    for record in records:
        relative = Path(record["path"])
        if relative.is_absolute() or ".." in relative.parts or relative in seen:
            raise ValueError("unsafe or duplicate module path")
        seen.add(relative)
        if not re.fullmatch(r"[a-f0-9]{64}", record["sha256"]):
            raise ValueError("invalid expected digest")
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError("module escapes extraction directory")
        try:
            if path.stat().st_size != record["length"]:
                errors.append(f"{relative}: size mismatch")
                continue
            if digest(path) != record["sha256"]:
                errors.append(f"{relative}: SHA-256 mismatch")
                continue
            modules_verified += 1
            with path.open("rb") as handle:
                for symbol in record.get("symbols", []):
                    offset = symbol["byte_offset"]
                    anchor = symbol["anchor"].encode("latin1")
                    if type(offset) is not int or not anchor or not 0 <= offset <= record["length"] - len(anchor):
                        raise ValueError("invalid symbol offset or anchor")
                    handle.seek(offset)
                    if handle.read(len(anchor)) != anchor:
                        errors.append(f"{relative}: anchor mismatch for {symbol['name']}")
                    else:
                        anchors_verified += 1
        except OSError:
            errors.append(f"{relative}: missing or unreadable")
    binary_verified = False
    if binary is not None:
        path = Path(binary)
        artifact = manifest["artifact"]
        try:
            binary_verified = path.stat().st_size == artifact["size"] and digest(path) == artifact["sha256"]
            if not binary_verified:
                errors.append("binary: size or SHA-256 mismatch")
        except OSError:
            errors.append("binary: missing or unreadable")
    return {"ok": not errors, "modules_verified": modules_verified,
            "anchors_verified": anchors_verified, "binary_checked": binary is not None,
            "binary_verified": binary_verified, "errors": errors,
            "scope": "artifact identity and anchor locations only; no inference or equivalence test"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path,
                        default=Path(__file__).resolve().parents[1] / "docs/context/evidence.json")
    parser.add_argument("--extracted", type=Path, required=True)
    parser.add_argument("--binary", type=Path)
    args = parser.parse_args()
    try:
        result = verify(json.loads(args.manifest.read_text()), args.extracted, args.binary)
    except (OSError, ValueError, KeyError, TypeError):
        result = {"ok": False, "errors": ["invalid manifest or input directory"]}
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
