# Local decision models for the next experiment

Research checked **2026-11-12 (America/Los_Angeles)**. This is a model-selection
handoff, not a benchmark result. No candidate weights were downloaded, no live
model inference was run, and no model in this comparison was fine-tuned by this
project.

**Recommendation:** benchmark `vllm-sr/Vela-2.0-0.3B` first for the smallest
CPU-oriented implementation, alongside `vllm-sr/Decision-2.0-Kai-0.6B` as the
general decision-model comparator. Keep this project's Qwen3 three-class trainer
as a supervised baseline. Select after measuring authorization errors and memory
on the intended device. This is a recommendation for an experiment, not evidence
that either released model safely authorizes arbitrary tools.

## These are actual Jev-style models

vLLM Semantic Router now publishes models that accept state and caller-defined
questions and return typed probabilities. Its Decision and Vela families are not
limited to fixed domain-routing labels. `choice`, `noul` and `score` correspond to
the interface we wanted from Jev; the specific support differs by model.
[Official supported-model catalog](https://vllm-sr.ai/docs/model-runtime/supported-models/overview/).

The important distinction remains **authorization**. A harmful-content or
prompt-injection score does not answer whether the user authorized this exact
command, recipient, file write or external side effect. We need to supply intent,
constraints, candidate arguments and relevant trusted facts together. A model's
existing safety tasks can help initialize that experiment; they are not a
replacement for the application's authorization labels or host checks.

## Shortlist and exact versions

| Candidate | Size evidence | Useful capability | Fit for this project |
| --- | --- | --- | --- |
| **Vela-2.0-0.3B** | 309,114,369 packaged parameters | ModernBERT; caller-defined Choice/Noul/Score, set and span questions; trained router tasks | First CPU and compact-runtime candidate |
| **Decision-2.0-Kai-0.6B** | 597,103,104 loaded parameters in its release manifest | Qwen3; general Choice/Noul/Score over text/JSON; 8,192-token input | General decision-model comparator, comfortably below 1B |
| **Vela-2.0-0.8B** | Official runtime reports about 0.756B loaded | Qwen3.5 text; typed decisions plus router/broad span heads | Optional larger comparator if GPU or latency budget permits |
| Existing Qwen3-0.6B baseline | 596,052,992 with this project's classification head | Fixed `allow / ask / deny` classes after supervised training | Existing pipeline; currently untrained for this task |

Pinned Hugging Face revisions, resolved through the Hub API rather than guessed
from model names:

```text
vllm-sr/Vela-2.0-0.3B
  a3209a50dc3ebd7e3b7520440d8fba666000f4c4
vllm-sr/Decision-2.0-Kai-0.6B
  cd49ea3813fd8ba0928a9a23ef6c9a0f2f0cd764
vllm-sr/Vela-2.0-0.8B
  a778eb2ae2304cfa72fca7e53a19136dea5be012
```

These match the revisions linked by the runtime documentation when checked.
The repositories' moving `main` heads were different; do not silently substitute
them. Size sources: [Vela 0.3B pinned Hub metadata](https://huggingface.co/api/models/vllm-sr/Vela-2.0-0.3B/revision/a3209a50dc3ebd7e3b7520440d8fba666000f4c4),
[Kai release manifest](https://huggingface.co/vllm-sr/Decision-2.0-Kai-0.6B/blob/cd49ea3813fd8ba0928a9a23ef6c9a0f2f0cd764/MODEL_MANIFEST.json),
[Vela 0.8B runtime page](https://vllm-sr.ai/docs/model-runtime/supported-models/vela-2/vela-2-0-8b/),
and this project's [validation record](validation.json).

Do not equate packaged tensor counts with total loaded runtime parameters.
For example, the Vela 0.8B Hub metadata reports 754,565,953 parameters, while the
runtime catalog rounds its loaded model to 0.756B. Measure the actual selected
runtime instead of presenting these different counts as one exact number.

### Why not choose the newest default automatically?

The current `vela3-fast` default is described as roughly 0.4B *per question*, but
its model page reports **1.52B loaded**, about 6.1 GB of FP32 weights, and a 12 GiB
device-memory recommendation. It exceeds our total-parameter target. The
sub-billion `vela3-lite` is a different, multimodal model. A small active-per-query
number is not the resident model size.
[Vela3-fast model page](https://vllm-sr.ai/docs/model-runtime/supported-models/vela-3/vela3-fast/),
[full model catalog](https://vllm-sr.ai/docs/model-runtime/supported-models/overview/).

## What low memory currently means

| Candidate and documented runtime | Weight-memory estimate from runtime docs | Catalog device budget |
| --- | --- | --- |
| Vela 0.3B, CPU FP32 | About 1.2 GB | At least 4 GiB |
| Kai 0.6B, CPU FP32 | About 2.4 GB | At least 4 GiB |
| Vela 0.8B, CPU FP32 | About 3.0 GB | At least 4 GiB |

These are upstream sizing figures, **not measured process RSS in our app**.
Tokenization, intermediate activations, loaded libraries, input length and
concurrency add memory. The Vela 0.3B page validates CPU use; Kai's page identifies
CPU support as well. The larger Vela decoder is documented as taking seconds on
CPU for the upstream workload.
[Vela 0.3B](https://vllm-sr.ai/docs/model-runtime/supported-models/vela-2/vela-2-0-3b/),
[Kai 0.6B](https://vllm-sr.ai/docs/model-runtime/supported-models/decision-2/kai-0-6b/),
[Vela 0.8B](https://vllm-sr.ai/docs/model-runtime/supported-models/vela-2/vela-2-0-8b/).

The pinned Vela 0.3B package includes standalone ONNX FP32 and FP16 encoder
exports, with tokenization, windowing, calibration and output decoding performed
outside the graph. That makes an ONNX-based local adapter worth testing without
adopting the whole routing service. Its documented parity sample is small and
does not establish authorization quality.
[Pinned Vela model card, ONNX section](https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/a3209a50dc3ebd7e3b7520440d8fba666000f4c4/README.md#onnx).

The official runtime currently does **not** load quantized Vela 2.0 or Decision
2.0 packages. Its published compressed-weight support concerns Decision 3.0.
Do not advertise an existing 4-bit Vela/Kai backend merely because the backbone
has a familiar name. A future INT8 export is a separate engineering experiment
requiring kernel support, complete-input handling and re-evaluation of scores.
[Quantization documentation](https://vllm-sr.ai/docs/model-runtime/quantization/overview/).

Apple silicon is documented as CPU-only in this runtime release, with host GPU
support tracked separately. A native ONNX/Core ML/Metal/MLX port may be possible,
but this research did not establish one for these exact model heads and versions.
The Docker-based macOS path also uses a Linux VM, so it does not meet the user's
preferred VM-free packaging. Prefer a direct host process or library for the
experiment, and measure that deployment.
[Hardware support](https://vllm-sr.ai/docs/model-runtime/get-started/choose-a-model/#hardware).

## Licenses and integration boundaries

Kai's pinned manifest describes Apache-2.0 coverage for the released model,
runtime, and Qwen3 base/tokenizer components. Its model card requires
`transformers>=5.17` for the demonstrated custom model interface. Our existing
trainer pins Transformers below 5; use an isolated environment or process for
this comparator instead of breaking the tested baseline.
[Kai model card](https://huggingface.co/vllm-sr/Decision-2.0-Kai-0.6B/blob/cd49ea3813fd8ba0928a9a23ef6c9a0f2f0cd764/README.md),
[component manifest](https://huggingface.co/vllm-sr/Decision-2.0-Kai-0.6B/blob/cd49ea3813fd8ba0928a9a23ef6c9a0f2f0cd764/MODEL_MANIFEST.json).

Vela 0.3B's top-level Apache label does not cover every inherited component:
its retained notices identify MIT upstream contributions and Gemma-origin
tokenizer conditions. Preserve and review those terms when bundling the model
with an app. The retained licensing document has an older Decision-family title;
use the actual files at the pinned revision, not just the Hub license badge.
[Pinned license scope](https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/a3209a50dc3ebd7e3b7520440d8fba666000f4c4/LICENSING_STATUS.md),
[distribution terms](https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/a3209a50dc3ebd7e3b7520440d8fba666000f4c4/DISTRIBUTION_TERMS.md).

Neither the local model nor a local HTTP service creates an execution boundary.
Keep the dispatcher responsible for capabilities, exact arguments, current
targets and mandatory confirmation. Before a sandbox exists, an unrestricted
shell can perform effects that a probabilistic classifier misses. The useful
near-term product is an auditable, abstaining decision gate with explicit host
checks; it must not be presented as containment.

## Concrete next task for the coding handoff

Implement a **benchmark-only local decision adapter** before changing enforcement
or fine-tuning anything:

1. Add a separate optional runtime/environment for pinned Vela 0.3B, beginning
   with its FP32 ONNX path. Inspect and pin any imported custom runtime code and
   weight files. Load once; make downloads explicit. Add a Kai comparator in its
   separate supported environment after the Vela path works.
2. Define a versioned mapping from [the context packet](context/reference.md) to
   the model's state. Preserve authenticated user intent, constraints, exact
   candidate arguments and provenance boundaries. Vela's automatic JSON-field
   role mapping is a model input convention, not an identity verifier. Reject
   unsupported or incomplete packets before inference.
3. Ask one three-way Choice question (`allow`, `ask`, `deny`) and separately test
   Noul predicates for authorization, sensitive egress, destructive effects and
   instruction injection. Compare bundled and separate-question results. Do not
   invent a mapping from Noul probabilities to this project's three-class scores.
4. Build a reviewed owned dataset with matched pairs: identical command with
   different intent, changed recipient/path, stale memory, lost constraint,
   legitimate versus forged answer, and instructions inside tool results. Split
   by session/scenario family before fitting anything; retain a never-tuned test
   set. Synthetic fixtures are software tests, not reported safety accuracy.
5. Measure cold start, peak RSS, warm p50/p95 latency and CPU threads at short,
   medium and maximum supported input lengths, with concurrency one first.
   Record hardware, full revision, runtime/library versions and truncation.
   Missing context must produce abstention, not an approval over a shortened
   input.
6. Compare macro F1, calibration, unsafe approvals and coverage. Select thresholds
   using only calibration data. Keep automatic approval off. Only then decide
   whether task-specific fine-tuning, a smaller head, distillation or quantization
   is justified, and repeat the held-out evaluation after each change.

The existing `training.py` trains a Qwen sequence-classification head. It does
not fine-tune Vela's typed heads or Kai's custom decision architecture by changing
the model name. Add a deliberate training path only after a measured baseline
and usable labeled data exist.
