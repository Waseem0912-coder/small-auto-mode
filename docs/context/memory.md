# Memory, context lifetime, and compaction

This map covers the client-side code recovered from Claude Code **2.1.323** and
the official documentation captured during the investigation. It separates the
executor's working context from the narrower context submitted to auto mode.
There is no single memory buffer shared by all of these mechanisms.

**Evidence labels:** **Recovered** means a branch or data dependency was read in
the pinned client. **Documented** means the linked official documentation makes
the claim. **Reference design** means a deliberate choice in this project's
original implementation. Static inspection does not establish which remotely
configured branches are enabled for a particular account.

All source offsets below are zero-based **module byte offsets**, measured in the
original extracted bytes, not reformatted source lines. Function offsets point
to `function`, excluding a preceding `async`. The full binary and module hashes
are recorded in [evidence.json](evidence.json).

## The distinct stores

| Store or view | Contents | Lifetime and consumer | Authorization meaning |
| --- | --- | --- | --- |
| Persistent instruction files | Managed/user/project/local instructions, rules, expanded imports | Disk or configured storage; loaded into executor context | Context expressing instructions, not a replacement for enforced permission settings |
| Auto-memory index and topic files | Model-maintained notes useful across sessions | Project or configured memory store; index eagerly loaded, topics read as needed | Reference information; not automatically a fresh user approval |
| Executor conversation | User turns, assistant actions, results, attachments, reminders, summaries | In-memory working conversation and persisted transcript | Contains mixed-trust information |
| Cached instruction snapshot | Formatted instruction content from a completed user-context build | Session/context cache; later read by `_Zr` | An input to the classifier, with explicit limits on what counts as authorization |
| Classifier projection | Selected turns/actions and validated contextual facts | Constructed for the action under review | Preserves source distinctions; ordinary tool output is not promoted to user intent |
| Compaction summary | Model-written description of earlier work plus preserved recent messages when applicable | Replaces part or all of active history | Lossy derived context, even when the summarizer was instructed to preserve constraints |
| Provider prompt cache | Reusable prefix computation for matching requests | Provider-controlled TTL/cache semantics | A performance mechanism, not long-term memory or a permission grant |
| Tool discovery/catalog cache | Tool names, definitions, connection/discovery state | Host/session cache; some discovery state carried across compact | Describes capabilities; discovering a tool does not authorize it |

The [projection map](projection.md) explains what reaches the classifier. The
[boundary map](boundaries.md) covers ToolSearch, advisor, and server safeguards.

## Persistent instruction discovery

**Recovered.** The eager loader `vRr` constructs a typed list of instruction
records before formatting them. The main local-file path is:

```text
_E: memoized eager-load request
  -> vRr: enumerate applicable sources and permitted paths
     -> e6: read one instruction file and recursively expand imports
        -> Kot: bounded regular-file / storage read
        -> zot: frontmatter, comments, imports, AutoMem processing
     -> aRe: enumerate rules, selecting scoped or unscoped rules
  -> uPe / cPe: feature- and content-dependent filtering
  -> Trt: format the selected instruction records
```

The recovered eager-load order includes managed instructions and managed rules,
user instructions and unscoped user rules, then ancestor-to-working-directory
project/local instruction sources and unscoped project rules. It can append
instruction sources supplied by other integration paths, additional directories,
and the auto-memory index. Managed settings can also supply inline instruction
content. This is concatenation of applicable records, rather than a simple
last-file-wins configuration merge.

The directory walk builds the ancestor list in root-to-leaf order. Within a
directory the ordinary project files precede `CLAUDE.local.md`. The code has
separate treatment for a worktree's main repository, project/local settings
availability, exclusions, approved external imports, and restricted reads.
Consequently, "read every CLAUDE.md up to `/`" is not a faithful implementation
of its filesystem boundary rules.

**Documented.** [Memory documentation][memory] also describes direct `AGENTS.md`
support, controlled by the project-instructions setting and compatibility
conditions. The ordinary CLAUDE.md loader above is verified; this map does not
claim to have reproduced every AGENTS.md selection or integration branch.

