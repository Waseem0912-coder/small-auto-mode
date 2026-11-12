# Existing work and what to reuse

Inspected 2026-11-12. These are references, not dependencies vendored into this project. Published benchmark numbers from different task distributions are not interchangeable.

| Project | Verified contribution | Reuse decision |
| --- | --- | --- |
| [LangChain AutoModeMiddleware](https://github.com/langchain-ai/langchain/blob/980e4a80d01f699ba359db139cd7c8bfc348c110/libs/langchain_v1/langchain/agents/middleware/auto_mode.py) | Core middleware, any BaseDecisionModel, Noul risk question, last 30 messages and tool call/description, fixed 0.5 cutoff; only named tools guarded; errors propagate before handler | Best existing integration if the application already uses LangChain. MIT. Not a trained small classifier or dataset |
| [Deprecated TypeSafe wrapper](https://github.com/langchain-ai/langchain/blob/980e4a80d01f699ba359db139cd7c8bfc348c110/libs/partners/typesafe/langchain_typesafe/experimental/middleware/auto_mode.py) | Wrapper now delegates to core AutoModeMiddleware with TypeSafeClassifier | Use the core API for new integration; the earlier Jev-only import is deprecated |
| [cc-automode](https://github.com/lghupan/cc-automode) | Reimplementation referencing Claude Code 2.1.81; staged hosted classification; 42-case Docker comparison | Useful historical architecture/benchmark reference. Repository metadata reports MIT, but bundled proprietary extracts retain their own status. Do not vendor its CLI copies/prompt dumps. Its benchmark is small and includes service-unavailable outcomes |
| [opencode-plugin-auto-classifier](https://github.com/nateinaction/opencode-plugin-auto-classifier) | Jev/System One integration, contextual authorization questions, deterministic trust/policy composition, uncertainty/fallback handling; README describes a 63-denial regression corpus | Useful integration and test-design reference. MIT repository. Its denial corpus is not verified native Claude-classifier training data; evaluate provenance separately |
| [AmPermBench](https://github.com/yan5ui/cc-auto-mode-measurement) | 128 authorization-ambiguity prompts across four task families, deterministic simulated environments, trace collection and action-level evaluation | Strong evaluation candidate. GitHub metadata did not identify a repository license at inspection; verify permission before redistributing or training on its assets. Paper licensing does not automatically license code/data |
| [AgentDojo](https://github.com/ethz-spylab/agentdojo) | Agent prompt-injection benchmark framework with tool environments | Useful additional adversarial evaluation, not a drop-in tool-authorization training corpus. MIT repository; inspect individual artifact provenance |

The LangChain source was inspected directly at the pinned commit above. It only guards the listed tools; a host must ensure its tool catalog is covered. It returns a blocked tool message rather than requesting human approval. This project instead uses an explicit `ask` path and keeps arbitrary unknown tools out of automatic approval.

The cc-automode README reports 39/42 cases for its custom classifier and acknowledges service-unavailable results in the official comparison. It also describes enforcement limitations in its own setup. These figures do not validate current Claude 2.1.323, our model, broad adversarial safety or parity. We did not run its benchmark.

AmPermBench's [paper](https://arxiv.org/abs/2604.04978) intentionally stresses authorization ambiguity. Its results differ from production-traffic evaluations because the workload and gate coverage differ. Keep external benchmarks as final evaluations rather than tuning prompts/thresholds to them.

The inspected projects and targeted searches did **not establish an existing released 500M–1B checkpoint distilled from verified Claude Code auto-classifier labels**. That is a bounded finding, not proof no such project exists. Existing integration code, small regression corpora and benchmark generators are valuable, but do not remove the need for a licensed, representative training corpus.

Suggested order: reuse a host's existing middleware, reuse evaluation ideas, collect owned ground truth, compare pretrained small-model baselines, and only then build a specialized checkpoint. A prompt-injection detector alone does not answer whether a particular user authorized a particular action.
