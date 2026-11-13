# Continuing small-auto-mode

Read [docs/HANDOFF.md](docs/HANDOFF.md) first. It contains the current state,
verification commands, implementation map and ordered next tasks. If the user
says only **continue**, start with that guide's **Next implementation task**.

The goal is an independent, local, low-memory tool-authorization gate for a
general application. Preferred model size is below 500M parameters; the ceiling
is 1B **total loaded** parameters. The current project is a research prototype,
with automatic approval disabled by default. It is not integrated into Muse or
any other app, and no sandbox is implemented here.

Keep these distinctions accurate:

- Context assembly is not a model verdict; `ready` means `unassessed`.
- Source-backed behavior, public API contracts and original design choices are
  labeled separately. Preserve that provenance when editing the documentation.
- No native classifier weights, representative teacher dataset, trained 596M
  checkpoint or production accuracy result has been obtained.
- A tool's successful execution is not an authenticated classifier allow label.
- The original inspected bytes are preserved in the checked-in private archive
  `research/ground-source-2.1.323.tar.gz`. Restore it when source verification is
  needed, following [ground-source.md](docs/handoff/ground-source.md); a fresh
  clone includes it. Never edit those originals; format a separate copy if needed.

This checkpoint contains the original research archive and must remain private.
Do not change repository visibility or redistribute the archive. Provenance and
third-party terms remain unchanged by private storage.

The next implementation task uses public open-model contracts and original code.
It does not require accessing private endpoints or extending the inspection of
Claude Code. If a reference artifact is unavailable or you cannot work with it,
state that limit and continue the independent task using its available public
sources. Do not invent evidence or claim to have run missing experiments.

Use Python 3.11+, keep the default runtime dependency-free, and keep model
dependencies optional. Run relevant tests and the complete existing suite before
publishing changes. Do not execute candidate commands while testing the gate.
Do not commit credentials, live user transcripts, weights or an unreviewed
dataset. Keep the preserved research archive unchanged; do not add unrelated
vendor artifacts. See [NOTICE.md](NOTICE.md) and the data provenance
contract in [docs/collection.md](docs/collection.md).