### Reads, imports, and limits

**Recovered.** `Kot` enforces a **4,194,304-byte** file-read ceiling and skips
nonregular or oversized files instead of loading their first 4 MiB. A storage
backend path requests at most the ceiling plus one byte and checks reported
total size. Restricted-read paths can return no content when the path is
unsettled, denied, or outside allowed locations. Missing files are ordinary
absence; other read failures have separate diagnostics.

`e6` tracks processed spellings/canonical paths, rejects unsuitable paths,
applies exclusions, and records parent relationships for imports. With the root
call at depth zero and a stop condition at depth five, at most **four import
hops** are admitted. External import eligibility depends on scope and session
state. Imports retain the originating instruction type and can inherit an
unverified marker.

`uRr` parses imports outside Markdown code spans and fenced code, resolves them
relative to the importing file, and handles escaped spaces. `zot` separates
frontmatter and strips applicable HTML comments before constructing the loaded
record. These transformations are separate from the content a normal Read tool
would show when explicitly opening the same file.

| Limit | Recovered enforcement | Important distinction |
| --- | --- | --- |
| Eager instruction file | 4 MiB, whole-file skip above limit | Not a recommended instruction length and not a classifier token budget |
| Import recursion | Root depth 0; stops at depth 5 | Four additional hops |
| Lazy nested instruction | Model/window-dependent character cap | Can return a prefix plus an instruction to read the remainder |
| Auto-memory index | First 200 lines and at most 25,000 JavaScript string units before warning text | Not the same as 25,000 UTF-8 bytes for non-ASCII text |
| Classifier instruction wrapper `_Zr` | No independent length cap observed in this wrapper | Upstream limits and downstream request limits still apply |

**Recovered.** Nested instructions are materialized by `H5n` when applicable
files are used. It avoids repeat announcements using read state and previously
announced content. An oversized non-managed record is shortened with `jao`,
which prefers a newline boundary and adds guidance to Read the rest. `oQe`
computes the base cap as the greater of 40,000 characters or a model-dependent
5% context-window estimate. Do not hard-code every model to 40,000.

**Documented.** Current [memory documentation][memory] gives examples of 40,000
characters for a 200K window and 150,000 or 200,000 for certain 1M models. These
are documentation examples; the recovered formula depends on model/window
helpers and configuration. Root instruction files and lazy nested files do not
share the same truncation behavior.

Rules with `paths:` frontmatter are selected against matching paths. Unscoped
rules join eager context. `lPe` performs scoped matching; `Nmo` and `dhn` load
appropriate project/user/managed rule sources. Lazy nested instructions and
scoped rules become conversation material and need to be loaded again after
that part of the conversation is compacted away.

## Auto memory is file-backed, with additional hosted branches

**Documented.** The ordinary local store is
`~/.claude/projects/<project>/memory/`. The project key normally derives from the
repository, allowing worktrees to share a memory directory. Configuration can
change the location. `MEMORY.md` is the startup index; other Markdown topic files
are read through tools when needed. The main conversation's auto memory is not
automatically supplied to every subagent. A subagent can have its own memory;
forking the conversation is a separate inheritance path. See [memory][memory]
and [subagent memory][subagent-memory].

**Recovered.** `vRr` has an AutoMem branch gated by memory availability and
restricted-read checks. It warms canonical repository state, obtains the index
path, and reads the index or uses an explicitly supplied index value. It does
not recursively concatenate every topic file into eager context. `zot` runs
AutoMem content through `HDr` and text sanitation. In some memory modes `uPe`
filters AutoMem records from the conventional instruction route; other memory
mechanisms serve the information instead.

`HDr` first trims the index. It keeps at most 200 lines, then shortens overlong
content to a boundary at or below 25,000 string units, and appends a warning
that content was omitted. A subtle implementation detail matters for replication:
the helper called `g6e` names its measure `byteCount` but calculates it with
JavaScript `.length`. The pinned implementation therefore measures UTF-16 code
units at this point. The official page describes a 25KB limit; those descriptions
agree for ordinary ASCII, but are not an exact byte-level specification for all
Unicode input. The appended warning can itself take the final output beyond the
content cap.

