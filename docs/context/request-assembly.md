# Policy, context, and request assembly

This document maps the **client-requested classifier path in Claude Code 2.1.323**. It complements [projection](projection.md), [memory](memory.md), and [boundaries](boundaries.md). It is a behavioral description with short source locators, not a redistribution of the vendor's full policy prompt.

Context preparation is not one linear stage that finishes before all policy work begins. The client derives policy, trusted session facts, loaded instructions, projected history, and the proposed action from several sources, then joins them into a classification request.

## The assembled request

The inspected `bHe` → `BZr` path produces this conceptual layout:

```text
system blocks
  stable policy and settings-derived rules              [cache boundary]
  dynamic session / project / connector / host rules

messages
  optional loaded CLAUDE.md context                     [cache boundary]
  transcript opening delimiter
  projected historical records                         [cache boundary at final history block]
  candidate-specific facts: repository, git, metadata
  candidate action                                     [cache boundary]
  transcript closing delimiter
  optional keyed forwarded-user-turn envelope
  stage-specific decision instruction
```

That diagram shows content order, not a fixed count of API messages. With ordinary assembly, transcript blocks are grouped in one user message after any leading CLAUDE.md message. A segmented mode places the constituent blocks in individual user messages. The generic provider layer can further normalize the request; this map is the classifier builder's output boundary.

The candidate is **inside** the transcript delimiters in this path. The separately keyed forwarded-user-turn envelope comes after the closing delimiter. Neither should be silently moved when attempting native request comparison.

## Stable policy versus dynamic context

`bZr` builds the first system block from a base policy builder and several rule sources:

| Source | Treatment in the inspected builder |
|---|---|
| Base classifier policy | Constructed locally; transformed for the selected verdict protocol and feature paths |
| Cross-session and provenance rules | Inserted according to the project/relay/host mode |
| Permission template | Constructed using the active permission/tool context and relevant connector/browser conditions |
| User auto-mode rule settings | Allow, soft-deny, hard-deny, and environment lists are inserted unless the caller selects built-in-only context |
| Settings-level deny rules | Extracted separately, deduplicated, and formatted; some source classes and prompt-style rules are excluded by this extractor |

The settings-deny extractor `kZr` ignores the `toolsNarrowing` and `command` source categories, skips entries whose parsed rule content begins with `prompt:`, and deduplicates the remaining strings. That describes this prompt construction step; it does **not** imply that other permission machinery ignores those categories.

The subsequent dynamic system block concatenates available session identity, project/workspace guidance, connector-specific rules, attached-machine guidance, and rules supplied for a reviewed host. In particular:

- `SZr` can add a resolved user identity used by ownership-sensitive policy examples.
- `hZr` describes the active project/forwarded-owner context when enabled.
- `tQi` contributes connector-specific handling only for the identified configured connector prefixes.
- `csn` adds attached-machine guidance when that feature is active.
- `wZr` formats the attached host's hard-deny, soft-deny, allow, and environment rules when supplied.

These enter through application/configuration channels. That is not a universal claim that the application has authenticated every upstream speaker: the attached-host rule wrapper explicitly acknowledges that sender verification for that machine's messages may be incomplete, and distinguishes command rules from attempts to instruct the classifier. Ordinary tool text should not be accepted as a replacement for these channels in an independent host.

## Loaded instructions are a separate message

`_Zr` reads `joi()`, an accessor for the session's cached loaded CLAUDE.md content. A null cache gives no instruction message. Otherwise it wraps and sanitizes the cached text, adds a cache marker, and places it in a leading user message.

The wrapper treats this content as information about environment and intent, with a narrow distinction: an explicit authorization for the **same operation and target** can be relevant; generic instructions to be autonomous or avoid asking are not blanket authorization. This does not mean arbitrary retrieved text is trusted equally with the loaded-instruction channel.

`_Zr` does not itself discover files, read every memory directory, or fetch a learned vector memory. The upstream loader determines the cached content; [memory.md](memory.md) maps that path. The classifier receives the snapshot already selected by the application.

`onlyBuiltInContext` suppresses this leading message and the user's custom auto-mode rule lists in the examined builder. It also suppresses repository/git context collection. It is not equivalent to “send no transcript” or “disable every dynamic host rule.”

## Historical blocks and candidate facts

`zZr` serializes each projected item with `rzn`, tracks user/tool character counts, and builds text blocks. In segmented mode each serialized item becomes a block. Otherwise it accumulates adjacent text, but emits a separate block at marked tool boundaries. `classifierBoundary` and a host-side boundary lookup can cause those splits.

Before appending the candidate, `bHe` can gather additional facts associated with it:

- repository visibility from an imported helper;
- git state from `DGn`, for recognized shell-tool commands and enabled feature conditions;
- host-maintained serialized metadata associated with the candidate call ID.

The git helper does not run for every tool or every command. It recognizes eligible shell inputs, uses the current repository, and obtains porcelain status; depending on the condition it emits a clean marker, counts of staged/modified/untracked files, or bounded porcelain text. Errors and unavailable context yield no git fact. Absence of a fact should not be interpreted as a verified clean repository.

The host fact strings appear after historical records and before the candidate. The wrapper can also retain those strings in its call-ID metadata cache for later history projection.

## Forwarded-user context

The client can collect verified forwarded turns separately from normal transcript projection. `yZr` emits them in a dedicated envelope with a request-specific key. Each turn includes an author category and sometimes a validated timestamp. Its text receives stricter sanitation through `sCo`.

