# Original research archive — private checkpoint

[ground-source-2.1.323.tar.gz](ground-source-2.1.323.tar.gz) preserves all 3,711
saved research files, including the 3,237 original extracted contents files.
The repository owner requested that this archive be committed after changing
the repository to private. Keep this checkpoint private.

The archive is byte-for-byte identical to the companion originally created for
the handoff. Original minified source, policy export, saved notes, captured pages,
and historical prototypes are retained; their provenance has not been changed.
External material retains its own terms and is not covered by this repository's
Apache-2.0 license. No credentials, live session transcript, CLI config, model
weights, or installed environments are included.

The executable and downloaded package archives are not duplicated here. The
original extracted source/assets and their hashes are included; the executable
can be obtained from the pinned official package if a new extraction is needed.

## Restore from a clone

From the repository root, verify the SHA-256:

```sh
sha256sum research/ground-source-2.1.323.tar.gz
```

Expected:

```text
8f679f81d2c546a421a1b3216101d7bb128602f2020a6626f77425fedf8446e0
```

Then restore to the ignored inspection directory:

```sh
mkdir -p inspection-artifacts
tar -xzf research/ground-source-2.1.323.tar.gz -C inspection-artifacts
cd inspection-artifacts/ground-source-2.1.323
sha256sum -c SHA256SUMS
cd ../..
python scripts/verify_context_evidence.py \
  --extracted inspection-artifacts/ground-source-2.1.323/original/extracted
```

On macOS, use `shasum -a 256` in place of `sha256sum`. Do not overwrite a modified
working copy: preserve your derived work separately, then restore into an empty
destination. The archive contains a README and a per-file manifest.

The archive's own README still describes the original local-companion delivery;
it was left unchanged to preserve the recorded hash. This file documents the
subsequent private Git storage. Updated findings and next tasks are in
[the handoff](../docs/HANDOFF.md); historical notes can contain earlier hypotheses.
