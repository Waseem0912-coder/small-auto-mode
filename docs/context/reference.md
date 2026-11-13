# Executable context reference

[`context.py`](../../src/small_auto_mode/context.py) is an original, deterministic
packet builder over a normalized **host-owned** event stream. It turns selected
history, an instruction snapshot, host facts, policy and the exact candidate call
into auditable JSON. It implements a supported subset of the concepts in
[projection](projection.md), [memory](memory.md), and
[request assembly](request-assembly.md).

It is not a Claude transcript decoder or a copy of the native request format.
It does not authenticate a user, discover or read memory files, redact account
memory, generate summaries, run inference, execute a tool, or authorize an action.
Those boundaries remain explicit rather than being simulated by trusted-looking
strings.

## Run it

From an installed checkout:

```sh
small-auto-mode context-build --input examples/context-input.json
```

The same interface is available from Python:

```python
from small_auto_mode.context import build_packet
from small_auto_mode.jev import load_json

packet = build_packet(load_json("examples/context-input.json"))
if not packet["ready"]:
    print("Needs review:", packet["errors"])
else:
    print(packet["decision"])  # unassessed, never allow
    print(packet["serialized"])
    print(packet["audit"])
```

The example is synthetic and contains an injected instruction in a tool result.
The projection excludes that result text and assistant speculation while retaining
the user restriction, host facts, a marked summary, and the unchanged candidate.
It is a boundary example, not a labeled training sample or a safety benchmark.

## Trust contract

The caller must be trusted host code, outside the proposing model's control.
All registry entries, attestations, environment facts, retained constraints,
policy and snapshot metadata are assertions by that caller. In particular,
`attestations.human` is **not** a cryptographic proof. Passing JSON produced by
an untrusted model directly to this function would allow it to attest itself.

Before constructing this input, the host must validate event origin and session
ownership, select the active conversation window, apply applicable account-memory
revocation/redaction, and retain security constraints. An attested summary means
the host knows where the summary came from; it does not certify that the summary
is accurate, complete, or a human instruction.

The host must also bind any later decision to the current principal, session,
exact action, policy and environment. The digests below detect input differences;
they are neither signatures nor protection against state changing after review.

## Input schema: version 1

The complete example is [context-input.json](../../examples/context-input.json).
Unknown fields are rejected at each defined schema boundary. Tool arguments and
the `session.environment` object deliberately accept arbitrary JSON keys because
their schemas belong to the host's tools and environment adapter.

| Top-level field | Required shape and meaning |
| --- | --- |
| `schema_version` | Integer `1`; a Boolean is not accepted as an integer |
| `events` | Ordered list of events from the already-selected active window |
| `attestations` | Exactly `human`, `answers`, `summaries`, `host_context`; each is a list of event IDs validated by the host |
| `registry` | List of unique tool definitions described below |
| `candidate` | `{id, name, arguments}`; nonempty ID/name and an object of exact arguments |
| `instruction_snapshot` | `null`, or `{id, text, sources}` where sources is a list of `{path, kind}` records |
| `stable_policy` | `{version, rules}` with a nonempty version and a list of nonempty rule strings |
| `session` | `{environment, constraints}`; an object of host facts and a list of retained constraint strings |
| `preprocessing` | `{account_memory, window}`; accepted states described below |
| `options` | Optional object of budgets and outcome settings |

Every event has a unique, nonempty `id` and a `kind`. Call IDs are a separate
namespace; historical calls must be unique and must not reuse the candidate ID.
Event order matters. An answer must follow its question; host context must follow
both its call and a result that occurred after that call.

