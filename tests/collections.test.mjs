import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { prepareCatalog } from '../catalog.js';

const root = path.resolve(import.meta.dirname, '..');

test('every registered collection has valid unique assets', () => {
  const collections = JSON.parse(fs.readFileSync(path.join(root, 'data/collections.json'), 'utf8'));
  const licenseClasses = new Set(['permissive', 'attribution', 'restricted']);
  const feeds = JSON.parse(fs.readFileSync(path.join(root, 'data/sources/feed-packs.json'), 'utf8'));
  assert.equal(collections.length, 103);
  assert.equal(collections.find(collection => collection.id === 'noto-emoji')?.name, 'Noto Color Emoji');
  assert.equal(collections.find(collection => collection.id === 'noto-emoji-monochrome')?.name, 'Noto Emoji');
  assert.equal(fs.existsSync(path.join(root, 'assets/noto-emoji-monochrome/NotoEmoji-Regular.ttf')), true);
  const items = [];
  for (const collection of collections) {
    assert.equal(licenseClasses.has(collection.licenseClass), true, `invalid license class for ${collection.id}`);
    if (['sf-symbols', 'segoe-fluent-icons'].includes(collection.id)) {
      assert.equal(collection.licenseClass, 'restricted');
      assert.equal(new URL(collection.licenseUrl).hostname, collection.id === 'sf-symbols' ? 'developer.apple.com' : 'learn.microsoft.com');
    } else assert.equal(fs.existsSync(path.resolve(root, collection.licenseUrl.replace(/^\.\//, ''))), true, `missing ${collection.licenseUrl}`);
    const catalogPath = path.resolve(root, collection.catalog.replace(/^\.\//, ''));
    assert.equal(fs.existsSync(catalogPath), true, `missing ${collection.catalog}`);
    const catalog = JSON.parse(fs.readFileSync(catalogPath, 'utf8'));
    assert.ok(catalog.length > 0, `empty ${collection.id}`);
    for (const item of catalog) {
      assert.equal(item.collection, collection.id, `${item.id} has wrong collection`);
      if (item.licenseClass) assert.equal(licenseClasses.has(item.licenseClass), true, `${item.id} has invalid license class`);
      if (item.kind === 'image') {
        if (item.src.startsWith('https://')) {
          if (collection.id === 'segoe-fluent-icons') {
            assert.match(item.src, /^https:\/\/raw\.githubusercontent\.com\/MicrosoftDocs\/windows-dev-docs\/[a-f0-9]{40}\/hub\/apps\/design\/iconography\/images\/segoe-fluent-icons\/[a-f0-9]+\.png$/i);
            continue;
          }
          const feed = feeds[collection.id];
          assert.ok(feed && /^[a-f0-9]{40}$/.test(feed.commit), `unknown image source for ${item.id}`);
          assert.ok(item.src.startsWith(`https://raw.githubusercontent.com/${feed.repo}/${feed.commit}/`), item.src);
          assert.match(new URL(item.src).pathname, /\.(?:svg|png)$/i);
        } else {
          assert.equal(fs.existsSync(path.resolve(root, item.src.replace(/^\.\//, ''))), true, `missing ${item.src}`);
        }
      }
    }
    items.push(...catalog);
  }
  assert.equal(prepareCatalog(items).length, 177_993);
  const coreui = items.filter(item => item.collection === 'coreui-icons-free');
  assert.equal(coreui.filter(item => item.licenseClass === 'attribution').length, 554);
  assert.equal(coreui.filter(item => item.licenseClass === 'restricted').length, 1029);
});