The client also contains account/team memory, connected stores, memory-service
indices, and a selector state with available memories, hydrated values, and
conversation state. These are not all equivalent to local `MEMORY.md`.
`SX` clears a memory selector's per-directory state and usage. This investigation
has not recovered a complete server-side memory retrieval/ranking algorithm or
its private model weights.

### Memory withdrawal changes existing history

**Recovered.** Before classifier projection, `byt` calls `lin`, which wraps
`EMs`. This is a **memory redaction step**, not a generic compact-to-last-N-turns
operation.

`EMs` looks for an account-memory removal boundary represented by a null
`cowork_memory_context` attachment. With the global removal flag enabled it can
apply over the whole prior history instead. Before the effective boundary it:

1. Removes matching memory-context/recall attachments.
2. Recognizes memory-tool calls through a tool-name/context predicate and masks
   their content-bearing inputs.
3. Replaces associated result content with a removal marker when applicable.
4. Handles memory-paused denial results separately, and retains the boundary
   record itself.

It also returns an epoch when modifications were made, permitting downstream
code to distinguish rewritten context. It does not erase arbitrary non-memory
conversation text or prove all semantic paraphrases of a withdrawn memory have
been forgotten. Treating any role-labeled transcript as an untouched historical
truth would miss this intentional rewriting.

## The exact instruction-cache path into the classifier

**Recovered.** The classifier does not call the filesystem loader itself:

```mermaid
flowchart LR
    A[Applicable instruction records] --> B[rAr user-context build]
    B --> C[uPe / cPe / Trt]
    C --> D[Context and instruction integration hook]
    D --> E[zM newest completed build]
    E --> F[TJn cachedClaudeMdContent]
    F --> G[joi accessor]
    G --> H[_Zr wrapper and escaping]
    H --> I[Classifier request]
```

`rAr` builds the executor's user-context blocks, including the instruction
snapshot. It invokes an integration hook that can modify context blocks or
instruction-file records; the classifier snapshot is taken from the resulting
`claudeMd` block. The snapshot can include AutoMem in modes where it survives
the earlier filter. It should not be described as only the text of one file
literally named `CLAUDE.md`.

`zM` tracks build ordinals. A completed build only updates the shared classifier
snapshot if its ordinal is newer, avoiding an older asynchronous build replacing
newer state. There is also retry/backoff behavior for certain project-context
read failures, and refresh/invalidation helpers. `TJn` stores the value; `joi`
returns the active context/session value.

`_Zr` returns no instruction message when this snapshot is null. Otherwise it
sanitizes/escapes the snapshot and wraps it as a separately cache-marked user
message. The wrapper tells the reviewer to use it as environment/intent context;
specific authorization for the same action/target can matter, while generic
encouragement to be autonomous is not authorization. See
[request assembly](request-assembly.md) for the stable/dynamic block split.

This cache is a client-side snapshot. It is distinct from provider prompt
caching. The existence of a cached string neither guarantees a provider cache
hit nor proves that a file edited moments ago is already represented. Hosts
integrating this project should make the snapshot's revision and origin explicit.

## Compaction: summarize, retain, and reconstruct

**Recovered.** The client has full, reactive, partial, idle, and precomputed
compaction paths. `tmo` is the full conversation path; `mLn` is a reactive path
that works with conversation groups and retained messages. This map follows
their shared concepts without claiming one universal algorithm for every mode.

```text
model/window pressure, manual command, idle trigger, or classifier overflow
  -> choose compaction path / check failure breakers
  -> PreCompact hook (may block or add instructions)
  -> construct summarization request
  -> hosted summary call, possibly sharing the executor prefix cache
  -> validate text / summary shape and handle retryable errors
  -> create compact boundary and summary records
  -> retain selected recent messages when that path supports it
  -> reconstruct file, plan, skill, task, tool-discovery, and hook context
  -> invalidate relevant caches and load refreshed instruction context
```

### What the summarizer is asked to preserve