| Event `kind` | Other fields | Treatment |
| --- | --- | --- |
| `human` | `text` | Requires membership in `attestations.human`; retained with `origin: human` |
| `summary` | `text` | Requires membership in `attestations.summaries`; retained with `origin: assistant_summary` |
| `assistant_text` | `text` | Dropped; this version does not implement the native optional prose path |
| `internal` | `text` | Dropped as internal scaffolding |
| `tool_use` | `call: {id, name, arguments}` | Matched to registry, retained/adapted or explicitly omitted |
| `tool_result` | `call_id`, `text`, `is_error`; optional nonempty `denial_kind` | Ordinary text excluded; an attested answer or optional coarse outcome may be retained |
| `host_context` | `call_id`, `text`, `freshness` | Requires host attestation, prior call/result correlation and `freshness` of `current` or `snapshot` |

Text for a retained human, summary, answer or host-context event cannot be blank.
Ordinary result bodies can be empty. `is_error` must be Boolean. Multiple results
for the same call ID are rejected. Unrecognized event kinds require review; a
project-specific relay or forwarded-user envelope needs a separate validated
adapter before it can enter this schema.

Each attestation ID must exist and match its declared event kind. Repeated IDs in
an attestation list are rejected. A field such as `authenticated: true` placed
inside an event is an unknown field, not a way to bypass attestation validation.

## Tool registry and result correlation

Each registry entry has a unique `name` and may have:

| Field | Default | Behavior |
| --- | --- | --- |
| `history_mode` | `include` | `omit` excludes ordinary historical calls; does not omit the candidate |
| `argument_fields` | Absent: all fields | A list of top-level historical argument keys to retain; omitted keys are named in the audit |
| `question_tool` | `false` | Marks a host-controlled tool whose successful, explicitly attested result can be a human answer |

A historical adapter never changes the candidate. All candidate argument fields,
including descriptions and nested values, remain in the packet and its candidate
digest. The registry does not validate shell syntax, filesystem paths, recipients,
or the tool's full argument schema. The host must do that separately.

Attested answers require a previously seen registered question tool, a non-error
result, no denial marker, and nonblank answer text. An ordinary successful result
does not become an answer. A matching question call is retained even if its
registry entry normally omits history, so the answer keeps its question context.

Similarly, an attested host-context event keeps its associated historical call.
The fact must follow a result correlated to that prior call. A result that arrived
before the call cannot satisfy this condition. Freshness remains a host assertion;
the builder does not check timestamps or refresh the fact.

With `include_outcomes: true`, results for included calls can produce only
`success`, `error`, or `denied` outcomes. Their arbitrary text is still excluded.
Outcomes for omitted calls are not emitted. Unattested ordinary results with no
prior call are dropped and cannot establish host-context correlation or user
authorization. An attested orphan answer is an error.

## Memory, compaction and limits

`instruction_snapshot` is the loaded text the host actually selected. The builder
keeps its source metadata but does not invent a project/user/auto-memory inclusion
rule or open the paths listed there. `null` explicitly represents no snapshot.
Generic instructions in a snapshot do not create a fresh human event.

`preprocessing.account_memory` must be `absent` or `redacted`. Here `redacted`
means the host has completed its applicable sanitation, not that this builder
inspected or removed every memory item. This is a declared prerequisite rather
than a reimplementation of native `lin`/`EMs` revocation handling.

`preprocessing.window` must be `full` or `compacted`. A compacted window requires
at least one attested summary. All packets also require at least one attested
human event; a summary alone cannot satisfy the user-intent requirement. The
builder does not check whether the summary actually preserves every old
restriction. The host supplies durable restrictions separately in
`session.constraints` and must review missing or uncertain context.

| Limit | Default | Measurement and failure behavior |
| --- | ---: | --- |
| Input document | 1,000,000 bytes, fixed | Canonical ASCII-escaped JSON representation; oversized input returns `ask` |
| Complete inference packet | 128,000 bytes | `options.max_packet_bytes`; overflow returns `ask` without a partial packet |
| Individual host-context string | 2,000 bytes | `options.max_host_context_bytes`; measures serialized string including JSON quotes and escapes |

Configurable budgets must be integers between 1 and 1,000,000. There is no silent
truncation or automatic summarization: the candidate, user intent, constraints and
snapshot are not cut to make a packet fit. These are **reference byte budgets**,
not native token limits. In particular, native host-context truncation uses
JavaScript UTF-16 units; our measured, reject-on-overflow rule is different.