The accompanying boundary instruction says only this exact keyed envelope has the special forwarded-turn standing. Lookalike tags in tool text, transcripts, or other locations do not acquire that standing. The request key is a structural binding within the prompt; it is not evidence of a cryptographic source signature. Eligibility of the rows is established upstream.

This channel and the provenance-marked entries within `byt` serve related but distinct purposes. A normalized implementation should not merge all forwarded messages into ordinary user text and erase their provenance.

## Prompt cache behavior

The inspected code applies ephemeral prompt-cache controls at several boundaries:

| Boundary | Local behavior |
|---|---|
| Stable system-policy block | `cache_control` is attached immediately in `bZr` |
| Loaded CLAUDE.md message | Has its own cache control |
| Final existing history block | Receives transcript cache control before candidate facts are appended |
| Candidate action block | Also receives transcript cache control |
| Dynamic system text and intervening candidate facts | No separate cache control is added at those exact locations by this builder |

`Ste` creates an ephemeral cache-control object. `myt` requests a one-hour TTL when the relevant feature gate allows it; otherwise it leaves the TTL unspecified. A caller asking for a five-minute transcript TTL can override the one-hour setting for transcript/candidate blocks. Do not infer a universal TTL or a measured cache hit rate from those branches.

Cache boundaries are request reuse hints. They do not summarize history, establish source trust, grant permission, or preserve a user's long-term memory by themselves. File-based memory, the session's loaded-instruction cache, prompt caching, and deferred-tool catalog state are separate mechanisms.

## Size accounting and overflow

`bHe` computes character counts for the system string and serialized projected history plus candidate, then estimates tokens with roughly **characters / 4**. It also measures the main-loop transcript separately and uses the larger estimate in deadline selection.

This diagnostic estimate is not an exact tokenizer count or a complete accounting of the final wire request. It is formed before the additional candidate facts are appended and does not include every leading message, delimiter, forwarded envelope, or stage suffix. It should not be copied as a hard model-window admission check.

There is no general “truncate everything to N tokens” operation in this wrapper. Limits elsewhere include individual host facts, loaded memory selection, inherited-turn selection, main-loop compaction, and the provider's actual context window. If the provider reports context overflow, the classifier orchestration returns a blocked/no-verdict result with the overflow status. The outer permission gate has additional handling, including interactive compaction/fallback and specific special cases; [the existing findings](../findings.md) describe those limits.

The reference implementation's explicit budget, protected candidate, and review-required behavior on insufficient context are independent design choices. They should be evaluated as such; they are not evidence of a recovered native token-budget algorithm.

## Two stages share the same prepared context

`BZr` constructs a common content sequence and adds a stage-specific decision suffix. In the inspected ordinary two-stage path, both stages use the selected hosted model. The second-stage messages are rebuilt from the common context; the first stage's generated rationale is not appended as another transcript turn.

The fast stage checks whether a block rule could apply without applying intent-based exceptions. A clean parsed allow can finish early. Otherwise the reasoning stage evaluates the action with the relevant intent/exception analysis. Different verdict protocols and site thresholds are supported. This is model orchestration, not a recovered small local classifier followed by a separate larger model.

The provider receives the prepared system blocks, messages, chosen model, output cap, retry/deadline settings, and protocol options. No local classifier weights were identified in this path. Mapping the request builder therefore does not by itself supply a training dataset or establish the accuracy of a replacement model.

## Reference-code boundary

The independent code should consume a host-owned normalized document and emit inspectable blocks plus an audit of selection decisions. Its supported source types and policy fields are a new public interface. They are not raw Claude Code event schemas, and merely sending a field named `host_context` from an untrusted tool must not confer authority.

The reference can preserve the architecture—separate loaded instructions, typed projected history, host facts, candidate, and stable/dynamic policy—without copying the vendor's private policy text or claiming native byte compatibility. Unsupported product integrations remain explicit gaps.

## Source locators

Offsets refer to the `function NAME(` keyword in the extracted module; hashes and binary addresses are in [evidence.json](evidence.json).

| Module | Symbol | Module byte offset | Role |
|---|---|---:|---|
| `chunk-579w43z0.js` | `bHe` | 3,328,253 | Main preparation, metrics, facts, cache boundaries |
| `chunk-579w43z0.js` | `bZr` | 3,308,459 | Stable policy and dynamic system text |
| `chunk-579w43z0.js` | `_Zr` | 3,305,988 | Loaded-instruction message |
| `chunk-s67bjq59.js` | `joi` | 124,716 | Cached loaded-instruction accessor |
| `chunk-579w43z0.js` | `kZr` | 3,306,596 | Settings deny extraction |
| `chunk-579w43z0.js` | `SZr` | 3,306,822 | Session identity context |
| `chunk-579w43z0.js` | `wZr` | 3,307,109 | Attached host rule formatting |
| `chunk-7vdjs0h2.js` | `tQi` | 1,851 | Connector-specific dynamic rule contribution |
| `chunk-579w43z0.js` | `yZr` | 3,305,390 | Keyed forwarded-turn envelope |
| `chunk-579w43z0.js` | `zZr` | 3,327,235 | Projected history block layout |
| `chunk-579w43z0.js` | `DGn` | 3,224,886 | Candidate git context |
| `chunk-579w43z0.js` | `Ste` / `myt` | 3,025,701 / 3,274,914 | Cache controls and optional TTL |
| `chunk-579w43z0.js` | `BZr` | 3,315,680 | Stage requests and common message construction |
