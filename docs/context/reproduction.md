# Reproducing and checking the source map

The inspected artifact is the official npm package
`@anthropic-ai/claude-code-linux-x64@2.1.323`. Its `claude` file is 362,435,088 bytes
with SHA-256:

```text
604d29a6869409106b6a1110bdadcc8b72e8654a5a865d23258f938a696e348e
```

REA version: `rea-agents@6.9.0`, source
[a8527d43b8439476f5c9d1497315dfe7dd5e1f38](https://github.com/morluto/rea/tree/a8527d43b8439476f5c9d1497315dfe7dd5e1f38).
The map is pinned to these artifacts. Later releases may reuse a symbol name for
something different; a hash mismatch invalidates the pinned offsets.

## Extraction method

The binary contains a Bun standalone module graph. REA's standard expansion
refused its aggregate bytecode accounting because multiple modules refer to
overlapping bytecode ranges. We did not increase that budget. The original
[`extract-bun-contents.mjs`](../../scripts/extract-bun-contents.mjs) adapter uses
REA's unchanged graph reader and decoder, then copies only each module's contents
range. It omits bytecode and source maps and never runs the target binary.

The adapter restricts paths to the embedded root, rejects traversal and duplicate
destinations, caps each contents range at 16 MiB and their total at 128 MiB, and
requires a new output directory. A decoding or writing error is fatal; remove
only that failed scratch output before retrying. Use a private scratch directory
not concurrently writable by another process.

If you already have the pinned npm packages, run from the repository root:

```sh
node scripts/extract-bun-contents.mjs \
  /path/to/rea-agents/package \
  /path/to/claude-code-linux-x64/package/claude \
  /path/to/new-private-extraction-directory
```

For a fresh local inspection, obtain the packages without installing or launching
Claude Code. From the repository root, with a Node version supported by REA:

```sh
mkdir -p inspection-artifacts/rea inspection-artifacts/claude
npm pack --ignore-scripts --pack-destination inspection-artifacts/rea rea-agents@6.9.0
npm pack --ignore-scripts --pack-destination inspection-artifacts/claude @anthropic-ai/claude-code-linux-x64@2.1.323
tar -xzf inspection-artifacts/rea/rea-agents-6.9.0.tgz -C inspection-artifacts/rea
tar -xzf inspection-artifacts/claude/anthropic-ai-claude-code-linux-x64-2.1.323.tgz -C inspection-artifacts/claude
npm install --prefix inspection-artifacts --ignore-scripts --no-audit --no-fund zod@4.6.6
node scripts/extract-bun-contents.mjs \
  inspection-artifacts/rea/package \
  inspection-artifacts/claude/package/claude \
  inspection-artifacts/extracted
```

The adapter's transitive REA reader imports require `zod@4.6.6`; installing it in
the ancestor directory supplies that dependency without installing the entire
REA CLI dependency set or running package lifecycle scripts.

The verified extraction yielded **3,237 source/assets and 63,760,938 contents
bytes**. A second extraction reproduced every module hash. Extraction produces a
local manifest beside the output directory; that manifest records each absolute
binary offset, length, encoding and SHA-256. Extracted vendor artifacts are not
part of this repository and `inspection-artifacts/` is ignored by Git.

## Check the published anchors

```sh
python scripts/verify_context_evidence.py \
  --extracted inspection-artifacts/extracted \
  --binary inspection-artifacts/claude/package/claude
```

The verifier compares the binary when supplied, every documented module hash and
size, and every short declaration anchor at its expected byte offset. It exits
nonzero on mismatch and does not print or execute vendor source. Without
`--binary`, it verifies extracted modules only. Use `--manifest` to select another
explicitly versioned map.

`byte_offset` is zero-based **within the extracted file**. For the pinned
contents-only representation:

```text
absolute binary offset = module.absolute_byte_offset + symbol.byte_offset
```

Offsets refer to the original bytes, not a pretty-printed file or Unicode
character count. The principal JS chunks are Latin-1 encoded. Decode as Latin-1
for one-byte indexing, or navigate in a binary-capable editor. Keep a separate
formatted copy for reading; do not use its offsets to verify the original.

## Evidence strength

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| Matching binary/module hashes | We examined the same bytes | Source interpretation is correct |
| Matching symbol anchors | Readers can locate the cited functions | Every branch was exercised |
| Static function and caller analysis | Available branches, input transforms and request contracts | A particular account enables those branches |
| Public documentation | Stated service behavior at the referenced page | Hidden server implementation or unchanged future defaults |
| Reference implementation tests | Our declared input/output and failure behavior | Native implementation equivalence or classifier accuracy |

The Markdown maps are original analysis and the scripts are original adapters.
Only identifiers, hashes and short location anchors are published from the
inspected artifact; no complete proprietary implementation, policy prompt,
transcript or checkpoint is included.

The optional [private research companion](../handoff/ground-source.md) preserves
the original extracted files and saved research snapshots unchanged. It offers
another way to verify the map without downloading or extracting the binary again.
