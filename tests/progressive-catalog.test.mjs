import test from 'node:test';
import assert from 'node:assert/strict';
import { loadProgressively, PRIMARY_COLLECTION } from '../progressive-catalog.js';
const collections = ['a', PRIMARY_COLLECTION, 'b', 'c', 'd'].map(id => ({ id, catalog: id, licenseClass: 'permissive' }));
const raw = id => [{ id, collection: id, name: id, kind: 'emoji', emoji: '😀' }];
test('Material is the only request until first-paint acknowledgement; remainder is bounded', async () => {
  const requested = [], accepted = [];
  let release, reached, active = 0, peak = 0;
  const gate = new Promise(resolve => { release = resolve; });
  const atGate = new Promise(resolve => { reached = resolve; });
  const loading = loadProgressively(collections, {
    read: async id => { requested.push(id); peak = Math.max(peak, ++active); await new Promise(r => setTimeout(r, 5)); active--; return raw(id); },
    accept: (collection, items) => { accepted.push(collection.id); assert.equal(items[0].licenseClass, 'permissive'); },
    failed: () => assert.fail('unexpected failure'),
    primaryReady: async () => { reached(); await gate; }, concurrency: 2,
  });
  await atGate;
  assert.deepEqual(requested, [PRIMARY_COLLECTION]);
  assert.deepEqual(accepted, [PRIMARY_COLLECTION]);
  release(); await loading;
  assert.equal(peak, 2);
  assert.equal(accepted.length, 5);
});
test('failed primary does not block other libraries and a failed library can retry alone', async () => {
  const accepted = [], failed = [];
  await loadProgressively(collections, {
    read: async id => { if (id === PRIMARY_COLLECTION) throw Error('offline'); return raw(id); },
    accept: c => accepted.push(c.id), failed: c => failed.push(c),
    primaryReady: () => assert.fail('must not wait for failed primary'),
  });
  assert.equal(accepted.length, 4);
  await loadProgressively(failed, { read: async id => raw(id), accept: c => accepted.push(c.id), failed: () => assert.fail() });
  assert.equal(new Set(accepted).size, 5);
});
