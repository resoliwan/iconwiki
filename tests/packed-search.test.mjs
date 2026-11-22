import test from 'node:test';
import assert from 'node:assert/strict';
import { createPackedSearch } from '../packed-search.js';
import { encodeCollection, encodeBundle, decodeBundle } from '../scripts/search_index_codec.mjs';
import { filterCatalogItems, prepareCatalog } from '../catalog.js';
import { buildSmartResults } from '../smart-search.js';

function library(id, definitions) {
  const library = { id, namespace: 'local', name: 'Test icons', license: 'MIT', licenseClass: 'permissive' };
  const items = definitions.map(([slug, fields]) => ({
    collection: id, id: id + ':' + slug, kind: 'image', src: './test.svg', name: slug.replaceAll('-', ' '),
    licenseClass: 'permissive', ...fields,
  }));
  return { items, frame: encodeCollection(library, items) };
}

const packA = library('one', [
  ['arrow', { group: 'Main', keywords: ['go right', 'moving'] }],
  ['arrow-right', { group: 'Main', emoji: '➡️', codepoints: ['27A1', 'FE0F'] }],
  ['chevron', { keywords: ['turn', 'right arrow'] }],
  ['rightward', { keywords: ['arrow'] }],
  ['arrowhead', { keywords: ['turning'] }],
  ['crook', { keywords: ['arrowhead'] }],
  ['hyphen', { name: 'arrow-right' }],
  ['slash', { name: '（＿）' }],
  ['swatch', { status: 'component', keywords: ['arrow'] }],
  ['tinted', { skinTone: true, keywords: ['arrow'] }],
  ['locked', { licenseClass: 'restricted', keywords: ['arrow'] }],
]);
const packB = library('two', [
  ['arrow', {}], ['turn', { keywords: ['right', 'arrow'] }],
]);
const blocks = [...decodeBundle(encodeBundle([packA.frame, packB.frame]))];
const items = prepareCatalog([...packA.items, ...packB.items]);
const engine = createPackedSearch(blocks);

function idOf({ block, index }) {
  const row = block.rows[index];
  return (block.collectionId ?? block.id) + ':' + (Array.isArray(row) ? row[0] : row);
}

test('packed search preserves catalog ranking, smart results and filter membership', () => {
  const cases = [
    ...['', 'arrow', 'a', 'arr', 'go right', 'ar ri', 'arrow arrow', 'arrow-r', 'arrow-right',
      'ＡＲＲＯＷ', '➡', '0x27a1 U+FE0F', '(_)', 'ONE:CHEVRON', 'no-such-word'].map(query => ({ options: { query } })),
    { options: { query: 'arrow', group: 'Main', collection: 'one' } },
    { options: { query: 'arrow', skinTones: false, collections: ['one'], licenseClasses: ['permissive'] } },
    { options: { query: '', collections: [] } },
    { options: { query: '', licenseClasses: [] } },
    { options: { query: 'arrow', licenseClass: 'restricted' } },
    { options: { query: '화살표' }, expansion: { sourceLanguage: 'ko', englishQuery: 'arrow', terms: ['turn', 'chevron'] } },
    { options: { query: 'right arrow' }, expansion: { englishQuery: 'crook', terms: ['turn', 'right'] }, withinFilter: 'ar' },
  ];
  for (const data of cases) {
    for (const resultType of ['all', 'exact', 'keyword', 'prefix', 'similar']) {
      const expected = buildSmartResults(items, data.options, data.expansion, resultType);
      const members = filterCatalogItems(expected.results, data.withinFilter);
      for (const limit of [1, 50]) {
        const { total, visible, selected } = engine.search({ ...data, resultType, limit, selected: 'one:swatch' });
        const message = JSON.stringify({ ...data, resultType, limit });
        assert.equal(total, members.length, message);
        assert.deepEqual(visible.map(hit => [idOf(hit), hit.matchType, hit.relatedTerm]),
          members.slice(0, limit).map(({ id }) => [id, expected.matchTypeById.get(id), expected.relatedTermById.get(id)]), message);
        assert.equal(idOf(selected), 'one:swatch');
      }
    }
  }
});

test('smart search applies the 120-per-term cap before excluding direct matches and filtering within', () => {
  const { frame } = library('bulk', Array.from({ length: 125 }, (_, i) =>
    ['row-' + i, { keywords: ['turn', ...(i === 0 ? ['direct'] : []), ...(i === 119 || i === 120 ? ['edge'] : [])] }]));
  const search = createPackedSearch([...decodeBundle(encodeBundle([frame]))]);
  const data = { options: { query: 'direct' }, expansion: { terms: ['turn', 'turn'] }, resultType: 'similar' };
  assert.equal(search.search(data).total, 119);
  const { visible } = search.search({ ...data, withinFilter: 'edge' });
  assert.deepEqual(visible.map(idOf), ['bulk:row-119']);
});

test('selected IDs and exact ID matches use the public collection namespace', () => {
  const remoteBlock = { ...blocks[1], collectionId: 'iconify-two', classes: [''], defaultClass: 'restricted' };
  const search = createPackedSearch([blocks[1], remoteBlock]);
  const { visible, selected } = search.search({
    options: { query: 'ICONIFY-TWO:ARROW', licenseClasses: ['restricted'] }, selected: 'two:turn',
  });
  assert.deepEqual(visible.map(hit => [idOf(hit), hit.matchType]), [['iconify-two:arrow', 'exact']]);
  assert.equal(idOf(selected), 'two:turn');
  assert.equal(search.resolveId('unknown:arrow'), null);
});
