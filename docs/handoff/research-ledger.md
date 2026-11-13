# Research ledger

This consolidates the on-disk outputs and verified findings from the previous
work streams. It is an edited index, not a claim to preserve hidden reasoning or
an exact transcript of every agent message. The private bundle keeps the actual
saved research files unchanged. Published interpretations remain revisable.

## Artifact inspection and auto mode

- Inspected the official Linux x64 Claude Code 2.1.323 npm artifact using REA
  6.9.0. Retained the original byte ranges and hashes. The standard expansion
  rejected overlapping bytecode accounting; the original contents-only adapter
  extracted 3,237 source/assets totaling 63,760,938 bytes without raising the
  bytecode budget or executing the binary.
- Repeated extraction reproduced the file hashes. The documented policy export
  was run with isolated local configuration and nonessential traffic disabled;
  the original JSON remains private. Its counts were 16 allow, 72 soft-deny,
  1 hard-deny and 21 environment entries.
- Recovered client context/policy assembly, model selection, fast/escalated
  review, Boolean/severity parsers, retries and outer permission handling. The
  selected model is hosted; no neural weights were recovered.
- Nine isolated parser probes passed in the earlier inspection. These exercised
  parsing, not the hosted model or authorization accuracy.

Public outputs: [findings](../findings.md), [request assembly](../context/request-assembly.md),
[evidence](../context/evidence.json). Private originals: `research/auto_docs/`,
`original/extracted/`, `original/auto-mode-defaults.json`, and extraction manifests.

## Context projection, memory, and boundaries

- Mapped `byt`, `ozn`, `rzn`, `_Zr`, `bZr`, and `bHe`, including origin
  classification, matched human answers, summaries, optional host facts/outcomes,
  registry filtering, input adaptation and separate candidate serialization.
- Resolved `lin` as account-memory withdrawal/redaction rather than compaction.
  Traced instruction discovery, imports, limits, auto memory, cache publication,
  snapshot selection, compaction requests, post-compact restoration and
  classifier-overflow recovery.
- Distinguished source instructions to preserve constraints from proof that a
  generated summary actually preserved them. The independent reference carries
  explicit host constraints rather than claiming such a proof.
- Mapped the separate server safeguards context and ownership/freshness checks,
  byte-budget shedding, ToolSearch schema budget/discovery cache, and advisor
  context boundary. Private server behavior remains unavailable.

Public outputs: [context index](../context/README.md) and linked detailed pages.
Private originals: `research/context-v3/` and original modules. Some investigators
were interrupted by a usage limit after saving their files; the saved work was
subsequently completed and checked. No unavailable agent output is represented as
a completed experiment.

## ToolSearch and advisor

- Inspected the local `qNt` ranker and built an independent deterministic
  implementation. Exact-name, required-term and weighted matching are separate
  from hosted regex/BM25 search and permission to execute a discovered tool.
- Inspected the advisor declaration and public API contract. The service receives
  conversation context and provides advice through a separate hosted model;
  local client code does not expose the complete server prompt or weights.

Public outputs: `search.py`, `advisor.py`, [integration](../integration.md),
[boundaries](../context/boundaries.md). Private originals:
`research/search_advisor/` and the earlier standalone prototypes.

## Jev, prior art, and collection

- Resolved Jev as TypeSafe's typed System One decision API; built a pinned
  five-predicate Noul request/response adapter. No live call was made.
- Reviewed LangChain core AutoModeMiddleware, its deprecated TypeSafe wrapper,
  cc-automode, opencode-plugin-auto-classifier, AmPermBench and AgentDojo.
  Distinct integration code, benchmarks, and label provenance are documented.
- Reviewed official hook/SDK contracts and built a passive collector. It stores
  observations with null labels and `training_eligible: false`. Executed calls
  are not automatically classifier allow labels; unavailable reviews are not
  automatically semantic deny labels.

Public outputs: [prior art](../prior-art.md), [collection](../collection.md),
`jev.py` and `collection.py`. Private originals: `research/jev-search/`,
`research/jev-guard/`, `research/research-v2/`.

## Model pipeline and packaging

- Verified the Qwen3-0.6B sequence-classifier architecture at its pinned revision:
  596,052,992 total parameters and a 3,072-parameter three-class head, using a
  metadata-device construction rather than downloading pretrained weights.
- Implemented reviewed-data checks, connected-component splitting, head-only or
  full fine-tuning, calibration, metrics, safetensors persistence and local
  inference. Ran a real tiny random Transformer train/save/reload smoke.
- Published the original project commit `d7ad8e7e36e95a60e2a63c3dc0b91562d308a057`.
  Its GitHub Actions run `43333579542` passed. The newer context/handoff checks are
  recorded separately in [validation.json](../validation.json).

No full-size training, representative dataset or production evaluation was
completed. Private originals: `research/training-v2/` and prototype validation
files. Current maintained code is in `src/small_auto_mode/`; earlier prototypes
are historical evidence, not alternate production entry points.

## Local decision-model follow-up

The user requested vLLM's decision models and the closest practical Jev-like
alternatives under a low-memory, on-device constraint. The fresh primary-source
comparison is [local-model-options.md](../local-model-options.md). It distinguishes
total loaded parameters from parameters active per question and weight size from
resident process memory. Metadata/cards/licenses were inspected; weights were
not downloaded and no accuracy or latency benchmark was run.

The next coding session should follow [HANDOFF.md](../HANDOFF.md), beginning with
the optional local backend and benchmark contract.
