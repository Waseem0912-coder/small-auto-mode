"""Opt-in passive hook observations. Observations are NEVER training labels."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid
from .jev import canonical, strict_json

EVENTS = {"PreToolUse", "PostToolUse", "PostToolUseFailure", "PermissionDenied"}
SENSITIVE = re.compile(r"password|secret|token|api.?key|authorization|credential", re.I)


def redact(value):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if SENSITIVE.search(k) else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        value = re.sub(r"\b(?:sk-ant-|sk-|ghp_|gho_|ghu_)[A-Za-z0-9_-]{12,}", "[REDACTED]", value)
        value = re.sub(r"(?i)Bearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer [REDACTED]", value)
    return value


def observe(event, include_input=False, version="unknown"):
    if not isinstance(event, dict) or event.get("hook_event_name") not in EVENTS:
        raise ValueError("unsupported event")
    for field in ("session_id", "tool_use_id", "tool_name"):
        if not isinstance(event.get(field), str) or not event[field]:
            raise ValueError("missing correlation field")
    if not isinstance(event.get("tool_input"), dict):
        raise ValueError("missing tool input")
    reason = event.get("reason", "")
    if not isinstance(reason, str):
        raise ValueError("invalid reason")
    status = "observed"
    if event["hook_event_name"] == "PermissionDenied":
        status = "denied_without_confirmed_verdict"
        if reason == "Classifier unavailable" or reason.startswith("Auto mode could not evaluate this action"):
            status = "classifier_unavailable_or_no_verdict"
        elif re.fullmatch(r"\[[^\[\]\n]+\]", reason.strip()):
            status = "possible_classifier_denial_requires_review"
    out = {"schema_version": 1, "event_id": uuid.uuid4().hex,
           "observed_at": datetime.now(timezone.utc).isoformat(),
           "session_id": event["session_id"], "tool_use_id": event["tool_use_id"],
           "hook_event_name": event["hook_event_name"], "tool_name": event["tool_name"],
           "permission_mode": event.get("permission_mode", "unknown"),
           "claude_code_version": version, "status": status,
           "arguments_sha256": hashlib.sha256(canonical(event["tool_input"])).hexdigest(),
           "label": None, "training_eligible": False}
    if include_input:
        out["tool_input"] = redact(event["tool_input"])
        out["reason"] = redact(reason)
    # Never follow transcript_path or save tool output, cwd, credentials or the entire input.
    return out


def save_observation(record, output):
    directory = Path(output)
    if directory.is_symlink():
        raise ValueError("output directory cannot be a symlink")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = directory / (uuid.uuid4().hex + ".json")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(target, flags, 0o600), "w") as handle:
        json.dump(record, handle, sort_keys=True)
        handle.write("\n")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--include-input", action="store_true", help="Opt in to locally storing redacted arguments; inspect before sharing")
    parser.add_argument("--claude-code-version", default="unknown")
    args = parser.parse_args()
    try:
        raw = sys.stdin.buffer.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError("hook input too large")
        save_observation(observe(strict_json(raw), args.include_input, args.claude_code_version), args.output)
    except Exception:
        print("small-auto-mode: observation not saved", file=sys.stderr)
    # Passive logging never overrides permissions, changes arguments or requests retries.
    print("{}")


if __name__ == "__main__":
    main()
