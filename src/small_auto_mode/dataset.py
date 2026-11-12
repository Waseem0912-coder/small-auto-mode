"""Reviewed records, provenance validation and connected-group data splitting."""
import argparse
import hashlib
import json
from pathlib import Path
import random
from .jev import canonical, strict_json

LABELS = ("allow", "ask", "deny")
SOURCES = {"human", "teacher_model", "claude_auto_classifier"}


def input_text(record):
    # Never include labels, reasons, provider verdicts, session ids or provenance as features.
    return canonical({"user_intent": record["user_intent"], "tool": record["tool"],
                      "environment": record["environment"], "history": record.get("history", []),
                      "untrusted_context": record.get("untrusted_context", [])}).decode()


def validate(record, allowed_sources=("human",)):
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    for field in ("id", "session_id", "scenario_family", "user_intent"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError("missing " + field)
    tool = record.get("tool")
    if not isinstance(tool, dict) or not isinstance(tool.get("name"), str) or not tool["name"] or not isinstance(tool.get("arguments"), dict):
        raise ValueError("invalid tool")
    if not isinstance(record.get("environment"), dict) or not isinstance(record.get("history", []), list):
        raise ValueError("invalid context")
    if not isinstance(record.get("untrusted_context", []), list) or any(not isinstance(x, str) for x in record.get("untrusted_context", [])):
        raise ValueError("invalid untrusted context")
    label, provenance = record.get("label", {}), record.get("provenance", {})
    if not isinstance(label, dict) or label.get("decision") not in LABELS or label.get("verified") is not True:
        raise ValueError("an explicitly verified decision is required")
    if label.get("source") not in SOURCES or label["source"] not in allowed_sources:
        raise ValueError("unapproved label source; hook observations are not labels")
    if not isinstance(provenance, dict) or provenance.get("training_rights") not in ("owned", "licensed", "permission"):
        raise ValueError("document training rights")
    for key in ("rights_basis", "reviewer", "context_reviewed"):
        if not provenance.get(key):
            raise ValueError("missing provenance " + key)
    if provenance["context_reviewed"] is not True:
        raise ValueError("context must be reviewed")
    if len(canonical(record)) > 128000:
        raise ValueError("oversized record")


def read_records(path, allowed_sources=("human",)):
    rows = []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = strict_json(line)
            validate(row, allowed_sources)
        except (ValueError, TypeError, KeyError) as error:
            raise ValueError(f"{path}:{number}: {error}") from error
        rows.append(row)
    if not rows:
        raise ValueError("empty corpus")
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError("duplicate record id")
    return rows


def split_records(rows, seed=42):
    """Connected components prevent BOTH session and scenario-family overlap."""
    parent = list(range(len(rows)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    seen, labels = {}, {}
    for i, row in enumerate(rows):
        content = hashlib.sha256(input_text(row).encode()).hexdigest()
        if content in labels and labels[content] != row['label']['decision']:
            raise ValueError("contradictory labels for identical context")
        labels[content] = row['label']['decision']
        for key in (("session", row['session_id']), ("scenario", row['scenario_family']), ("content", content)):
            if key in seen:
                parent[find(i)] = find(seen[key])
            seen[key] = i
    groups = {}
    for i, row in enumerate(rows):
        groups.setdefault(find(i), []).append(row)
    groups = list(groups.values())
    if len(groups) < 3:
        raise ValueError("need at least three independent session/scenario components")
    random.Random(seed).shuffle(groups)
    n = max(1, round(.15 * len(groups)))
    out = {"test": groups[:n], "calibration": groups[n:2*n], "train": groups[2*n:]}
    return {k: [r for group in v for r in group] for k, v in out.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    parser.add_argument("--allow-source", action="append", choices=sorted(SOURCES), default=[])
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    sources = ["human", *args.allow_source]
    rows = read_records(args.input, sources)
    splits = split_records(rows, args.seed)
    if {r['label']['decision'] for r in splits['train']} != set(LABELS):
        raise ValueError("training split must contain all three decisions")
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    manifest = {"schema_version": 1, "seed": args.seed, "allowed_sources": sources,
                "input_sha256": hashlib.sha256(Path(args.input).read_bytes()).hexdigest(), "splits": {}}
    for name, records in splits.items():
        payload = ''.join(json.dumps(r, sort_keys=True) + '\n' for r in records)
        (out / (name + '.jsonl')).write_text(payload)
        manifest['splits'][name] = {"count": len(records), "sha256": hashlib.sha256(payload.encode()).hexdigest()}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