## Output and audit

A successful assembly returns `ready: true`, `decision: "unassessed"`, no errors,
and the following artifacts:

| Output | Contents |
| --- | --- |
| `stable` | Contract name and stable policy |
| `dynamic` | Session facts/constraints, instruction snapshot, projected history and exact candidate |
| `serialized` | Canonical JSON of `{stable, dynamic}` |
| `audit` | Per-event `keep`, `drop`, `transform` or `reject` entries with a reason; adapted history names removed argument keys |
| `candidate_sha256` | Canonical exact candidate, including its ID, name and every argument |
| `stable_sha256` | Stable block only; useful for identifying a reusable policy prefix |
| `packet_sha256` | Actual serialized inference packet |
| `binding_sha256` | Contract plus the entire supplied input, including attestations, registry, preprocessing, options and dropped evidence |
| `packet_bytes` | Byte length of `serialized` |

Serialization sorts keys, escapes non-ASCII/control characters, and encodes
`<`, `>` and `&` as JSON Unicode escapes. JSON decoding recovers the exact values;
there are no raw wrapper tags to spoof in the serialized representation. This is
structural encoding, not a claim that a language model cannot obey an injection
embedded in a JSON string.

Changing a dropped tool-result body can leave `packet_sha256` unchanged while
changing `binding_sha256`. Changing a memory snapshot leaves `stable_sha256`
unchanged but changes the full packet. None of these hashes is a provider cache
instruction, a cryptographic identity attestation, or an authorization token.

Incomplete or invalid input returns `ready: false` and `decision: "ask"`, with
error codes and any accumulated audit. It does **not** return `stable`, `dynamic`,
`serialized` or `packet_sha256` for partial inference. Some failure paths include
diagnostic digests/byte counts; callers must always check `ready` rather than
guessing readiness from field presence. No error path returns `allow`.

## Deliberate differences from the native client

- The input is a small normalized schema. It does not parse native JSONL records,
  project principal rows, relay delivery stamps, forwarded-turn envelopes,
  schedules, voice events, plugin origins or every attachment type.
- Attestations and retained constraints are explicit host inputs. They do not
  reproduce the product's identity and delegation protocols.
- Unknown candidates and unknown historical tools require review. Native
  serialization has empty-string and fallback branches described in the source
  map; this reference intentionally does not inherit those no-review behaviors.
- Registry adapters select top-level history fields only. There is no execution
  of arbitrary tool-specific adapter code, alias normalization or model-generated
  policy. The exact candidate always survives adaptation.
- Assistant prose is always excluded here; the native optional prose mode and
  inherited-prefix handling are not implemented.
- Full IDs, tagged JSON records, explicit source binding and reject-on-overflow
  budgets replace the native compact IDs, wrappers and sanitation details.
- The stable/dynamic separation is conceptual. It is not a wire-compatible
  Anthropic Messages request, and it adds no actual provider cache controls.
- Summary generation, filesystem loading, memory writes, token-window selection,
  native server safeguards, ToolSearch schema budgets and advisor orchestration
  remain outside this module.

The tests in [test_context.py](../../tests/test_context.py) exercise these stated
boundaries, including reordered results, forged answers, missing attestations,
budget overflow, preserved candidate fields and digest changes. They establish
the reference contract, not native parity or model accuracy.

## Integration and continuation

This packet is not automatically fed to `gate.assess`, `LocalClassifier`, or the
current trainer. Those use the separately documented `case` input format. A host
integration must choose one versioned representation and use it consistently for
collection, labeling, training, evaluation and inference. Do not flatten every
record into `user_intent` or silently change the existing training distribution.

The next implementation step is an original trusted adapter from the application's
authenticated event store to this schema, with explicit behavior for unsupported
events and missing constraints. Then build a reviewed, permitted dataset and
measure the complete guard—including host checks and abstentions—on held-out
scenarios. Keep inference in shadow mode until that evidence exists.
