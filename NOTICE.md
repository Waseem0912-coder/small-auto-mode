# Provenance and third-party work

The Python implementation in this repository is independently written. Runtime prototypes were developed from public API contracts and a static behavioral inspection. The separately identified `research/ground-source-2.1.323.tar.gz` archive preserves the original inspection artifacts and working research in this private checkpoint at the repository owner's request. Those external contents retain their own terms; the project's Apache-2.0 license does not relicense them. No original executable binary or private session transcript is included.

REA (morluto/rea) was used for the local inspection. LangChain, cc-automode, opencode-plugin-auto-classifier, AmPermBench and AgentDojo are referenced in `docs/prior-art.md`; their source is not vendored. Their licenses do not automatically cover separately embedded third-party assets or service-generated data.

Optional model training downloads Qwen/Qwen3-0.6B under its own Apache-2.0 license. This repository's license covers original code and documentation, not external model weights, service outputs or datasets. Anthropic and TypeSafe APIs remain subject to their own service terms. Names identify compatibility/research subjects and do not imply affiliation or endorsement.
