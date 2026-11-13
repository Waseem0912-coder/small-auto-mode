"""Auditable context reference over a HOST-OWNED normalized event stream.

This is not a Claude transcript decoder, identity verifier, summarizer, or policy
model. See docs/context/reference.md before integrating. All attestations,
registry entries, policy and snapshot metadata must come from the trusted host.
"""
import copy
import hashlib
import json
import math


MAX_SOURCE_BYTES = 1_000_000
DEFAULT_PACKET_BYTES = 128_000
DEFAULT_HOST_CONTEXT_BYTES = 2_000
CONTRACT = "small-auto-mode.context.v1"


class InvalidContext(ValueError):
    pass


def _object(value, required, optional=()):
    if (not isinstance(value, dict) or not set(required) <= set(value)
            or set(value) - set(required) - set(optional)):
        raise InvalidContext("invalid_fields")


def _text(value, *, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise InvalidContext("invalid_text")
    return value


def _strings(value):
    if not isinstance(value, list):
        raise InvalidContext("invalid_string_list")
    for item in value:
        _text(item)
    return value


def _json_tree(value):
    """Reject Python-only values, non-string keys and non-finite numbers."""
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if isinstance(value, list):
        for item in value:
            _json_tree(item)
        return
    if isinstance(value, dict) and all(isinstance(k, str) for k in value):
        for item in value.values():
            _json_tree(item)
        return
    raise InvalidContext("invalid_json_value")


def serialize(value):
    """Canonical ASCII JSON; angle brackets cannot impersonate wrapper tags.

    Encoding is an unambiguous data boundary, not a prompt-injection detector.
    JSON decoding recovers the exact strings, including original control chars.
    """
    _json_tree(value)
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def _digest(value):
    return hashlib.sha256(serialize(value).encode("ascii")).hexdigest()


def _call(value):
    _object(value, ("id", "name", "arguments"))
    _text(value["id"])
    _text(value["name"])
    if not isinstance(value["arguments"], dict):
        raise InvalidContext("invalid_arguments")


def _registry(entries):
    if not isinstance(entries, list):
        raise InvalidContext("invalid_registry")
    registry = {}
    for entry in entries:
        _object(entry, ("name",), ("history_mode", "argument_fields", "question_tool"))
        name = _text(entry["name"])
        if name in registry:
            raise InvalidContext("duplicate_tool_name")
        if entry.get("history_mode", "include") not in ("include", "omit"):
            raise InvalidContext("invalid_history_mode")
        if type(entry.get("question_tool", False)) is not bool:
            raise InvalidContext("invalid_question_tool")
        if "argument_fields" in entry:
            fields = _strings(entry["argument_fields"])
            if len(set(fields)) != len(fields):
                raise InvalidContext("duplicate_argument_field")
        registry[name] = entry
    return registry


def _adapt(call, spec):
    fields = spec.get("argument_fields")
    args = call["arguments"]
    kept = args if fields is None else {key: args[key] for key in fields if key in args}
    return {"id": call["id"], "name": call["name"], "arguments": kept}, sorted(set(args) - set(kept))


def _attestations(value, events):
    roles = {"human": "human", "answers": "tool_result", "summaries": "summary",
             "host_context": "host_context"}
    _object(value, roles)
    by_id = {event["id"]: event for event in events}
    result = {}
    for role, kind in roles.items():
        ids = _strings(value[role])
        if len(set(ids)) != len(ids):
            raise InvalidContext("duplicate_attestation")
        for event_id in ids:
            if event_id not in by_id or by_id[event_id]["kind"] != kind:
                raise InvalidContext("invalid_attestation_target")
        result[role] = set(ids)
    return result


def _events(value):
    if not isinstance(value, list):
        raise InvalidContext("invalid_events")
    ids = set()
    for event in value:
        if not isinstance(event, dict):
            raise InvalidContext("invalid_event")
        event_id = _text(event.get("id"))
        _text(event.get("kind"))
        if event_id in ids:
            raise InvalidContext("duplicate_event_id")
        ids.add(event_id)
    return value


def _snapshot(value):
    if value is None:
        return
    _object(value, ("id", "text", "sources"))
    _text(value["id"])
    _text(value["text"], empty=True)
    if not isinstance(value["sources"], list):
        raise InvalidContext("invalid_snapshot_sources")
    for source in value["sources"]:
        _object(source, ("path", "kind"))
        _text(source["path"])
        _text(source["kind"])


def build_packet(document):
    """Return ready/unassessed on assembly, ask on any unsupported/incomplete input.

    Never execute or authorize a call. `ready` only means the reference contract
    was satisfied. Host attestations are assertions from the caller, not proof
    established by this function. Input is copied; returned data never aliases it.
    """
    audit = []
    errors = []
    try:
        source = serialize(document)
        if len(source) > MAX_SOURCE_BYTES:
            raise InvalidContext("source_byte_budget_exceeded")
        doc = copy.deepcopy(document)
        _object(doc, ("schema_version", "events", "attestations", "registry", "candidate",
                      "instruction_snapshot", "stable_policy", "session", "preprocessing"),
                ("options",))
        if type(doc["schema_version"]) is not int or doc["schema_version"] != 1:
            raise InvalidContext("unsupported_schema_version")
        events = _events(doc["events"])
        attest = _attestations(doc["attestations"], events)
        registry = _registry(doc["registry"])
        _call(doc["candidate"])
        if doc["candidate"]["name"] not in registry:
            errors.append("unknown_candidate_tool")
        _snapshot(doc["instruction_snapshot"])
        _object(doc["stable_policy"], ("version", "rules"))
        _text(doc["stable_policy"]["version"])
        _strings(doc["stable_policy"]["rules"])
        _object(doc["session"], ("environment", "constraints"))
        if not isinstance(doc["session"]["environment"], dict):
            raise InvalidContext("invalid_environment")
        _strings(doc["session"]["constraints"])
        pre = doc["preprocessing"]
        _object(pre, ("account_memory", "window"))
        if pre["account_memory"] not in ("absent", "redacted"):
            errors.append("account_memory_preprocessing_unconfirmed")
        if pre["window"] not in ("full", "compacted"):
            errors.append("unsupported_window_state")
        options = doc.get("options", {})
        _object(options, (), ("max_packet_bytes", "max_host_context_bytes", "include_outcomes"))
        limit = options.get("max_packet_bytes", DEFAULT_PACKET_BYTES)
        host_limit = options.get("max_host_context_bytes", DEFAULT_HOST_CONTEXT_BYTES)
        for number in (limit, host_limit):
            if type(number) is not int or not 1 <= number <= MAX_SOURCE_BYTES:
                raise InvalidContext("invalid_byte_budget")
        if type(options.get("include_outcomes", False)) is not bool:
            raise InvalidContext("invalid_outcome_option")
        projected, calls, seen_results, included_calls = [], {}, set(), set()
        correlated_results = set()
        human_count = summary_count = 0
        # Only attested host metadata may cause an omitted history tool to remain.
        host_calls = {e.get("call_id") for e in events
                      if e["id"] in attest["host_context"] and isinstance(e.get("call_id"), str)}
        answer_calls = {e.get("call_id") for e in events
                        if e["id"] in attest["answers"] and isinstance(e.get("call_id"), str)}

        def note(event, action, reason, **details):
            audit.append({"event_id": event["id"], "action": action, "reason": reason, **details})

        for event in events:
            kind, event_id = event["kind"], event["id"]
            if kind in ("human", "summary", "assistant_text", "internal"):
                _object(event, ("id", "kind", "text"))
                _text(event["text"], empty=True)
                if kind in ("assistant_text", "internal"):
                    note(event, "drop", "excluded_" + kind)
                elif event_id not in attest["human" if kind == "human" else "summaries"]:
                    errors.append("unattested_" + kind)
                    note(event, "reject", "missing_host_attestation")
                elif not event["text"].strip():
                    errors.append("empty_" + kind)
                    note(event, "reject", "empty_context")
                else:
                    projected.append({"kind": kind, "event_id": event_id, "text": event["text"],
                                      "origin": "human" if kind == "human" else "assistant_summary"})
                    human_count += kind == "human"
                    summary_count += kind == "summary"
                    note(event, "keep", "attested_" + kind)
            elif kind == "tool_use":
                _object(event, ("id", "kind", "call"))
                call = event["call"]
                _call(call)
                if call["id"] in calls or call["id"] == doc["candidate"]["id"]:
                    raise InvalidContext("duplicate_call_id")
                spec = registry.get(call["name"])
                calls[call["id"]] = (call, spec)
                if spec is None:
                    errors.append("unknown_history_tool")
                    note(event, "reject", "unknown_tool")
                elif (spec.get("history_mode", "include") == "omit"
                      and call["id"] not in host_calls | answer_calls):
                    note(event, "drop", "registry_history_omission")
                else:
                    adapted, removed = _adapt(call, spec)
                    projected.append({"kind": "tool_use", "event_id": event_id, "call": adapted})
                    included_calls.add(call["id"])
                    note(event, "transform" if removed else "keep", "registry_adapter",
                         omitted_argument_fields=removed)
            elif kind == "tool_result":
                _object(event, ("id", "kind", "call_id", "text", "is_error"), ("denial_kind",))
                _text(event["call_id"])
                _text(event["text"], empty=True)
                if type(event["is_error"]) is not bool:
                    raise InvalidContext("invalid_result_status")
                if "denial_kind" in event:
                    _text(event["denial_kind"])
                if event["call_id"] in seen_results:
                    raise InvalidContext("duplicate_tool_result")
                seen_results.add(event["call_id"])
                prior = calls.get(event["call_id"])
                if prior is not None:
                    correlated_results.add(event["call_id"])
                if event_id in attest["answers"]:
                    if (not prior or not prior[1] or not prior[1].get("question_tool", False)
                            or event["is_error"] or event.get("denial_kind") or not event["text"].strip()):
                        errors.append("invalid_attested_answer")
                        note(event, "reject", "answer_requires_successful_prior_question")
                    else:
                        projected.append({"kind": "human_answer", "event_id": event_id,
                                          "call_id": event["call_id"], "text": event["text"]})
                        note(event, "transform", "attested_question_answer")
                elif options.get("include_outcomes", False) and event["call_id"] in included_calls:
                    projected.append({"kind": "outcome", "event_id": event_id,
                                      "call_id": event["call_id"],
                                      "status": "denied" if event.get("denial_kind") else
                                      "error" if event["is_error"] else "success"})
                    note(event, "transform", "coarse_outcome_only_result_text_excluded")
                else:
                    note(event, "drop", "ordinary_tool_result_text_excluded")
            elif kind == "host_context":
                _object(event, ("id", "kind", "call_id", "text", "freshness"))
                _text(event["call_id"])
                _text(event["text"])
                prior = calls.get(event["call_id"])
                if (event_id not in attest["host_context"] or not prior or not prior[1]
                        or event["call_id"] not in correlated_results
                        or event["freshness"] not in ("current", "snapshot")):
                    errors.append("invalid_host_context")
                    note(event, "reject", "host_context_requires_attestation_prior_call_and_freshness")
                elif len(serialize(event["text"]).encode("ascii")) > host_limit:
                    errors.append("host_context_byte_budget_exceeded")
                    note(event, "reject", "host_context_too_large_no_silent_truncation")
                else:
                    projected.append({"kind": "host_context", "event_id": event_id,
                                      "call_id": event["call_id"], "text": event["text"],
                                      "freshness": event["freshness"]})
                    note(event, "keep", "attested_correlated_host_context")
            else:
                errors.append("unsupported_event_kind")
                note(event, "reject", "unsupported_event_kind")

        if not human_count:
            errors.append("missing_authenticated_user_intent")
        if pre["window"] == "compacted" and not summary_count:
            errors.append("compacted_window_without_summary")
        stable = {"contract": CONTRACT, "policy": doc["stable_policy"]}
        dynamic = {"session": doc["session"], "instruction_snapshot": doc["instruction_snapshot"],
                   "history": projected, "candidate": doc["candidate"]}
        # Bind the configuration and all host evidence too, including dropped events.
        binding = {"contract": CONTRACT, "source": doc}
        serialized = serialize({"stable": stable, "dynamic": dynamic})
        byte_count = len(serialized.encode("ascii"))
        if byte_count > limit:
            errors.append("packet_byte_budget_exceeded")
        result = {"schema_version": 1, "ready": not errors,
                  "decision": "ask" if errors else "unassessed", "errors": sorted(set(errors)),
                  "audit": audit, "candidate_sha256": _digest(doc["candidate"]),
                  "stable_sha256": _digest(stable), "binding_sha256": _digest(binding),
                  "packet_bytes": byte_count}
        if not errors:
            result.update(stable=stable, dynamic=dynamic, serialized=serialized,
                          packet_sha256=hashlib.sha256(serialized.encode("ascii")).hexdigest())
        return result
    except InvalidContext as error:
        return {"schema_version": 1, "ready": False, "decision": "ask",
                "errors": [str(error)], "audit": audit}
    except (TypeError, ValueError, KeyError, RecursionError, OverflowError):
        # Do not echo malformed values or emit a partial inference packet.
        return {"schema_version": 1, "ready": False, "decision": "ask",
                "errors": ["invalid_context_input"], "audit": audit}
