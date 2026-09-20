import test from 'node:test';
import assert from 'node:assert/strict';
import { prepareCatalog, searchCatalog } from '../catalog.js';
import { emptyMatching, isEnglishText, upsertMatch, validateMatching } from '../matching.js';

const items = prepareCatalog([
  { id: 'unicode:1F408', collection: 'unicode', kind: 'emoji', emoji: '🐈', name: 'cat', keywords: ['animal', 'pet'], group: 'Animals & Nature', skinTone: false },
  { id: 'unicode:1F431', collection: 'unicode', kind: 'emoji', emoji: '🐱', name: 'cat face', keywords: ['cat', 'face', 'pet'], group: 'Animals & Nature', skinTone: false },
  { id: 'unicode:1FA9D', collection: 'unicode', kind: 'emoji', emoji: '🪝', name: 'hook', keywords: ['catch'], group: 'Objects', skinTone: false },
  { id: 'unicode:1F3FB', collection: 'unicode', kind: 'emoji', emoji: '🏻', name: 'light skin tone', keywords: ['skin'], group: 'Component', status: 'component', skinTone: true },
  { id: 'material-symbols-outlined:pets', collection: 'material-symbols-outlined', kind: 'font', glyph: 'pets', name: 'pets', keywords: ['animal', 'cat', 'dog'], group: 'Social' },
]);

test('direct name matches rank before exact keyword matches', () => {
  assert.deepEqual(searchCatalog(items, { query: 'cat' }).map(item => item.id), ['unicode:1F408', 'unicode:1F431', 'material-symbols-outlined:pets']);
});

test('multiple terms must all match', () => {
  assert.deepEqual(searchCatalog(items, { query: 'cat face' }).map(item => item.id), ['unicode:1F431']);
});

test('plain words that look hexadecimal do not match icon codepoints', () => {
  const codepointLike = prepareCatalog([
    { id: 'x', collection: 'test', kind: 'image', src: 'x.svg', name: 'alignment', keywords: ['layout'], codepoints: ['FACE'] },
  ]);
  assert.deepEqual(searchCatalog(codepointLike, { query: 'face' }), []);
  assert.deepEqual(searchCatalog(codepointLike, { query: 'U+FACE' }).map(item => item.id), ['x']);
});

test('search does not match word prefixes or standalone components', () => {
  assert.equal(searchCatalog(items, { query: 'cat' }).some(item => item.id === 'unicode:1FA9D'), false);
  assert.equal(searchCatalog(items, { query: 'skin', skinTones: true }).some(item => item.id === 'unicode:1F3FB'), false);
});

test('font icons use the same search and collection filter', () => {
  assert.deepEqual(searchCatalog(items, { query: 'dog', collection: 'material-symbols-outlined' }).map(item => item.id), ['material-symbols-outlined:pets']);
});

test('license class filter limits results independently from text search', () => {
  const licensed = prepareCatalog([
    { id: 'p', collection: 'permissive-set', licenseClass: 'permissive', kind: 'image', src: 'p.svg', name: 'cat', keywords: ['pet'] },
    { id: 'a', collection: 'attribution-set', licenseClass: 'attribution', kind: 'image', src: 'a.svg', name: 'cat', keywords: ['pet'] },
  ]);
  assert.deepEqual(searchCatalog(licensed, { query: 'cat', licenseClass: 'attribution' }).map(item => item.id), ['a']);
});

test('matching values must use English text', () => {
  assert.equal(isEnglishText('a small domesticated animal'), true);
  assert.equal(isEnglishText('\uD55C\uAE00'), false);
  const valid = upsertMatch(emptyMatching(), { word: 'cat', meaning: 'a pet animal', assetId: 'unicode:1F408', status: 'pending_review' });
  assert.equal(valid.matches.length, 1);
  assert.throws(() => validateMatching({ schemaVersion: 1, matches: [{ word: 'cat', meaning: '\uD55C\uAE00', assetId: 'unicode:1F408', status: 'pending_review' }] }), /English/);
});