**Recovered.** The summary request asks for ongoing user intent, important
technical work, errors, pending tasks, and current next steps. The constraint
instruction represented by `Yut` requires user-stated security constraints to be
retained verbatim. `_de` adds this requirement even when a configurable summary
prompt does not already contain it. It also includes provenance guidance against
counting assistant text formatted as a user message as actual user instruction.
Some variants explicitly distinguish the system's summarization request from a
user task.

This is **prompt guidance**, not a demonstrated deterministic preservation
guarantee. The inspected validation checks text/error/summary structure; it does
not compare every prior security constraint with the generated summary. A small
guard trained only on summaries would inherit any summarization omissions.

**Reference design.** The local reference carries current host-owned constraints
separately and refuses to construct a usable packet when mandatory context does
not fit. That is an original, inspectable safeguard; it is not a claim that the
native compactor maintains the same deterministic constraint store.

### Summarizer request and recovery

**Recovered.** `DNn` first attempts a cache-sharing fork when enabled, with a
single summarization turn and tool use rejected by the summary path. It uses a
hosted model request, not a local string compressor. It can fall back to another
request path/model under specific availability or refusal conditions.

The full path handles prompt-too-long responses with bounded retries. `xde`
operates on message groups, dropping enough early groups for an estimated gap
or a default fraction while retaining at least one group. It can insert an
explicit truncation marker. `Rz` substitutes image/document placeholders where
that recovery path strips media. Separate more aggressive helper `d3r` removes
thinking-like blocks and shortens tool-input/result strings; it should not be
mistaken for the normal context given to every classification.

Reactive compaction can preserve recent groups, leave out large tool results,
or summarize more of the tail as pressure changes. `cct` records preserved UUIDs
and an anchor/segment in compact metadata. This matters when reconstructing a
session: "everything before the newest compact marker is discarded" is not
correct for all compacted transcripts.

### What gets restored after compaction

**Recovered and documented.** The following behaviors are visible in restoration
helpers and described in [the context-window guide][context-window]:

| Context | Restoration behavior |
| --- | --- |
| Root instructions and unscoped rules | Relevant caches invalidated; eager instruction sources rebuilt/re-read |
| Auto-memory index | Re-enters through the applicable memory-loading route |
| Nested instructions and scoped rules | Reload when their triggering paths are used again |
| Recent files | `c3r` considers up to five recent eligible files, newest timestamp first; re-reads with a 5,000-token per-file limit and a separate aggregate attachment budget |
| Plan | `f3r` restores a plan-file reference and content when available |
| Invoked skills | `p3r` processes newest first, shortens to 5,000 tokens per skill, and limits total included skill bodies to 25,000 tokens |
| Background agents / shell work | `m3r` and `g3r` add applicable task-status reminders; compaction does not itself restart those tasks |
| Tools already discovered | Discovery names can be carried in compact metadata and used while reconstructing declarations |
| Hooks | The compact-source SessionStart hook runs where enabled; its results join the rebuilt context |

The full `tmo` path clears the file-read state and calls `SX` to reset its memory
selector before reconstructing attachments. `FHe` performs post-compaction
cleanup including instruction/user-context invalidation for applicable main
session paths. Other state such as tool declarations, API beta state, and
precomputed work has its own reset rules.

**Documented.** An oversized recent file can be restored as a reference rather
than its full contents. The built-in prompt, output style, and skills catalog
continue through their own request construction paths. Hook output previously
in conversation is summarized; fresh compact-source hook output is newly
injected. A summary alone therefore is not the whole post-compaction request.

## Classifier overflow can trigger executor compaction

**Recovered.** The auto-mode classifier has request-size constraints separate
from the executor's selected context window. The executor can still have room
while the classifier cannot review the projected request.

`A3r` checks pending classifier-overflow state, including whether it is stale
because the context epoch changed or auto mode was left. The automatic
compaction controller can then take an overflow-driven path. Successful
recovery through `KNn` adds a reminder via `MNn` identifying prior tool calls
that were not executed and can be reissued for review if still needed.

