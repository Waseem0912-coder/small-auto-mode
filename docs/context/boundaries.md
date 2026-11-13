# Server safeguards, tool discovery and advisor context

These paths use different views of a session. The local auto-mode classifier's
projection in [projection.md](projection.md) is **not** a universal context
format shared by all three features.

Evidence labels in this document:

- **Recovered:** readable client behavior in the pinned Claude Code 2.1.323
  artifact. Offsets are zero-based bytes in the named extracted module.
- **Documented:** behavior described by the linked public API documentation;
  this is not a recovery of private server code.
- **Reference choice:** a recommendation for an independent implementation.

Exact artifact hashes and source anchors are in [evidence.json](evidence.json).
Feature flags and live provider configuration can change which recovered branch
runs. No provider inference was performed for this investigation.

## The separate context surfaces

| Surface | What receives context | What the client establishes | What remains unavailable |
| --- | --- | --- | --- |
| Local auto-mode request | A separate hosted classifier request | Projected transcript, selected memory, policy and environment assembly | Hosted weights, training recipe and live quality |
| Server-integrated auto mode | `safeguards[].classifier_context` alongside the main model request | Auxiliary context shape, shedding, response parsing and stale-verdict handling | Server-side projection, prompts, model selection and execution |
| Local `ToolSearch` | A deterministic local ranker, then main-model context | Catalog selection, ranking, description cache and conditional schema-budget checks | No learned ranker is needed for this recovered function |
| Hosted search | A server search tool and main-model context | Public deferred-schema and tool-reference contract | Private search implementation beyond documented behavior |
| Advisor | A separate hosted advisor inference | Client declaration and public transcript-forwarding contract | Private advisor system prompt, weights and opaque advice content |

## Server-integrated auto-mode context

### Request construction

**Recovered:** the main request can carry a `dangerous_tool_use` safeguard with
a `classifier_context` field. The entry is conditional on the active provider,
beta support, routing and context availability; this is not the separate
`bHe` classifier Messages request.

The context builder `p$n` calls `BXr` with the host-prepared context, git state,
prior-turn context, system-reminder identifiers, events, artifact state and
several execution flags. It can attach text provenance and classifier facts.
The resulting object includes a version marker, permission rules, auto-mode
lists, platform and other supplied facts. Optional flags identify an attached
tool host, a structured-output handback or a limited set of tools to judge.

There are two distinct byte limits:

| Limit in this build | Meaning |
| --- | --- |
| 256,000 bytes | Soft target for the auxiliary object assembled by `BXr` |
| 1,040,000 bytes | Hard field ceiling checked by `p$n` after adding text provenance; a larger object is withheld |
| 200 characters | Maximum length of each normalized `judge_only_tools` name; an empty selected set or an oversized name prevents construction |

These are **serialized object byte budgets**, not the model's context-window
size or tokenizer limits. Do not transfer them to the local transcript builder.

**Recovered shedding order:** `BXr` tries the full object first. If it exceeds
the soft target, it performs these steps and rechecks size after each change:

1. Repeatedly halve retained prior-turn records, keeping the newest suffix.
2. Remove detailed Chrome tabs while keeping the enabled flag and baselines.
3. Empty the repository visibility cache.
4. Empty repository remotes.
5. Remove detailed git porcelain status.
6. Repeatedly halve event entries, retaining the newest suffix and recording
   the count of dropped events.
7. Repeatedly halve retained system reminders, keeping the newest suffix.
8. Remove artifact state.

Complete removals are recorded in `shed`; partial suffix reduction is not
equivalent to retaining all history. Rule lists are not silently chopped to
fit the soft target. The function can return a still-oversized static object
with a warning, after which the separate hard ceiling can withhold it entirely.
Absence of `classifier_context` therefore cannot be interpreted as an empty,
safe context or an affirmative classifier judgment.

The main request records which artifact facts, exact MCP allow rules, selected
tools, auto-mode lists and classifier facts were actually sent. That request
record is associated with the response, rather than trusting an arbitrary
later message to supply an equivalent snapshot.

### Result binding, freshness and rewrites

**Recovered:** the result parser expects one `dangerous_tool_use` result in
`safeguard_results`. It distinguishes unsupported/unavailable/unrecognized
results from per-tool results. Per-tool entries may be evaluated
(`flagged` or `not_flagged`), skipped or unavailable. Missing data is not a
`not_flagged` classification. The result record has an in-memory identity,
tracks sent facts and settles once; its `toJSON` does not serialize that live
result record as a reusable object.

