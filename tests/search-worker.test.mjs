import test from 'node:test';
import assert from 'node:assert/strict';
import { Worker } from 'node:worker_threads';
import { readFileSync } from 'node:fs';

const root = new URL('../', import.meta.url);
const read = url => JSON.parse(readFileSync(new URL(url, root), 'utf8'));
const manifestUrl = './data/search/manifest.json';
const manifest = read(manifestUrl);
const material = manifest.collections.find(collection => collection.id === 'material-symbols-outlined');
const firstPage = read(material.catalog).slice(0, 100);
const publicId = 'iconify-mdi:home';
const localId = 'unicode:1F600';

function startWorker(t, brotli, failOnce) {
  const worker = new Worker(new URL('./helpers/worker-host.mjs', import.meta.url), {
    workerData: { root: root.href, brotli, failOnce },
  });
  t.after(() => worker.terminate());
  const requests = [];
  let registry;
  worker.on('message', message => {
    if (message.type === 'requested') requests.push(message.url);
    if (message.type === 'manifest') registry = message;
  });
  function send(message, matches) {
    return new Promise((resolve, reject) => {
      function cleanup() {
        worker.off('message', receive);
        worker.off('error', fail);
      }
      function fail(error) {
        cleanup();
        reject(error);
      }
      function receive(reply) {
        if (reply.type === 'error') return fail(new Error(reply.message));
        if (matches(reply)) {
          cleanup();
          resolve(reply);
        }
      }
      worker.on('message', receive);
      worker.once('error', fail);
      worker.postMessage(message);
    });
  }
  let request = 0;
  return {
    requests,
    registry: () => registry,
    load: type => send({ type }, m => m.type === 'progress' && !m.loading),
    search(options = {}, extra = {}) {
      const id = ++request;
      return send({ type: 'search', request: id, options, limit: 100, ...extra },
        m => m.type === 'results' && m.request === id);
    },
    detail: id => send({ type: 'detail', id }, m => m.type === 'detail' && m.item.id === id),
  };
}

for (const brotli of [true, false]) {
  const name = brotli ? 'Brotli download' : 'gzip download with retry';
  test('browser worker searches the shipped index via ' + name, { timeout: 30000 }, async t => {
    const url = brotli ? manifest.brotliUrl : manifest.gzipUrl;
    const worker = startWorker(t, brotli, brotli ? [] : [url]);
    const previewReady = await worker.load('init');
    assert.equal(previewReady.primaryReady, true);
    assert.deepEqual(previewReady.loaded, []);
    assert.deepEqual(worker.registry().collections.map(c => c.id), manifest.collections.map(c => c.id));
    assert.equal(worker.registry().rowCount, manifest.rowCount);
    assert.deepEqual(worker.requests, [manifestUrl, material.previewCatalog]);

    const preview = await worker.search();
    assert.equal(preview.total, 100);
    assert.deepEqual(preview.items.map(item => item.id), firstPage.map(item => item.id));
    let ready = await worker.load('continue');
    if (!brotli) {
      assert.ok(ready.failed.length);
      assert.deepEqual((await worker.search()).items, preview.items);
      assert.deepEqual(worker.requests, [manifestUrl, material.previewCatalog, url]);
      ready = await worker.load('retry');
    }
    assert.deepEqual(ready.failed, []);
    assert.deepEqual(ready.loaded, manifest.collections.map(c => c.id));
    const loadRequests = [manifestUrl, material.previewCatalog, url];
    if (!brotli) loadRequests.push(url);
    assert.deepEqual(worker.requests, loadRequests);

    const first = await worker.search();
    assert.ok(first.total > material.count);
    assert.deepEqual(first.items.map(({ id, name, kind, glyph }) => ({ id, name, kind, glyph })),
      firstPage.map(({ id, name, kind, glyph }) => ({ id, name, kind, glyph })));
    const filtered = await worker.search({ query: 'cat', collections: ['lucide'] });
    assert.ok(filtered.items.some(item => item.id === 'lucide:cat' && item.src));
    assert.ok(filtered.items.every(item => item.collection === 'lucide'));

    const all = await worker.search({ query: 'cat' }, { limit: 20, selected: localId });
    assert.equal(all.selected.emoji, '😀');
    const nextPage = await worker.search({ query: 'cat' }, { limit: 40 });
    assert.equal(nextPage.total, all.total);
    assert.equal(nextPage.items.length, 40);
    assert.deepEqual(nextPage.items.slice(0, 20), all.items);
    const remote = await worker.search({ query: publicId }, { selected: publicId });
    assert.deepEqual(remote.matches[0], [publicId, 'exact']);
    assert.deepEqual(remote.selected, remote.items[0]);
    assert.equal(remote.selected.src, 'https://api.iconify.design/mdi/home.svg');
    const remoteDetail = (await worker.detail(publicId)).item;
    assert.ok(remoteDetail.keywords.includes('mdi'));
    assert.equal(remoteDetail.src, remote.selected.src);
    assert.deepEqual(worker.requests, loadRequests);

    const unicode = manifest.collections.find(c => c.id === 'unicode');
    const source = read(unicode.catalog).find(item => item.id === localId);
    const detail = (await worker.detail(localId)).item;
    assert.deepEqual(detail.keywords, source.keywords);
    assert.equal(detail.subgroup, source.subgroup);
    assert.deepEqual(worker.requests, [...loadRequests, unicode.catalog]);
  });
}
