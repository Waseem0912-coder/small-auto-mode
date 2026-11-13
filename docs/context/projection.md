# Transcript projection before classifier review

This is a static map of the client in **Claude Code 2.1.323**, not a claim about every live feature configuration. It describes what the examined JavaScript does; it does not recover model weights or demonstrate that the model obeys each distinction. See [request assembly](request-assembly.md), [memory](memory.md), and the [evidence manifest](evidence.json).

The central observation is that the classifier gets a **purpose-built view of the conversation**, not the executor's whole prompt. Selection depends on the source of a message, relationships between calls and results, and host metadata. A string saying “the user approved” is not, by itself, a user approval.

## Entry points and order

The main wrapper `bHe` prepares both the candidate action and the surrounding context:

```text
host transcript                       tool definitions + aliases
      │                                          │
      ├─ lin / EMs: memory revocation sanitation  │
      │                                          │
      ├─ byt: provenance-aware projection ────────┤
      │        ├─ selected human/task text        │
      │        ├─ marked compaction summaries     │
      │        ├─ selected historical tool calls  │
      │        └─ correlated host/outcome facts   │
      │                                          │
      └─ zZr → rzn → ozn: adapted serialized history
                                                 │
candidate assistant event ── Nms → Ryt → rzn ─────┘
```

`lin` is **not** a last-N-message selector or a compaction summarizer. It wraps the account-memory sanitation routine `EMs`; [memory.md](memory.md) describes its revocation boundary. `byt` handles already-existing compaction-summary events separately. No fixed “last 30 messages” rule appears in this projection.

`bHe` also reads inherited-prefix and subagent flags. Historical tools in the inherited prefix are suppressed, while prose treatment can differ between inherited and current messages. These are caller-supplied boundaries, not a universal numeric context window.

## Message selection matrix

The following describes the ordinary inspected branches. Feature flags and specialized project/delegation paths can change the annotated form.

| Input in the host event stream | Projected behavior | Why the distinction matters |
|---|---|---|
| Ordinary user text, including an unstamped user event | Retained as a human frame; depending on mode, normalized/indented | The outer event wrapper is trusted. This does not prove that arbitrary text arriving from a tool is human-authored. |
| Provenance-marked relay human text | Retained with relay/thread annotations and, where available, validated reply relationships | Delegation and reply-to context are represented rather than inferred solely from words. |
| Meta event with no usable provenance | Invisible | Internal scaffolding is not automatically user intent. |
| Project relay event | Not copied wholesale; recognized source rows may be reconstructed through the principal-source validation path | An arbitrary relay body is not promoted to an owner instruction. |
| Existing compaction summary | Retained as explicitly assistant-written summary text | Reported task context may survive; a reported approval or lifted restriction does not become a new human confirmation. |
| Historical assistant tool call | Retained if enabled and not in the retrieval/discovery exclusion set; adapted using its registered tool definition | The classifier sees selected actions and their meaningful arguments. |
| Historical assistant prose | Normally omitted; optional prior-assistant-context mode retains selected preceding prose | “The assistant explained why this is safe” is not universally part of the native input. |
| Ordinary tool-result body | Omitted | External/file/tool text is not copied wholesale into the classifier's intent channel. |
| Successful result for a previously seen `AskUserQuestion` call | Converted into an explicitly marked user-answer entry | The question-tool channel is a narrow, correlated exception to ordinary-result filtering. |
| Failed `AskUserQuestion` result | Not converted into an answer | A failed question is not approval. |
| Recognized principal-source tool result | May contribute individually validated principal rows | Validation is performed on the structured source, not on an arbitrary result's claimed identity. |
| Optional tool outcome metadata | Coarse outcome entry linked to the included call | Success/error/interruption/denial metadata is distinct from tool-output text. |
| Host classifier context | Bounded host-context entry linked to an included call | This comes from privileged host fields, not an inline assertion by tool content. |
| Validated attached-machine result marker | Result-origin entry linked to an included call | Origin of private data can matter even when the result body is omitted. |
| Queued task, schedule, peer agent, plugin, observer, channel, or voice input | Origin-dependent non-user formatting, with special cases | Being stored in a user-shaped transport message does not make every event a human request. |
| Omitted-turn sentinel | Explicit omission marker | Missing history is represented as missing, not silently assumed harmless. |

