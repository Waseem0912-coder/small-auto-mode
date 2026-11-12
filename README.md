# small-auto-mode

Independent tool-call authorization, local tool discovery, and a training pipeline for a **596M-parameter allow / ask / deny classifier**.

**Status: research prototype. No trained safety checkpoint or production accuracy claim.** Candidate tool calls are never executed by this package. Automatic approval is off by default. The project is independent of Claude Code, LangChain, Jev, and any application host.

## Why this exists

An agent needs to distinguish an authorized action from a similar-looking action that exceeds the user's request. A command-only blacklist and a prompt-injection detector cannot make that decision reliably. The input needs the authenticated user request, durable constraints, exact tool arguments, trusted environment facts, and relevant history.

We inspected Claude Code 2.1.323 with REA and reviewed existing open-source auto-mode projects. The useful recoverable pieces are policy/context assembly, staged review, parsers, tool-search ranking, and failure handling. The examined classifier and advisor paths use hosted inference; no model weights were recovered. See [findings](docs/findings.md) and [prior art](docs/prior-art.md).

## Included

- Host policy gate: deterministic deny/ask/unknown handling before model inference; shadow mode; decisions bound to the exact call and policy.
- Jev adapter: version-pinned typed risk questions, offline request building, strict response validation, explicit live API command.
- Small local model: Qwen3-0.6B with a three-class classification head, head-only or full fine-tuning, calibration and held-out metrics. No generated-text verdict parsing.
- Claude Code observation collector: documented hooks, private local files, no automatic permission overrides, no automatic training labels.
- Dataset preparation: reviewed provenance, separate train/calibration/test sets, connected grouping across sessions, scenarios and duplicate inputs.
- Tool search: small independent deterministic implementation of observed name/hint/description ranking.
- Advisor: documented integration pattern and API declaration; no private server prompt or weights.

## Quick start: offline

Python 3.11+:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -e .
small-auto-mode gate --case examples/example-case.json --policy examples/example-policy.json
small-auto-mode jev-build --case examples/example-case.json --policy examples/example-policy.json
small-auto-mode search --catalog examples/catalog.json --query '+slack search'
python -m unittest discover -s tests -v
```

The gate returns `ask` by default. `jev-build` prints a request without sending it. `jev-query` is the explicit live alternative and reads `TYPESAFE_API_KEY` from the environment. Never place credentials in examples or datasets.

## Add a gate to your dispatcher

```python
from small_auto_mode.gate import assess
from small_auto_mode.local_model import LocalClassifier

predictor = LocalClassifier("models/my-reviewed-checkpoint")  # requires train extra
result = assess(case, policy, predictor)
# Your host enforces result['decision'] immediately before execution.
# Recheck the exact call, policy and current environment; do not reuse stale approvals.
```

`case` has `user_intent`, `environment`, `tool: {name, arguments}`, `host_gate`, and `untrusted_context`. Only the trusted host may set `host_gate`, environment facts or policy. The proposing model cannot grant itself authorization. The gate is not a shell parser, DLP engine, sandbox, path resolver or identity system. See [integration](docs/integration.md).

The local model returns probabilities for `allow`, `ask`, and `deny`. Host denials remain authoritative. Unless automatic approval is explicitly enabled with a validated threshold, model output remains advisory. High risk and uncertainty return `ask`; learned scores cannot override host policy.

## Collect with Claude Code

See [collection](docs/collection.md) before installing the example hook configuration. The collector is passive and never installs itself or reads your transcript automatically.

**A tool running is not an auto-classifier allow label. A denied action may be a no-verdict failure.** Observations are stored with `label: null` and `training_eligible: false`. Add reviewed intent, context, a decision and rights provenance to construct training records.

## Train the small model

See [training](docs/training.md) for the full data contract and commands:

```sh
pip install -e '.[train]'
python -m small_auto_mode.dataset reviewed.jsonl --output data/split-v1
python -m small_auto_mode.training --data data/split-v1 --output models/guard-v1
```

The default freezes the pretrained backbone and trains the classification head. `--full-finetune` trains the full model and needs substantially more memory. The trainer downloads the pinned Qwen checkpoint only when you run real training. Parameter count is checked against the 1B cap.

You can verify the plumbing without downloading pretrained weights:

```sh
python -m small_auto_mode.training --smoke --output models/random-smoke
```

This creates a tiny random Transformer artifact, explicitly marked `smoke_only`. It cannot protect tools.

## Measurement and provenance

The pipeline fits temperature and chooses an illustrative selective-approval threshold using calibration data only. It reports final-test macro F1, calibration error, Brier score, unsafe approvals and coverage. These metrics do not certify deployment. Evaluate unseen scenario families, tool families and adversarial cases, then compare Jev, the local model, a larger permitted teacher and human labels.

Human-owned labels are accepted by default. Other verified sources require explicit inclusion and documented training rights. Claude service terms restrict some competing-model training; a subscription or an observed verdict is not proof that a publishable training corpus is licensed. This project does not automate proprietary classifier scraping, private endpoint access, credential interception, or bulk teacher calls. See [data provenance](docs/collection.md#using-teacher-data).

## What is ready and what is not

Runtime and data tests pass, including an actual random-Transformer train/save/reload/inference smoke test. See [validation](docs/validation.json). No live teacher calls, representative labeled corpus, 596M fine-tuning run, or production evaluation was completed. The next milestone is a reviewed dataset and a measured error-versus-coverage curve, not a claim of Claude parity.

Original code is Apache-2.0. Referenced projects and model weights retain their own terms. No proprietary CLI source, full prompts, binaries, private transcripts, credentials or model weights are distributed here.
