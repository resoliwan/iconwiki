import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { prepareCatalog } from '../catalog.js';

const root = path.resolve(import.meta.dirname, '..');

test('every registered collection has valid unique assets', () => {
  const collections = JSON.parse(fs.readFileSync(path.join(root, 'data/collections.json'), 'utf8'));
  const licenseClasses = new Set(['permissive', 'attribution', 'restricted']);
  assert.equal(collections.length, 21);
  assert.equal(collections.find(collection => collection.id === 'noto-emoji')?.name, 'Noto Color Emoji');
  assert.equal(collections.find(collection => collection.id === 'noto-emoji-monochrome')?.name, 'Noto Emoji');
  assert.equal(fs.existsSync(path.join(root, 'assets/noto-emoji-monochrome/NotoEmoji-Regular.ttf')), true);
  const items = [];
  for (const collection of collections) {
    assert.equal(licenseClasses.has(collection.licenseClass), true, `invalid license class for ${collection.id}`);
    assert.equal(fs.existsSync(path.resolve(root, collection.licenseUrl.replace(/^\.\//, ''))), true, `missing ${collection.licenseUrl}`);
    const catalogPath = path.resolve(root, collection.catalog.replace(/^\.\//, ''));
    assert.equal(fs.existsSync(catalogPath), true, `missing ${collection.catalog}`);
    const catalog = JSON.parse(fs.readFileSync(catalogPath, 'utf8'));
    assert.ok(catalog.length > 0, `empty ${collection.id}`);
    for (const item of catalog) {
      assert.equal(item.collection, collection.id, `${item.id} has wrong collection`);
      if (item.licenseClass) assert.equal(licenseClasses.has(item.licenseClass), true, `${item.id} has invalid license class`);
      if (item.kind === 'image') {
        assert.equal(fs.existsSync(path.resolve(root, item.src.replace(/^\.\//, ''))), true, `missing ${item.src}`);
      }
    }
    items.push(...catalog);
  }
  assert.equal(prepareCatalog(items).length, 78_209);
});
