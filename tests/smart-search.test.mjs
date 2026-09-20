import test from 'node:test';
import assert from 'node:assert/strict';
import { prepareCatalog } from '../catalog.js';
import { buildSmartResults, ChromeSmartSearch, guessLanguageFromScript, localTranslation, sanitizeExpansion } from '../smart-search.js';

const items = prepareCatalog([
  { id: 'a', collection: 'test', kind: 'image', src: 'a.svg', name: 'face', keywords: ['head'] },
  { id: 'b', collection: 'test', kind: 'image', src: 'b.svg', name: 'smile', keywords: ['happy', 'expression'] },
  { id: 'c', collection: 'test', kind: 'image', src: 'c.svg', name: 'jump', keywords: ['leap'] },
]);

test('script detection handles common non-Latin search words', () => {
  assert.equal(guessLanguageFromScript(String.fromCodePoint(0xACE0, 0xC591, 0xC774)), 'ko');
  assert.equal(guessLanguageFromScript(String.fromCodePoint(0x306D, 0x3053)), 'ja');
  assert.equal(guessLanguageFromScript(String.fromCodePoint(0x043A, 0x043E, 0x0442)), 'ru');
  assert.equal(guessLanguageFromScript('jump'), null);
});

test('common foreign visual words have an instant English fallback', () => {
  assert.equal(localTranslation(String.fromCodePoint(0xC5BC, 0xAD74), 'ko'), 'face');
  assert.equal(localTranslation(String.fromCodePoint(0xB098, 0xBB34), 'ko'), 'tree');
  assert.equal(localTranslation(String.fromCodePoint(0x9854), 'ja'), 'face');
});

test('expansion terms are English, unique, and exclude the query', () => {
  assert.deepEqual(sanitizeExpansion({ terms: ['Smile', 'face', 'smile', String.fromCodePoint(0xD45C, 0xC815), 'facial expression'] }, 'face'), ['smile', 'facial expression']);
});

test('exact, keyword, and similar results have separate match ranges', () => {
  const expansion = { englishQuery: 'face', terms: ['smile', 'expression'] };
  assert.deepEqual(buildSmartResults(items, { query: 'face' }, expansion, 'all').results.map(item => item.id), ['a', 'b']);
  assert.deepEqual(buildSmartResults(items, { query: 'face' }, expansion, 'exact').results.map(item => item.id), ['a']);
  assert.deepEqual(buildSmartResults(items, { query: 'face' }, expansion, 'keyword').results.map(item => item.id), []);
  assert.deepEqual(buildSmartResults(items, { query: 'face' }, expansion, 'similar').results.map(item => item.id), ['b']);
  assert.equal(buildSmartResults(items, { query: 'face' }, expansion).matchTypeById.get('b'), 'similar');
});

test('only expansion terms supplied by the active AI search contribute similar results', () => {
  const allTerms = { englishQuery: 'face', terms: ['smile', 'jump'] };
  const oneTerm = { ...allTerms, terms: ['jump'] };
  assert.deepEqual(buildSmartResults(items, { query: 'face' }, allTerms, 'similar').results.map(item => item.id), ['b', 'c']);
  assert.deepEqual(buildSmartResults(items, { query: 'face' }, oneTerm, 'similar').results.map(item => item.id), ['c']);
});

test('Chrome smart search translates foreign input before expanding English terms', async () => {
  const storageValues = new Map();
  const storage = {
    getItem: key => storageValues.get(key) || null,
    setItem: (key, value) => storageValues.set(key, value),
  };
  const scope = {
    LanguageModel: {
      create: async () => ({ prompt: async () => JSON.stringify({ terms: ['cat', 'pet', 'animal'] }) }),
    },
    Translator: {
      create: async options => ({
        translate: async () => options.sourceLanguage === 'ko' ? 'cat' : 'unknown',
      }),
    },
  };
  const smart = new ChromeSmartSearch(scope, storage);
  const result = await smart.expand(String.fromCodePoint(0xACE0, 0xC591, 0xC774));
  assert.equal(result.sourceLanguage, 'ko');
  assert.equal(result.englishQuery, 'cat');
  assert.deepEqual(result.terms, ['pet', 'animal']);
  assert.equal([...storageValues.values()].some(value => /[^\x00-\x7F]/.test(value)), false);
});

test('smart search falls back locally when built-in AI needs a user gesture', async () => {
  const scope = {
    LanguageDetector: { create: async () => { throw new Error('user gesture required'); } },
    LanguageModel: { create: async () => { throw new Error('user gesture required'); } },
  };
  const smart = new ChromeSmartSearch(scope, null);
  const result = await smart.expand('face');
  assert.equal(result.sourceLanguage, 'en');
  assert.deepEqual(result.terms, ['head', 'person', 'smile', 'expression', 'eyes', 'mouth', 'human']);
  assert.equal(result.local, true);
});
