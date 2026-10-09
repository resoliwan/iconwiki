import { parentPort, workerData } from 'node:worker_threads';
import { readFile } from 'node:fs/promises';
globalThis.self = globalThis;
globalThis.postMessage = message => parentPort.postMessage(message);
globalThis.fetch = async url => {
  parentPort.postMessage({ type: 'requested', url });
  return { ok: true, json: async () => JSON.parse(await readFile(new URL(url, workerData.root), 'utf8')) };
};
await import('../../search-worker.js');
parentPort.on('message', data => self.onmessage({ data }));