Results are looked up against the relevant tool-use ID, with a client mapping
for normalized IDs. The outer permission gate still applies policy and
tool-specific checks. In particular:

- Changing a tool's input, or changing a sibling call reviewed in the same
  response, can void the server verdict. `XPr` tracks the rewrite cause and
  can remove the attached result before setting a rewritten-input marker.
- There is a feature-controlled exception for certain local rewrites; the
  artifact does **not** justify claiming that every rewrite is treated
  identically. Local fallback eligibility also depends on the active role.
- Before accepting an allow, the outer gate may call a tool's
  `staleServerClassifierContext` hook with the sent artifact snapshot and live
  state. A stale result becomes `server_context_stale` and blocks for retry.
  The logged fact classes include ownership, audience, shared-live state,
  co-writing, attestation, type declarations, watches and connectors.
- The hook is optional and feature-gated. These checks do not establish that
  every tool always revalidates every fact.
- A result associated with a message-thread request can cause the client to
  retry future classification without threading when the server reports that
  the thread mode is unsupported.

`JPr` maps a parsed server result into the client's classifier-result shape.
Unavailable and refused results remain distinct from evaluated ones. Outer
logic can select the separate local classifier for specific no-result,
unsupported, unavailable or rewritten-input cases, depending on whether the
role is `arbiter` or `arbiterWithLocalFallback` and on feature configuration.
Other cases block or prompt. This is why “all missing server results allow”
and “all errors always use exactly one fallback” would both be inaccurate.

**Reference choice:** bind an independent verdict to the exact normalized
candidate, policy version and relevant host-context version. Recheck those
facts immediately before execution. An attacker-controlled string saying
“owner” or “approved” must never substitute for the application's provenance
and freshness checks. This is a design lesson from the recovered boundaries,
not a claim that our reference code reproduces the entire native server path.

### Server-path evidence

| Module | Symbol / anchor | Byte offset | Evidence |
| --- | --- | ---: | --- |
| `chunk-579w43z0.js` | `p$n` | 2,866,901 | Auxiliary context construction and hard ceiling |
| `chunk-579w43z0.js` | `BXr` | 2,867,634 | Ordered variable-field shedding |
| `chunk-579w43z0.js` | `safeguards:[{type:eIs` | 3,096,929 | Main request carries the auxiliary context |
| `chunk-bpzcj4vc.js` | `vr` | 29,281 | Result shape validation |
| `chunk-bpzcj4vc.js` | `ZXi` | 31,938 | Record the facts sent with the request |
| `chunk-bpzcj4vc.js` | `Ar` | 33,953 | Unsupported thread handling |
| `chunk-bpzcj4vc.js` | `fJi` | 37,997 | Role-dependent fallback eligibility |
| `chunk-bpzcj4vc.js` | `XPr` | 40,051 | Input/sibling rewrite invalidation |
| `chunk-bpzcj4vc.js` | `JPr` | 43,219 | Server result to classifier-result adapter |
| `chunk-579w43z0.js` | `staleServerClassifierContext` call | 3,380,737 | Optional pre-execution artifact-freshness check |

## ToolSearch: catalog state becomes model context

### Local retrieval and caching

**Recovered:** the local ranker `qNt` consumes a query and tool catalog; it has
no model inference. Exact names and MCP prefixes have direct paths. General
queries use tokenized names, required terms, search hints and descriptions.
The existing [search.py](../../src/small_auto_mode/search.py) implements the
limited deterministic ranking behavior; it does not clone the entire client
wrapper.

The description cache is local to tool state. It caches descriptions by name
and invalidates when the sorted set of deferred tool names changes. That is
different from the provider prompt cache and from persistent memory. From
this invalidation condition alone, one must not assume a description edit
under an unchanged name always triggers invalidation.

The `jco` wrapper works with the currently available catalog and its loaded,
announced, deferred and withdrawn state. It refreshes MCP clients when possible,
can wait for pending servers, and can redial matching failed servers. A
no-match result can therefore mean a connector is still unavailable, not that
the underlying capability does not exist. Already-loaded definitions may be
reported as already available instead of loaded a second time.

### Conditional schema budgeting

