// Contents-only REA 6.9.0 adapter. It does not execute the inspected binary.
import { open, writeFile, mkdir } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';

const [reaArg, inputArg, outputArg] = process.argv.slice(2);
if (!reaArg || !inputArg || !outputArg) {
  console.error('Usage: node extract-bun-contents.mjs REA_PACKAGE_DIR BINARY NEW_OUTPUT_DIR');
  process.exit(2);
}
const rea = resolve(reaArg), input = resolve(inputArg), output = resolve(outputArg);
const { probeBunStandaloneGraph, loadBunStandaloneGraph } = await import(
  pathToFileURL(resolve(rea, 'dist/artifacts/bun/BunModuleGraphLayout.js')));
const { decodeBunModuleGraph } = await import(
  pathToFileURL(resolve(rea, 'dist/artifacts/bun/BunModuleGraphMembers.js')));
const handle = await open(input, 'r');
try {
  const stat = await handle.stat();
  const probe = await probeBunStandaloneGraph(handle, stat.size);
  if (probe.status !== 'present' || !probe.claim) throw new Error('No admitted Bun graph');
  const loaded = await loadBunStandaloneGraph(handle, probe.claim);
  if (!loaded.graph) throw new Error('REA could not load the Bun graph');
  const graph = loaded.graph, decoded = await decodeBunModuleGraph(graph);
  if (decoded.modules.length > 10000) throw new Error('Module count exceeds inspection budget');
  const used = new Set();
  let total = 0;
  const plan = decoded.modules.map(module => {
    const source = module.nameText.text, prefix = '/$bunfs/root/';
    if (!source?.startsWith(prefix)) throw new Error('Unexpected source name');
    const relative = source.slice(prefix.length);
    if (relative.includes('\\') || relative.split('/').some(p => !p || p === '..' || p === '.'))
      throw new Error('Unsafe source name');
    const destination = resolve(output, relative);
    if (!destination.startsWith(output + '/') || used.has(destination)) throw new Error('Path collision');
    used.add(destination);
    const { offset, length } = module.contents;
    if (![offset, length].every(Number.isSafeInteger) || offset < 0 || length < 0 ||
        length > 16 * 1024 * 1024 || offset + length > graph.payloadLength)
      throw new Error('Unexpected content range');
    total += length;
    if (total > 128 * 1024 * 1024) throw new Error('Contents exceed inspection budget');
    return { module, source, relative, destination, offset, length };
  });
  await mkdir(output); // Must not already exist; never overwrite a previous extraction.
  const records = [];
  for (const { module, source, relative, destination, offset, length } of plan) {
    const bytes = Buffer.alloc(length);
    let read = 0;
    while (read < length) {
      const result = await handle.read(bytes, read, length - read, graph.payloadOffset + offset + read);
      if (!result.bytesRead) throw new Error('Short read');
      read += result.bytesRead;
    }
    await mkdir(dirname(destination), { recursive: true });
    await writeFile(destination, bytes, { flag: 'wx', mode: 0o600 });
    records.push({ index: module.index, source, path: relative, length,
      absoluteByteOffset: graph.payloadOffset + offset,
      sha256: createHash('sha256').update(bytes).digest('hex'),
      encoding: module.encodingName, loader: module.loaderName });
  }
  const manifest = { reaVersion: '6.9.0', input, size: stat.size,
    payloadOffset: graph.payloadOffset, payloadLength: graph.payloadLength,
    entryPointId: decoded.entryPointId, output, selection: 'contents only; bytecode/maps omitted',
    modules: records };
  await writeFile(output + '.manifest.json', JSON.stringify(manifest, null, 2), { flag: 'wx', mode: 0o600 });
  console.log(JSON.stringify({ files: records.length, contentsBytes: total, output }));
} finally {
  await handle.close();
}
