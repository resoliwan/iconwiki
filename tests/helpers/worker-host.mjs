import { parentPort, workerData } from 'node:worker_threads';
import { readFile } from 'node:fs/promises';
import { Duplex } from 'node:stream';
import { createBrotliDecompress } from 'node:zlib';

globalThis.self = globalThis;
globalThis.postMessage = message => parentPort.postMessage(message);
const failOnce = new Set(workerData.failOnce);
globalThis.fetch = async url => {
  parentPort.postMessage({ type: 'requested', url });
  if (failOnce.delete(url)) return new Response(null, {status: 503});
  return new Response(await readFile(new URL(url, workerData.root)));
};

// Cover browsers with and without Brotli streams regardless of the Node version.
const NativeDecompressionStream = globalThis.DecompressionStream;
globalThis.DecompressionStream = class {
  constructor(format) {
    if (format === 'brotli') {
      if (!workerData.brotli) throw new TypeError('Unsupported compression format');
      try { return new NativeDecompressionStream(format); }
      catch { return Duplex.toWeb(createBrotliDecompress()); }
    }
    return new NativeDecompressionStream(format);
  }
};

await import('../../search-worker.js');
parentPort.on('message', data => self.onmessage({ data }));