This does **not** mean an unreviewed call is silently executed after compacting.
It must be submitted for a later review. Compaction can be disabled, blocked by a
hook, skipped by a rapid-refill breaker, interrupted, or fail to produce a usable
summary. These cases are recorded distinctly. Exact outer permission behavior
also depends on interactive/noninteractive mode, server/local classifier path,
and specialized handoff policies; see [boundaries](boundaries.md).

## What is implemented here, and what remains unknown

The original reference implementation takes **already normalized, host-owned
records**: events, loaded instruction/memory context, summaries, current host
constraints, and the proposed call. It exposes projection decisions and packet
assembly. It does not crawl a user's home directory, execute hooks, synthesize
summaries, call the Claude classifier, or emulate every memory service branch.

For an independent implementation, the recoverable structure is useful:

1. Load context under explicit filesystem/source boundaries.
2. Preserve provenance before extracting user intent.
3. Keep persistent notes, summaries, and current permissions distinguishable.
4. Version or invalidate context after memory withdrawal and compaction.
5. Audit what was omitted, transformed, or retained for classification.
6. Treat unavailable mandatory context as an unavailable review, not a safe label.

Still unproven are complete fidelity across dynamic feature combinations,
server-side memory/ranking internals, actual summary quality, and the classifier's
accuracy on compacted versus original sessions. No Claude-generated training
dataset, trained replacement model, or evaluation of those model behaviors was
created by this source-mapping work.

## Source locator index

Unless specified otherwise, the module is `chunk-579w43z0.js`.

| Symbol / marker | Module byte offset | Evidence used here |
| --- | ---: | --- |
| `jao` | 131814 | Prefix truncation and Read-rest note |
| `oQe` | 1550789 | Model-dependent lazy instruction budget |
| `Kot` | 1554253 | Bounded file/storage read |
| `e6` | 1556942 | Recursive imports and path/type filtering |
| `aRe` | 1558026 | Rules discovery and scoped selection |
| `_E` | 1562549 | Memoized instruction load |
| `vRr` | 1563770 | Eager source ordering and AutoMem branch |
| `PLn` | 1569040 | Load invalidation and hook refresh reason |
| `uPe` / `cPe` | 1570131 / 1570580 | Snapshot filtering |
| `zM` / `rAr` | 1580192 / 1582555 | Context build and newest snapshot publication |
| `tA` | 1585037 | User-context refresh |
| `SX` | 1940199 | Memory selector reset |
| `Yut` / `_de` | 2413806 / 2425291 | Constraint-preservation request and provenance guidance |
| `mLn` | 2442339 | Reactive compaction path |
| `Rz` / `d3r` / `xde` | 2767443 / 2768963 / 2770019 | Recovery transformations |
| `MNn` / `cct` | 2771208 / 2772059 | Overflow reminder and preserved UUID metadata |
| `tmo` / `DNn` | 2773436 / 2786396 | Full compaction and hosted summarizer request |
| `cLe` | 2795601 | Restoration coordinator and compact hooks |
| `c3r` / `f3r` / `p3r` | 2797728 / 2798316 / 2798481 | File / plan / skill restoration |
| `m3r` / `g3r` | 2800872 / 2801535 | Background task reminders |
| `A3r` / `KNn` | 2816098 / 2816536 | Classifier overflow freshness/recovery |
| `FHe` | 2841783 | Post-compaction invalidation |
| `_Zr` | 3305988 | Classifier's cached instruction wrapper |
| `H5n` | 3783872 | Lazy instruction announcement and truncation |
| `TJn` / `joi` in `chunk-s67bjq59.js` | 124605 / 124716 | Classifier snapshot storage/access |
| `HDr` in `chunk-2rhdc6tt.js` | 134017 | Memory-index truncation |
| `EMs` / `lin` in `chunk-mq1jfabw.js` | 3982 / 6681 | Account-memory history redaction |

[memory]: https://code.claude.com/docs/en/memory
[context-window]: https://code.claude.com/docs/en/context-window
[subagent-memory]: https://code.claude.com/docs/en/sub-agents#enable-persistent-memory
