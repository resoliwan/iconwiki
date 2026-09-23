import test from 'node:test';
import assert from 'node:assert/strict';
import { prepareCatalog } from '../catalog.js';
import { buildSmartResults, ChromeSmartSearch, guessLanguageFromScript, isDesktopChrome, localTranslation, sanitizeExpansion } from '../smart-search.js';

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

test('AI support is limited to desktop Google Chrome', () => {
  assert.equal(isDesktopChrome({
    userAgent: 'Mozilla/5.0 Chrome/148.0.0.0 Safari/537.36',
    userAgentData: { brands: [{ brand: 'Google Chrome', version: '148' }], mobile: false },
  }), true);
  assert.equal(isDesktopChrome({
    userAgent: 'Mozilla/5.0 Edg/148.0.0.0 Chrome/148.0.0.0 Safari/537.36',
    userAgentData: { brands: [{ brand: 'Microsoft Edge', version: '148' }, { brand: 'Chromium', version: '148' }], mobile: false },
  }), false);
  assert.equal(isDesktopChrome({
    userAgent: 'Mozilla/5.0 (Linux; Android 16) Chrome/148.0.0.0 Mobile Safari/537.36',
    userAgentData: { brands: [{ brand: 'Google Chrome', version: '148' }], mobile: true },
  }), false);
});

test('Chrome AI preparation checks availability with the same model options and shares one session', async () => {
  let createCalls = 0;
  let availabilityOptions;
  let createOptions;
  const smart = new ChromeSmartSearch({
    LanguageModel: {
      availability: async options => {
        availabilityOptions = options;
        return 'available';
      },
      create: async options => {
        createCalls++;
        createOptions = options;
        await Promise.resolve();
        return { prompt: async () => JSON.stringify({ terms: [] }) };
      },
    },
  }, null);
  const first = smart.prepare();
  const second = smart.prepare();
  assert.equal(await first, await second);
  assert.equal(createCalls, 1);
  assert.deepEqual(availabilityOptions, {
    expectedInputs: [{ type: 'text', languages: ['en'] }],
    expectedOutputs: [{ type: 'text', languages: ['en'] }],
  });
  assert.deepEqual(createOptions.expectedInputs, availabilityOptions.expectedInputs);
  assert.deepEqual(createOptions.expectedOutputs, availabilityOptions.expectedOutputs);
});

test('common foreign visual words have an instant English fallback', () => {
  assert.equal(localTranslation(String.fromCodePoint(0xC5BC, 0xAD74), 'ko'), 'face');
  assert.equal(localTranslation(String.fromCodePoint(0xB098, 0xBB34), 'ko'), 'tree');
  assert.equal(localTranslation(String.fromCodePoint(0x9854), 'ja'), 'face');
});

test('ASCII searches stay English instead of relying on language detection', async () => {
  let detectionCalls = 0;
  const smart = new ChromeSmartSearch({
    LanguageDetector: {
      create: async () => ({
        detect: async () => {
          detectionCalls++;
          return [{ detectedLanguage: 'mi', confidence: 0.9 }];
        },
      }),
    },
    LanguageModel: {
      create: async () => ({ prompt: async () => JSON.stringify({ terms: ['animal'] }) }),
    },
  }, null);

  const result = await smart.expand('kangaroo');
  assert.equal(result.sourceLanguage, 'en');
  assert.equal(detectionCalls, 0);
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

test('prefix matches can be selected as their own result range', () => {
  const catalog = prepareCatalog([
    { id: 'kangaroo', collection: 'test', kind: 'image', src: 'kangaroo.svg', name: 'kangaroo' },
    { id: 'kanban', collection: 'test', kind: 'image', src: 'kanban.svg', name: 'kanban' },
  ]);
  assert.deepEqual(buildSmartResults(catalog, { query: 'kan' }, null, 'prefix').results.map(item => item.id), [
    'kangaroo',
    'kanban',
  ]);
  assert.deepEqual(buildSmartResults(catalog, { query: 'kan' }, null, 'exact').results, []);
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

test('smart search stays quiet when built-in AI cannot start', async () => {
  const scope = {
    LanguageDetector: { create: async () => { throw new Error('user gesture required'); } },
    LanguageModel: { create: async () => { throw new Error('user gesture required'); } },
  };
  const smart = new ChromeSmartSearch(scope, null);
  const result = await smart.expand('face');
  assert.equal(result.sourceLanguage, 'en');
  assert.deepEqual(result.terms, []);
  assert.equal(result.unavailable, true);
});

test('downloadable Chrome AI waits for an active user interaction', async () => {
  let createCalls = 0;
  const smart = new ChromeSmartSearch({
    navigator: { userActivation: { isActive: false } },
    LanguageModel: {
      availability: async () => 'downloadable',
      create: async () => {
        createCalls++;
        return { prompt: async () => JSON.stringify({ terms: ['happy'] }) };
      },
    },
  }, null);
  const result = await smart.expand('smile');
  assert.equal(createCalls, 0);
  assert.deepEqual(result.terms, []);
  assert.equal(result.unavailable, true);
});


test('multi-word direct matches stay AND while AI suggestions remain separate', () => {
  const catalog = prepareCatalog([
    { id: 'both', collection: 'test', kind: 'image', src: 'a.svg', name: 'cat', keywords: ['black'] },
    { id: 'cat-only', collection: 'test', kind: 'image', src: 'b.svg', name: 'cat', keywords: ['white'] },
    { id: 'black-only', collection: 'test', kind: 'image', src: 'c.svg', name: 'dog', keywords: ['black'] },
  ]);
  const expansion = { englishQuery: 'cat', terms: ['dog', 'white'] };
  for (const query of ['black cat', 'cat black', '  CAT   black  ', 'cat\tblack', 'cat　black']) {
    for (const activeExpansion of [null, expansion]) {
      const result = buildSmartResults(catalog, { query }, activeExpansion);
      assert.deepEqual([...result.directIds], ['both']);
      assert.deepEqual(buildSmartResults(catalog, { query }, activeExpansion, 'keyword').results.map(item => item.id), ['both']);
      assert.equal(result.relatedIds.size, activeExpansion ? 2 : 0);
    }
  }
  assert.equal(buildSmartResults(catalog, { query: 'cat missing' }, expansion).directIds.size, 0);
});


test('explicit refresh regenerates expansions instead of returning cached terms', async () => {
  const values = new Map();
  let calls = 0;
  const smart = new ChromeSmartSearch({
    LanguageModel: { create: async () => ({ prompt: async () => {
      calls++;
      return JSON.stringify({ terms: [calls === 1 ? 'happy face' : 'smiling face'] });
    } }) },
  }, { getItem: key => values.get(key), setItem: (key, value) => values.set(key, value) });
  const first = await smart.expand('smile face', 'en');
  assert.deepEqual(first.terms, ['happy face']);
  const cached = await smart.expand('smile face', 'en');
  assert.equal(cached.cached, true);
  assert.equal(calls, 1);
  const refreshed = await smart.expand('smile face', 'en', null, null, { refresh: true });
  assert.deepEqual(refreshed.terms, ['smiling face']);
  assert.equal(calls, 2);
});
