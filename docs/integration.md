# Host integration boundaries

The package returns decisions; your dispatcher executes tools. Put the gate immediately before the effect and retain OS/network isolation. No inference result grants a new filesystem, network or account capability.

## Local classifier

Instantiate `LocalClassifier` once and reuse it; loading 596M parameters per call is inappropriate for a low-latency service. Pass it to `gate.assess(case, policy, predictor)`. `predictor` returns exactly `{allow, ask, deny}` probabilities summing to one. Failures and malformed distributions return `ask`.

The host supplies user intent, durable constraints, exact tool identity/arguments, environment, optional provenance-aware history, and untrusted context. It also determines `host_gate` (`eligible`, `ask`, `deny`) before model scoring. Eligibility means the host has checked the effect/capabilities sufficiently to consider automatic approval, not that the model has declared itself safe. Unknown tools ask. Deterministic denies and mandatory approval take precedence over model results and are checked before invoking the predictor.

Default policy leaves `auto_allow` false. When evaluated, explicit policy may set it true and set `allow_min`. Below threshold, the model abstains. Model `deny` probabilities inform abstention; only deterministic host policy produces an automatic deny. The classifier's supervised `ask` class captures missing authorization/context, not merely low numeric confidence.

The returned SHA-256 binds the snapshot of case and policy. It is not a signature, principal check, single-use token or protection against filesystem changes. Re-resolve paths and recipients, validate current state, bind approvals to the principal/session, and execute the exact reviewed call. Preserve earlier user constraints through compaction. Resolve shell syntax and transitive effects in the trusted adapter; the small model is not a complete shell analyzer.

## Jev

`jev.build_request` is offline. `jev.query` explicitly calls `https://api.typesafe.ai/v1/systemone` with `TYPESAFE_API_KEY` and a pinned versioned model ID. Its five Noul probabilities are composed separately from the local three-class head. The example uses shadow mode and no production threshold. API errors, wrong model IDs or malformed responses never approve a call.

Jev Noul has no separate confidence field. A high or low probability is not proof of calibration on this task. The local and Jev interfaces are separate experiments; compare their decisions against a shared reviewed corpus before choosing one.

## Claude Code

The included hook configuration is **observation only**. It is not an installed replacement for Claude Code auto mode. To enforce your own classifier through PreToolUse, write a trusted host adapter that obtains current intent/policy, calls the gate, maps its decision to Claude's documented `permissionDecision`, and blocks on adapter failure. Keep that adapter and policy outside executor-writable paths. A generic static context file would be stale and is not supplied as a production integration.

## Tool search

`search.search` ranks a catalog; `allowed_names` filters visibility before matching. Return `SearchResult.as_tool_result(tool_use_id)` for the documented client-side tool-reference format. Referenced definitions must already be in the Messages API tools array, usually marked `defer_loading: true`. Finding a tool never authorizes using it.

This prototype omits live MCP refresh, session-loaded-tool tracking, Claude Code's internal name normalization and context-token budgeting. The hosted regex/BM25 search API is a separate implementation. Our scorer is not a safety confidence score.

## Advisor

```python
from small_auto_mode.advisor import BETA, advisor_tool
tool = advisor_tool("<supported-advisor-model-id>")
# Add tool to your Messages request and BETA to its anthropic-beta header.
```

The helper builds the public `advisor_20260301` declaration and performs no API call. Use an account/model pair supported by the current [advisor API](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool). The executor chooses when to consult it; the server uses a separate model and its private prompt. The executor's advisor call has empty input, and the service supplies conversation context. Some result variants are opaque/encrypted; preserve them rather than treating them as readable training labels. Advisor errors can allow the executor to continue, so advice must never replace the fail-closed authorization stage.

A custom client-side second-model reviewer with a prompt you control is another design, but is not an exact reproduction of Anthropic's advisor. This project supplies neither hidden prompts nor server model weights.
