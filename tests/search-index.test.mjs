import test from 'node:test';
import assert from 'node:assert/strict';
import {
  encodeCollection,
  encodeBundle,
  decodeBundle,
  NAME_TOKEN,
  KEYWORD_TOKEN,
  KEYWORD_PHRASE,
} from '../scripts/search_index_codec.mjs';

test('packed index preserves stable IDs, display fields, and ranked word and phrase matches across byte boundaries', () => {
  const meta = { namespace: 'local', id: 'test', name: 'Test', license: 'MIT', licenseClass: 'permissive' };
  const items = Array.from({ length: 140 }, (_, i) => ({ id: 'test:icon-' + i, name: 'icon ' + i }));
  items[0].keywords = ['ＨＯＭＥ', 'go home'];
  Object.assign(items[139], {
    name: 'Home!',
    keywords: ['go home'],
    group: 'Faces',
    emoji: '😀',
    codepoints: ['1F600'],
    skinTone: true,
    licenseClass: 'restricted',
  });
  const frame = encodeCollection(meta, items);
  const [block, other] = [
    ...decodeBundle(encodeBundle([frame, encodeCollection({ ...meta, namespace: 'iconify' }, items)])),
  ];
  assert.equal(other.namespace, 'iconify');
  assert.equal(block.rows[0], 'icon-0');
  assert.deepEqual(block.rows[139], ['icon-139', 'Home!', 1, 1, 1, '😀', '1F600']);
  assert.deepEqual(block.classes, ['permissive', 'restricted']);
  assert.deepEqual(block.groups, ['', 'Faces']);
  assert.deepEqual(Array.from(block.postings.get('home')), [
    KEYWORD_TOKEN | KEYWORD_PHRASE,
    139 * 8 + KEYWORD_TOKEN,
  ]);
  assert.deepEqual(Array.from(block.postings.get('go home')), [KEYWORD_PHRASE, 139 * 8 + KEYWORD_PHRASE]);
  assert.deepEqual(Array.from(block.postings.get('home!')), [139 * 8 + NAME_TOKEN]);
  assert.throws(() => [...decodeBundle(encodeBundle([frame]).subarray(0, -1))], /Truncated/);
});

test('packed cards render local artwork and recover selected details from the original catalog', async () => {
  const { packedItem, hydratePackedItem } = await import('../packed-index.js');
  const meta = { namespace: 'local', id: 'ui', name: 'UI', license: 'MIT', licenseClass: 'permissive', catalog: 'data/ui.json' };
  const original = {
    id: 'ui:home:filled', collection: 'ui', name: 'home (filled)', kind: 'image', src: './assets/ui/filled/home.svg',
    variant: 'filled', colored: true, keywords: ['Homepage'], author: 'Designer',
  };
  const [block] = decodeBundle(encodeBundle([encodeCollection(meta, [original])]));
  block.metadata = meta;
  assert.equal(packedItem(block, 0).src, original.src);
  assert.equal(packedItem(block, 0).colored, true);
  assert.equal(packedItem(block, 0).variant, 'filled');
  const details = await hydratePackedItem(block, 0, async () => Response.json([original]));
  assert.deepEqual(details.keywords, original.keywords);
  assert.equal(details.attribution, 'Designer');
});

test('Iconify details resolve artwork, author, and searchable aliases from the bundle', async () => {
  const { hydratePackedItem } = await import('../packed-index.js');
  const meta = { namespace: 'iconify', id: 'iconify-test', prefix: 'test', name: 'Test', author: 'Designer',
    license: 'MIT', licenseClass: 'permissive', palette: false };
  const [block] = decodeBundle(encodeBundle([encodeCollection(meta, [
    { id: 'iconify-test:home', name: 'home', keywords: ['home', 'house', 'go home'] },
  ])]));
  block.metadata = meta;
  const item = await hydratePackedItem(block, 0, () => assert.fail('Unexpected network request'));
  assert.equal(item.src, 'https://api.iconify.design/test/home.svg');
  assert.equal(item.monochrome, true);
  assert.deepEqual(item.keywords, ['go home', 'home', 'house']);
  assert.equal(item.author, 'Designer');
});