**Recovered:** `wTn` is an optional budget pass after ranking. It runs only
when a room object is supplied and a dynamic fraction is a number in `(0, 1]`.
The fallback configuration value at this call site is `0`, which disables
this pass. Therefore the existence of this code is not proof that it is
enabled for every account.

For each candidate definition, the estimator `s0r` uses:

```text
estimated_tokens = ceil((UTF8_bytes(serialized_schema)
                        + UTF8_bytes(description)) / 2.5)
available = max(0, api_limit - max(parent_usage, held_context) - claimed_context)
result_budget = min(floor(api_limit * configured_fraction), available)
```

The first definition contributing tokens may consume all `available` room.
Subsequent definitions must fit the remaining `result_budget`. Accepted
estimates are claimed against the shared room object. Already-loaded tools
are separated from tools individually larger than the API limit and those
that simply do not fit the current result. The wrapper communicates these
different reasons in additional messages.

This is an estimate based on bytes, not exact tokenization. Search ranking
and schema admission are two different steps: a highly relevant tool can
be omitted because its definition does not fit.

On success, the local tool returns standard `tool_result` content containing
`tool_reference` blocks. This makes the selected definitions available to
the main model. It does not approve a subsequent invocation. Catalog visibility
should be restricted before retrieval, and the resolved tool call still needs
the permission gate.

### Hosted search is a separate contract

**Documented:** the public hosted regex and BM25 tools search deferred
definitions supplied in the request's `tools` list. References in the retained
conversation let the API expand the corresponding definitions into model
context. Custom client search can also return `tool_reference` blocks, but
the referenced full definition must already have been supplied to the API.

Neither this public contract nor the native ranker recovers a hidden neural
tool-search model. The schemas, catalog lifecycle and context-loading behavior
are the reusable parts relevant to this project.

Tool-search evidence: `MS` at 413,822, `$Es` at 414,303, `qNt` at 414,790 and
the description-cache `maybeInvalidate` method at 413,655 in
`chunk-187gn6d6.js`; `wTn` at 1,956,559, `s0r` at 1,957,340 and `jco` at
1,959,927 in `chunk-579w43z0.js`.

## Advisor: a larger view, with private server processing

**Recovered:** the client checks feature/provider availability and compatible
model ordering, then adds an `advisor_20260301` entry to the main request's
tool declarations with a selected model and sometimes `defer_loading`.
The inspected declaration does not specify `max_uses`, `max_tokens` or
advisor caching. A server refusal can disable the declaration for a host,
conversation or process and cause a retry without it.

**Documented:** the advisor sees the executor transcript, including system
instructions, tool definitions, prior calls/results and the current generated
text, under a separate advisor system prompt. The executor signals when to
ask; it does not supply a chosen text prompt as the advisor tool's input.
This is the **current executor context**. It is not evidence that the server
restores conversation turns already removed or replaced by a compaction
summary on the client.

The advisor has no tools and performs no independent context management.
Advice returns to the executor, which continues generating. Public options
allow usage/output limits and optional ephemeral advisor caching; that cache
is another distinct surface, not persistent user memory.

The API supports plaintext and opaque encrypted advisor results. Preserve
opaque blocks verbatim when resuming; their existence does not provide a
readable classifier label or disclose the advisor's private prompt. Failure
results can allow the executor to continue without advice. Consequently,
advisor is not the application-enforced authorization boundary for a dangerous
tool call.

Advisor evidence: `Enn` at 64,874, `dx` at 64,998 and `IVe` at 66,454 in
`chunk-187gn6d6.js`; `Iwn` at 1,863,976, `Mbn` at 1,892,569 and the request
declaration at 3,068,416 in `chunk-579w43z0.js`.

## Public documentation and limits

- [Hosted tool search](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)
- [Claude Code MCP tool search](https://code.claude.com/docs/en/mcp#scale-with-mcp-tool-search)
- [Agent SDK tool search](https://code.claude.com/docs/en/agent-sdk/tool-search)
- [Advisor API](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)
- [Claude Code advisor](https://code.claude.com/docs/en/advisor)
- [Auto-mode configuration](https://code.claude.com/docs/en/auto-mode-config)

Documentation was captured during the November 12, 2026 investigation;
client-source anchors are pinned independently to version 2.1.323. These
findings explain observable client contracts. They do not measure live
retrieval quality, classifier accuracy, provider entitlement or private
server behavior.