The frame classifier is `iY` in `chunk-qxb2gr8e.js`. It prioritizes meta filtering, existing summary status, special relay handling, and recognized human origins before falling back to a non-user frame. It explicitly distinguishes task notifications, coordinator/channel/peer events, observers, plugins, voice calls, and unclassified origins.

## Historical tool selection and adaptation

The exact historical exclusion set in `byt` resolves to:

```text
Read
Grep
Glob
LSP
ToolSearch
ListMcpResourcesTool
ReadMcpResourceTool
ReadMcpResourceDirTool
```

An attached-host feature branch can retain one of these calls when its input identifies that host. The set is about historical projection: **the candidate action is serialized separately**. Do not use this list as an unconditional authorization allowlist or as a rule to discard the candidate under review.

`QFe` builds a map from registered names and aliases to tool definitions. `rzn` then resolves a call against that map. Unknown tools serialize to the empty string. For a registered tool, `ozn` calls its `toAutoClassifierInput` adapter:

1. A non-null adapter result is used.
2. A null/undefined result falls back to serialized raw arguments.
3. An adapter exception also falls back to serialized raw arguments; the logging path records the failure without logging the complete error body here.
4. An empty-string adapter result suppresses that serialized entry.
5. Some configuration branches normalize the adapter's string output further.

This is an interface contract, not evidence that every tool uses the same field selection. Reimplementations must define adapters for their own tools. In particular, security-relevant arguments must not disappear merely because a UI-oriented description omitted them.

`Nms` serializes the candidate assistant content through `Ryt`/`rzn`. If the resulting candidate string is empty, `bHe` returns its no-review result without making the classifier request. A defensive independent implementation may instead reject an unknown or empty candidate. That is a deliberate policy choice, not an exact copy of this native branch.

## Correlated exceptions to result filtering

`byt` remembers full `AskUserQuestion` call IDs while traversing assistant events. A later non-error tool result matching such an ID can become a marked answer. There is a separate special case for the tool's “more questions” response: it is rewritten as a request for another question round, explicitly not an answer. Generic success from an unrelated tool has no such conversion.

Before the main projection pass, the code examines host user events containing exactly one `tool_result`. It gathers:

- `classifierMetaLines`, used as serialized metadata preceding the matching call;
- `classifierBoundary`, used to create a serialization/cache block boundary;
- nonempty `hostClassifierContext`, attached at the matching result position;
- a live-context classification based on a separate freshness check and feature flag.

For result-position host context and outcomes, the later pass requires a tracked, included historical call. The metadata lookup uses full call IDs. Emitted IDs are shortened separately, so those shortened labels should not be treated as globally unique authorization identifiers.

Host context is capped with `Z(context, T1)`, where `T1 = 2000`. `Z` limits JavaScript UTF-16 code units, avoids splitting a trailing high surrogate, and normalizes malformed surrogate data. It is not a 2,000-token budget. The live and ordinary forms serialize under separate keys, `host_context_live` and `host_context`.

When outcome visibility is enabled, the normal projection constructs outcome entries with `resultText` explicitly undefined. The serializer can handle a `resultText` field, but that capability does **not** show that this projection copies all ordinary tool outputs. The normal outcome helper distinguishes `ok`, `error`, some interruptions, and denial categories.

Attached-machine result metadata is recognized through a separate `tool_host_result_lines` attachment. Its host and disposition must pass the appropriate validators. [Boundaries](boundaries.md) covers the freshness, host, and server distinctions.

## Principal, relay, and reply provenance

The project-source path is more involved than a role conversion:

1. `Kgt` extracts candidate structured sources, source-read call IDs, and malformed/truncated/member-state observations.
2. `V_o` derives eligible principal rows using the current member-session mode.
3. `Lqi` attempts to associate an eligible reply with a delivered coordinator ask.
4. The projection checks reply relationships across copies. Multiple replies for one ask, multiple ask references for one reply, contradictory row copies, and malformed sources can veto credit.
5. Eligible rows are reconstructed with their source annotations. A recognized ask/reply pair may also contribute the corresponding assistant ask before the human reply.

Additional project modes track delivery state across own-work events, own nudges, compaction, and subsequent human replies. The code examines message IDs, author identity, timestamps, root/edit status, and reply linkage. This is not equivalent to trusting a `from: user` string in an MCP response.

The repository's normalized reference API does not claim to implement all these product-specific source formats or delivery protocols. A host adapter must authenticate and validate provenance before creating a trusted normalized human-answer event. If it cannot, it should preserve the lower-trust origin or require review.

## Assistant prose and inherited history

