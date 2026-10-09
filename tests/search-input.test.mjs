import test from 'node:test';
import assert from 'node:assert/strict';
import { bindSearchInput } from '../search-input.js';
function fixture(t) {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const input = new EventTarget(); input.value = '';
  const calls = [], changes = [];
  let invalidations = 0;
  const controller = bindSearchInput(input, { change: value => changes.push(value), invalidate: () => invalidations++, search: immediate => calls.push([input.value, immediate]) });
  const send = (type, props = {}) => { const event = new Event(type, { cancelable: true }); Object.assign(event, props); input.dispatchEvent(event); return event; };
  return { input, calls, changes, controller, send, invalidations: () => invalidations };
}
test('bursts search only the final query after 80 ms and invalidate old results immediately', t => {
  const f = fixture(t);
  for (const value of ['c','ca','cat']) { f.input.value = value; f.send('input'); t.mock.timers.tick(30); }
  assert.equal(f.invalidations(), 3);
  assert.deepEqual(f.calls, []);
  t.mock.timers.tick(50);
  assert.deepEqual(f.calls, [['cat',false]]);
  assert.equal(f.controller.pending,false);
});
test('Enter bypasses the delay without a duplicate automatic search', t => {
  const f = fixture(t); f.input.value='home'; f.send('input');
  assert.equal(f.send('keydown',{key:'Enter'}).defaultPrevented,true);
  assert.deepEqual(f.calls,[['home',true]]);
  t.mock.timers.tick(100);
  assert.equal(f.calls.length,1);
});
test('IME composition and its Enter do not search until committed', t => {
  const f = fixture(t); f.send('compositionstart');
  f.input.value='고'; f.send('input',{isComposing:true});
  assert.equal(f.send('keydown',{key:'Enter',isComposing:true}).defaultPrevented,false);
  t.mock.timers.tick(200); assert.deepEqual(f.calls,[]);
  f.input.value='고양이'; f.send('compositionend'); f.send('input');
  t.mock.timers.tick(80); assert.deepEqual(f.calls,[['고양이',false]]);
});
