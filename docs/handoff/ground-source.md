# Preserved ground source

The original extracted bytes are preserved separately from the maintained
interpretation and independent code. They were **not renamed to disguise their
origin, reformatted, redacted, or replaced with summaries**. Provenance remains
Claude Code 2.1.323 inspected using REA 6.9.0 plus an original contents-only
extraction adapter.

The archive is checked into this **private repository** at
[`research/ground-source-2.1.323.tar.gz`](../../research/ground-source-2.1.323.tar.gz).
A normal Git clone includes it, so no download from the previous chat is needed.
Keep this checkpoint private and do not redistribute the archive.

## What is in the preserved archive

`ground-source-2.1.323.tar.gz` contains **3,711 original files** totaling
75,814,704 uncompressed bytes, plus a README and checksum manifests:

- All **3,237 extracted contents files** in `original/extracted/`, including the
  original minified JS/assets, with their original byte encodings.
- The original policy export, extraction inventory/manifests, and package
  registry metadata in `original/`.
- Saved research notes, extracted function snippets, captured documentation and
  public model metadata in `research/`. This includes the auto-mode, context,
  memory, search/advisor, Jev, prior-art, collection and model investigations.
- Historical original prototypes and their validation records. The maintained
  implementation is the one in this repository, not these older copies.

Each original file was hashed, copied into the archive without transformation,
and re-read from the archive to verify its size and SHA-256 against the source.
`MANIFEST.json` and `SHA256SUMS` inside the archive enumerate every file.

Archive size: **24,374,142 bytes**. SHA-256:

```text
8f679f81d2c546a421a1b3216101d7bb128602f2020a6626f77425fedf8446e0
```

The machine-readable archive record is [private-bundle.json](private-bundle.json).
The original 362 MB executable and downloaded package archives are not duplicated
in this smaller archive. Its manifest records the binary digest;
[reproduction](../context/reproduction.md)
identifies the exact package for obtaining it again.

## Repository and extraction boundaries

The repository contains original analysis, code, tests, evidence locations and
hashes, plus the unchanged research archive under `research/`. This checkpoint
must remain private because the archive retains vendor source/assets, the
original exported policy and captured reference material under their existing
terms. Private storage does not relicense them under this project's Apache-2.0
license.

The archive excludes credentials, live CLI configuration, live user transcripts,
model weights, and the training environment. Original executable and package
archives are also omitted. `inspection-artifacts/` remains Git-ignored and is
where the checked-in archive is unpacked for reading; the unpacked files do not
need to be committed again.

The original source is available from a fresh clone even if the earlier research
workspace or chat attachment is unavailable. Continue independent implementation
using the maintained code and documents; unpack the source when a claim needs to
be checked against its original bytes.

## Restore beside a fresh clone

From the repository root, verify the checked-in archive's digest against the value
above. If `inspection-artifacts/ground-source-2.1.323/` already exists, verify its
checksums and reuse it rather than overwriting it. Otherwise extract:

```sh
sha256sum research/ground-source-2.1.323.tar.gz
mkdir -p inspection-artifacts
tar -xzf research/ground-source-2.1.323.tar.gz -C inspection-artifacts
cd inspection-artifacts/ground-source-2.1.323
sha256sum -c SHA256SUMS
cd ../..
python scripts/verify_context_evidence.py \
  --extracted inspection-artifacts/ground-source-2.1.323/original/extracted
```

On macOS, `shasum -a 256` can replace `sha256sum`, including the `-c` check.
Extract only the archive whose hash matches the recorded digest. The archive has
a single `ground-source-2.1.323/` root and contains regular files under that root.

Treat `original/` and historical `research/` snapshots as immutable evidence.
Put formatted code, new notes or corrections in a separate derived directory.
Use [evidence.json](../context/evidence.json) to navigate by module and byte
offset; formatting changes those offsets. A newer interpretation should point
back to the original and explain its correction, rather than changing the
historical source to match the new interpretation.

When two notes disagree, verify the pinned source and inspect the latest
maintained documentation. Historical notes can contain hypotheses that were
later corrected—for example, the early guess that `lin` performed compaction
was resolved to account-memory revocation/redaction. Keeping the original note
is part of the audit trail, not endorsement of that guess.