The default returned by `lmn` is false unless configuration or the environment supplies a value. With prose enabled, `byt` does not simply copy every assistant message: it stores selected trailing prose, emits it before certain subsequent human events, and clears it on other boundaries. `hNe` keeps at most the trailing 2,000 JavaScript UTF-16 code units; its upstream `jLe` ignores API-error, virtual, and designated synthetic-model messages. In the inherited prefix, separate `prefix`/`prose` options apply; current-loop prose is also suppressed for the subagent-loop route.

This matters for dataset design. A dataset made from raw chat transcripts, or one containing every assistant rationale, is a different input distribution from the native default. A dataset with every assistant message removed may also fail to represent a deployment that enables the optional prose path.

## Serialization and delimiter defenses

`rzn` produces line-oriented JSON-like records through the client's JSON helper. Text uses the projected speaker as its key. Calls use an adapted tool-name key; special metadata has its own record shapes.

Several transformations preserve structural distinctions:

- `fW` normalizes CR and alternate newline/control separators, neutralizes reserved transcript/forwarded-turn delimiters, and indents the text.
- `jan` removes Unicode format/default-ignorable code points and neutralizes opening forms of the specified reserved tag using the client's Unicode-aware delimiter helpers.
- `Fbt` applies that treatment to the transcript and forwarded-turn tag names.
- `Gz` escapes U+2028, U+2029, and U+0085 in serialized output.
- `uZr` removes format/default-ignorable characters from tool names; `fZr` additionally protects collisions with reserved record keys such as `user`, `assistant`, `id`, `meta`, `outcome`, and host-context keys.
- `GFe` uses the last six characters of a call ID, replacing characters outside `[A-Za-z0-9_-]` with underscores. This is a compact display association, not a collision-proof identity system.

These measures are evidence of boundary hardening, not proof of immunity to prompt injection. A normalized reference format can use different structural escaping while preserving the same trust distinctions; it must say so rather than claim byte-for-byte native compatibility.

## What this mapping establishes

It establishes local selection, labeling, sanitation, tool adaptation, and serialization logic for the pinned artifact. It does not establish the live flags chosen by a given account, complete behavior of every imported product integration, correctness of hosted classifications, or the internals of the separate server-integrated safeguard. The independent reference code is a supported subset with explicit host requirements, not a drop-in parser for every Claude Code event.

## Source locators

Offsets are zero-based bytes in the extracted module, measured from `function NAME(`, excluding a preceding `async`. Minified names only identify this exact build. The manifest records hashes and binary offsets.

| Module | Symbol | Module byte offset | Relevant behavior |
|---|---|---:|---|
| `chunk-579w43z0.js` | `byt` | 3,283,783 | Projection, result correlation, source handling |
| `chunk-579w43z0.js` | `QFe` | 3,297,014 | Registered-name and alias map |
| `chunk-579w43z0.js` | `ozn` | 3,297,123 | Tool input adaptation and fallback |
| `chunk-579w43z0.js` | `rzn` | 3,298,091 | Record serialization |
| `chunk-579w43z0.js` | `Nms` / `Ryt` | 3,298,994 / 3,299,033 | Candidate serialization |
| `chunk-579w43z0.js` | `zZr` | 3,327,235 | History block assembly |
| `chunk-579w43z0.js` | `bHe` | 3,328,253 | Request preparation |
| `chunk-579w43z0.js` | `GFe` / `Gz` | 3,282,401 / 3,282,626 | Short IDs and separator escaping |
| `chunk-579w43z0.js` | `uZr` / `fZr` | 3,297,546 / 3,297,799 | Tool-name sanitation |
| `chunk-579w43z0.js` | `lmn` | 1,520,662 | Prior-assistant-context configuration |
| `chunk-579w43z0.js` | `hNe` | 2,885,171 | Bounded prior assistant prose |
| `chunk-qxb2gr8e.js` | `iY` | 673,155 | Provenance/frame classifier |
| `chunk-mq1jfabw.js` | `EMs` / `lin` | 3,982 / 6,681 | Account-memory sanitation |
| `chunk-f2w9btq2.js` | `PKe` / `jan` / `Fbt` / `fW` | 425 / 548 / 772 / 831 | Text and delimiter sanitation |

The exact exclusion-set declaration is at main-module byte 3,282,479; its imported constants resolve in the modules recorded by the source artifact. The question-tool name and “more questions” distinction resolve in `chunk-fa3trqmm.js`.
