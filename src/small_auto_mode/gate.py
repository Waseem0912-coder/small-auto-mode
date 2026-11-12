"""Host policy always precedes a learned decision; never executes tools."""
import math
from .jev import fingerprint, validate_case


def precheck(case, policy):
    validate_case(case)
    if not isinstance(policy, dict):
        raise ValueError("policy must be host supplied")
    for key in ("known_tools", "deny_tools", "ask_tools"):
        if not isinstance(policy.get(key, []), list) or any(not isinstance(v, str) for v in policy.get(key, [])):
            raise ValueError("invalid tool policy")
    if type(policy.get("auto_allow", False)) is not bool:
        raise ValueError("auto_allow must be boolean")
    name = case["tool"]["name"]
    if case["host_gate"] == "deny" or name in policy.get("deny_tools", []):
        return "deny", "host_policy"
    if case["host_gate"] == "ask" or name in policy.get("ask_tools", []):
        return "ask", "host_review_required"
    if name not in policy.get("known_tools", []):
        return "ask", "unknown_tool"
    return None


def decide(case, policy, probabilities=None):
    try:
        early = precheck(case, policy)
        result = {"decision": "ask", "reason": "missing_assessment",
                  "binding_sha256": fingerprint({"case": case, "policy": policy})}
        if early:
            result.update(decision=early[0], reason=early[1])
            return result
        if probabilities is None:
            return result
        if not isinstance(probabilities, dict) or set(probabilities) != {"allow", "ask", "deny"}:
            raise ValueError("invalid class distribution")
        if any(type(v) not in (float, int) or not math.isfinite(v) or not 0 <= v <= 1 for v in probabilities.values()):
            raise ValueError("invalid probability")
        if abs(sum(probabilities.values()) - 1) > 1e-5:
            raise ValueError("probabilities must sum to one")
        result["probabilities"] = probabilities
        if not policy.get("auto_allow", False):
            result["reason"] = "shadow_mode"
            return result
        threshold = policy.get("allow_min")
        if type(threshold) not in (float, int) or not math.isfinite(threshold) or not .5 < threshold <= 1:
            raise ValueError("configure a validated allow_min")
        if probabilities["allow"] >= threshold:
            result.update(decision="allow", reason="configured_threshold_passed")
        else:
            result["reason"] = "uncertain_or_risky"
        return result
    except (ValueError, TypeError, KeyError, OverflowError):
        return {"decision": "ask", "reason": "invalid_context_or_assessment"}


def assess(case, policy, predictor):
    """predictor(case) -> {allow,ask,deny} probabilities. Exceptions abstain."""
    try:
        if precheck(case, policy):
            return decide(case, policy)
        return decide(case, policy, predictor(case))
    except Exception:
        return {"decision": "ask", "reason": "assessment_failed"}
