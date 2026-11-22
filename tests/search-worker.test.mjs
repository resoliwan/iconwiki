import test from 'node:test';
import assert from 'node:assert/strict';
import { Worker } from 'node:worker_threads';
import { readFileSync } from 'node:fs';
test('worker renders the preview, retries the remainder, and preserves search order and deep links', async t => {
  const remainder = './data/material-symbols-remaining.json';
  const worker = new Worker(new URL('./helpers/worker-host.mjs', import.meta.url), {
    workerData: { root: new URL('../', import.meta.url).href, failOnce: [remainder] },
  });
  t.after(() => worker.terminate());
  const messages = [], waiting = [];
  worker.on('message', message => {
    messages.push(message);
    for (const entry of [...waiting]) if (entry.match(message)) { waiting.splice(waiting.indexOf(entry),1); entry.resolve(message); }
  });
  const next = match => new Promise(resolve => waiting.push({match,resolve}));
  let ready = next(m => m.type === 'progress' && m.primaryReady);
  worker.postMessage({type:'init', usePreview:true});
  assert.deepEqual((await ready).loaded, []);
  assert.deepEqual(messages.filter(m=>m.type==='requested').map(m=>m.url), ['./data/collections.json','./data/material-symbols-preview.json']);
  const search = async (request, options = {}, extra = {}) => {
    const reply = next(m=>m.type==='results' && m.request===request);
    worker.postMessage({type:'search',request,options:{skinTones:false,...options},limit:100,withinFilter:'',resultType:'all',...extra});
    return reply;
  };
  const material = JSON.parse(readFileSync(new URL('../data/material-symbols-outlined.json', import.meta.url)));
  const primary = await search(1);
  assert.equal(primary.total,100);
  assert.deepEqual(primary.items.map(item=>item.id), material.slice(0,100).map(item=>item.id));
  ready = next(m=>m.type==='progress' && !m.loading);
  worker.postMessage({type:'continue'});
  const partial = await ready;
  assert.equal(partial.loaded.length, 57);
  assert.deepEqual(partial.failed, ['material-symbols-outlined']);
  const partialMaterial = await search(6, {collections:['material-symbols-outlined']});
  assert.deepEqual(partialMaterial.items, primary.items);
  const beforeRetry = messages.length;
  ready = next(m=>m.type==='progress' && !m.loading);
  worker.postMessage({type:'retry'});
  assert.equal((await ready).loaded.length, 58);
  assert.deepEqual(messages.slice(beforeRetry).filter(m=>m.type==='requested').map(m=>m.url), [remainder]);
  const requests = messages.filter(m=>m.type==='requested').map(m=>m.url);
  assert.ok(!requests.includes('./data/material-symbols-outlined.json'));
  const complete = await search(7,{collections:['material-symbols-outlined']},{limit:material.length,selected:material.at(-1).id});
  assert.deepEqual(complete.items,material.map(item=>({...item,licenseClass:'permissive'})));
  assert.equal(complete.selected.id,material.at(-1).id);
  const all = await search(2,{query:'cat'}, {selected:'unicode:1F600'});
  assert.equal(all.total,491);
  assert.equal(all.items.length,100);
  assert.equal(all.selected.id,'unicode:1F600');
  assert.ok(!('_names' in all.items[0]));
  const page = await search(3,{query:'cat'},{limit:200});
  assert.equal(page.items.length,200);
  assert.deepEqual(page.items.slice(0,100),all.items);
  const browse = await search(4);
  assert.equal(browse.total,138789);
  assert.ok(browse.items.every(item=>item.collection==='material-symbols-outlined'));
  const filtered = await search(5,{query:'cat',collections:['lucide']});
  assert.ok(filtered.items.every(item=>item.collection==='lucide'));
});
