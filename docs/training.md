# A 596M contextual authorization classifier

Base: [Qwen/Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B), revision `c1899de289a04d12100db370d81485cdf75e47ca`, Apache-2.0 model card/license. This repository does not redistribute weights.

The actual `Qwen3ForSequenceClassification` configuration has **596,052,992 parameters**, including **3,072 parameters in its classification head**. This count was verified by constructing the pinned architecture on PyTorch's metadata device, without downloading its pretrained weights. The 1B cap is also checked on the instantiated training/inference model.

The architecture uses a pretrained decoder backbone and a three-way classification head, one forward pass and no autoregressive verdict generation. It is a compact baseline for this task, not a reproduction of Jev's proprietary architecture. Head-only training is a cheap first baseline; full fine-tuning can adapt semantics more strongly but costs memory. LoRA and quantized deployment are future work, not implemented features.

## Data first

Create `reviewed.jsonl` from the [record template](../examples/record.template.json). The template is deliberately unverified and will be rejected until a reviewer fills it in. A real corpus needs both benign and risky actions, ambiguity (`ask`), varied tools and contextual near misses. Tests construct tiny fixtures solely to check software behavior.

```sh
python -m small_auto_mode.dataset reviewed.jsonl --output data/split-v1
```

Records are grouped into connected components across shared `session_id`, `scenario_family`, and identical serialized input. A component cannot cross partitions. This is stronger than a row shuffle: if two sessions share a scenario template, they remain together. You need at least three independent components, and enough examples for all labels in training. Use scenario-family IDs that group related variants; do not assign a fresh ID to each paraphrase to defeat the split.

The tool writes train/calibration/test JSONL and a SHA-256 manifest. The trainer verifies bytes and checks session, scenario and exact-context disjointness again. No label, reviewer, outcome, denial reason or provenance field enters model features. Ensure environment/history themselves do not leak answers.

## Train

For GPU use, install PyTorch appropriate for your GPU, then the extra. For a CPU mechanics test you can use the official CPU wheels:

```sh
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e '.[train]'
python -m small_auto_mode.training --data data/split-v1 --output models/guard-v1
```

Default: one epoch, batch size one, frozen pretrained backbone, trained classification head, maximum 4096 input tokens. Longer records cause an error rather than silently dropping authorization or the candidate. Create a reviewed, bounded representation or increase the cap and evaluate the memory/latency tradeoff.

Full fine-tuning:

```sh
python -m small_auto_mode.training --data data/split-v1 --output models/guard-full-v1 \
  --full-finetune --device cuda --epochs 3 --batch-size 1
```

The simple trainer uses AdamW and gradient clipping. It does not implement distributed training, gradient accumulation, mixed precision or automated hyperparameter search. Float32 weights alone are about 2.38 GB; gradients, optimizer states, activations, tokenization and runtime overhead add substantially more. A pretrained 596M run was not performed in the development session.

## Calibration and final test

Temperature is selected on a fixed calibration grid by negative log likelihood. An illustrative threshold is then selected on calibration only to maximize coverage with zero observed unsafe approvals on that partition. This is a starting operating-point search, not a proof of safety. If calibration lacks safe or unsafe examples, automatic approval is disabled (`allow_min > 1`).

The untouched test set reports raw-class macro F1/confusion matrix, 10-bin ECE, multiclass Brier score, auto-allow coverage and unsafe auto-approval rate. `ask` and `deny` both count as unsafe to automatically approve. Zero-failure confidence bounds assume independent representative cases, which correlated scenarios may violate. Report scenario-level uncertainty and per-tool/per-attack-family performance before deployment; this first pipeline does not calculate those analyses automatically.

`guard.json` records temperature, threshold, base revision, dataset hashes, counts and `deployment_validated: false`. Saved weights use safetensors. A policy must explicitly enable automatic approval and choose a reviewed threshold; loading a checkpoint does not enable it. A small test set or one favorable threshold cannot validate production use.

## Mechanics-only validation

```sh
python -m small_auto_mode.training --smoke --output models/random-smoke
python -m unittest discover -s tests -v
```

The optional test creates a tiny random Qwen3 model, trains its head, calibrates, saves it, reloads with `LocalClassifier`, and checks the probability interface. No pretrained weights or service credentials are used. `smoke_only: true` is preserved. Synthetic smoke metrics are not reported as model quality.

## Research milestones

1. Collect and review an initial corpus spanning authorized, forbidden and ambiguous effects; record actual source rights.
2. Compare Jev, a permitted larger teacher, the frozen-head baseline and full fine-tuning on identical held-out inputs.
3. Audit context construction, indirect effects, unknown-tool behavior and long-context cases.
4. Freeze a calibration procedure, evaluate a final unseen corpus and measure p50/p95 latency plus error-versus-coverage.
5. Only then test quantization and publish a model card and permitted weights/dataset artifacts.

There is no defensible accuracy promise from parameter count alone. Train a new model for this task; REA cannot turn hosted Claude weights into a 596M checkpoint.
