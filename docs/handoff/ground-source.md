# Preserved ground source

The original extracted bytes are preserved separately from the maintained
interpretation and independent code. They were **not renamed to disguise their
origin, reformatted, redacted, or replaced with summaries**. Provenance remains
Claude Code 2.1.323 inspected using REA 6.9.0 plus an original contents-only
extraction adapter.

## What is in the private companion

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
The original 362 MB executable and downloaded package archives remain in the
research workspace but are not duplicated in this smaller companion. Its
manifest records the binary digest; [reproduction](../context/reproduction.md)
identifies the exact package for obtaining it again.

## Public repository versus local bundle

The public Git repository contains original analysis, code, tests, evidence
locations and hashes. **It does not contain the private archive, full vendor
source, policy dump, credentials, private transcripts or model weights.** The
archive is stored under the ignored `inspection-artifacts/` directory in the
working checkout and was not uploaded to public GitHub.

Download or copy the companion while this workspace is available, and keep it
with your own project backups. A temporary workspace is not permanent archival
storage. A fresh Git clone alone contains the handoff and findings; access to the
original extracted bytes additionally requires this companion or a reproduced
extraction. Continuing the independent open-model implementation does not depend
on having those bytes.

## Restore beside a fresh clone

Put the downloaded archive into `inspection-artifacts/` under the repository
root. Verify its digest against the value above before extracting:

```sh
sha256sum inspection-artifacts/ground-source-2.1.323.tar.gz
tar -xzf inspection-artifacts/ground-source-2.1.323.tar.gz -C inspection-artifacts
cd inspection-artifacts/ground-source-2.1.323
sha256sum -c SHA256SUMS
cd ../..
python scripts/verify_context_evidence.py \
  --extracted inspection-artifacts/ground-source-2.1.323/original/extracted
```

On macOS, `shasum -a 256` can replace `sha256sum`, including the `-c` check.
Extract only the bundle whose hash matches the recorded digest. The archive has
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
