import test from 'node:test';
import assert from 'node:assert/strict';
import { Worker } from 'node:worker_threads';
test('real worker gates background loading, preserves search counts, pages and resolves deep links', async t => {
  const worker = new Worker(new URL('./helpers/worker-host.mjs', import.meta.url), { workerData: { root: new URL('../', import.meta.url).href } });
  t.after(() => worker.terminate());
  const messages = [], waiting = [];
  worker.on('message', message => {
    messages.push(message);
    for (const entry of [...waiting]) if (entry.match(message)) { waiting.splice(waiting.indexOf(entry),1); entry.resolve(message); }
  });
  const next = match => new Promise(resolve => waiting.push({match,resolve}));
  let ready = next(m => m.type === 'progress' && m.loaded.length === 1);
  worker.postMessage({type:'init'});
  await ready;
  assert.deepEqual(messages.filter(m=>m.type==='requested').map(m=>m.url), ['./data/collections.json','./data/material-symbols-outlined.json']);
  const search = async (request, options = {}, extra = {}) => {
    const reply = next(m=>m.type==='results' && m.request===request);
    worker.postMessage({type:'search',request,options:{skinTones:false,...options},limit:100,withinFilter:'',resultType:'all',...extra});
    return reply;
  };
  const primary = await search(1,{query:'home'});
  assert.ok(primary.total>0);
  assert.ok(primary.items.every(item=>item.collection==='material-symbols-outlined'));
  ready = next(m=>m.type==='progress' && !m.loading);
  worker.postMessage({type:'continue'});
  await ready;
  const all = await search(2,{query:'cat'}, {selected:'unicode:1F600'});
  assert.equal(all.total,462);
  assert.equal(all.items.length,100);
  assert.equal(all.selected.id,'unicode:1F600');
  assert.ok(!('_names' in all.items[0]));
  const page = await search(3,{query:'cat'},{limit:200});
  assert.equal(page.items.length,200);
  assert.deepEqual(page.items.slice(0,100),all.items);
  const browse = await search(4);
  assert.equal(browse.total,117965);
  assert.ok(browse.items.every(item=>item.collection==='material-symbols-outlined'));
  const filtered = await search(5,{query:'cat',collections:['lucide']});
  assert.ok(filtered.items.every(item=>item.collection==='lucide'));
});
