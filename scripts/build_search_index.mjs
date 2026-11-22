// Build the static search bundle from the local catalogs and the pinned Iconify snapshot.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { brotliCompressSync, constants, gzipSync } from 'node:zlib';
import { encodeCollection, encodeBundle } from './search_index_codec.mjs';
import { PRIMARY_COLLECTION } from '../progressive-catalog.js';

const root = fileURLToPath(new URL('../', import.meta.url));
const { values } = parseArgs({ options: { out: { type: 'string' }, iconify: { type: 'string' } } });
const out = path.resolve(values.out || path.join(root, 'data/search'));
const snapshot = '2.2.560';
const integrity = 'YclhHQsi7GT88AOE0lVZFO5n1PKxEa8DImC3e8CHhWLbzQuVHR/i06IXP6Dw5nZWT38PFOKe4NeaHXYdFjbZdQ==';
const read = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

function fetchSnapshot(directory) {
  const name = '@iconify/json@' + snapshot;
  const packed = JSON.parse(execFileSync('npm', [
    'pack', name, '--ignore-scripts', '--pack-destination', directory, '--json',
  ], { encoding: 'utf8' }));
  const archive = path.join(directory, packed[0].filename);
  const hash = createHash('sha512').update(fs.readFileSync(archive)).digest('base64');
  if (hash !== integrity) throw Error('Unexpected checksum for ' + name);
  execFileSync('tar', ['-xzf', archive, '-C', directory]);
  return path.join(directory, 'package');
}

function licenseClass(info) {
  const id = info.license.spdx;
  if (info.category === 'Logos' || id.includes('-NC-') || /^(GPL|MPL)-/.test(id)) return 'restricted';
  if (id.startsWith('CC-BY')) return 'attribution';
  return 'permissive';
}

function officialCollection(prefix, info) {
  const license = info.license.spdx;
  const author = info.author.name;
  const credit = `${info.name} by ${author}. Licensed under ${license}.`;
  return {
    id: 'iconify-' + prefix, namespace: 'iconify', prefix, name: info.name,
    version: info.version || snapshot, author, license, licenseClass: licenseClass(info),
    sourceUrl: info.author.url || `https://icon-sets.iconify.design/${prefix}/`,
    licenseUrl: info.license.url || `https://spdx.org/licenses/${license}.html`,
    palette: Boolean(info.palette), category: info.category || '', note: credit,
  };
}

function officialRows(collection, info, data) {
  const aliases = data.aliases || {};
  const docs = new Map();
  const isEmoji = info.category === 'Emoji';
  function add(slug, icon) {
    docs.set(slug, {
      id: collection.id + ':' + slug,
      name: slug.replaceAll('-', ' '),
      keywords: [collection.prefix, info.name],
      skinTone: isEmoji && /(?:^|-)skin-tone(?:-|$)/.test(slug),
      status: isEmoji && /^(?:light|medium|medium-light|medium-dark|dark)-skin-tone$/.test(slug)
        ? 'component' : undefined,
      attribution: icon.attribution || icon.author?.name || (typeof icon.author === 'string' && icon.author) || '',
    });
  }
  for (const [slug, icon] of Object.entries(data.icons)) if (!icon.hidden) add(slug, icon);
  // Iconify counts transformed aliases as separate artwork. Unchanged aliases
  // add search terms to the canonical icon instead of duplicating the result.
  for (const [slug, a] of Object.entries(aliases)) {
    if (!a.hidden && (a.hFlip || a.vFlip || a.rotate || a.width || a.height || a.left || a.top)) add(slug, a);
  }
  function resolve(slug) {
    const seen = new Set();
    while (!docs.has(slug) && aliases[slug] && !seen.has(slug)) {
      seen.add(slug);
      slug = aliases[slug].parent;
    }
    return docs.get(slug);
  }
  for (const [slug, a] of Object.entries(aliases)) {
    if (!a.hidden && !docs.has(slug)) resolve(slug)?.keywords.push(slug, slug.replaceAll('-', ' '));
  }
  for (const [group, names] of Object.entries(data.categories || {})) {
    if (!group) continue;
    for (const slug of names) {
      const doc = resolve(slug);
      if (doc) {
        doc.group ||= group;
        doc.keywords.push(group);
      }
    }
  }
  for (const [hex, slug] of Object.entries(data.chars || {})) {
    const doc = resolve(slug);
    if (!doc) continue;
    const codes = hex.split('-');
    if (codes.every(code => /^[a-f0-9]{1,6}$/i.test(code))) {
      doc.keywords.push(codes.map(code => 'u+' + code.toLowerCase()).join(' '));
      doc.codepoints ||= codes.map(code => code.toUpperCase());
      if (info.category === 'Emoji' && !doc.emoji)
        doc.emoji = String.fromCodePoint(...codes.map(code => Number.parseInt(code, 16)));
    }
  }
  if (docs.size !== info.total) throw Error(`${collection.prefix}: ${docs.size} visible icons, expected ${info.total}`);
  return [...docs.values()];
}

function buildIndex(pkg) {
  const identity = read(path.join(pkg, 'package.json'));
  if (identity.name !== '@iconify/json' || identity.version !== snapshot) throw Error('Unexpected Iconify package version');
  const frames = [], collections = [], ids = new Set();
  function include(meta, rows) {
    if (ids.has(meta.id)) throw Error('Duplicate collection ' + meta.id);
    ids.add(meta.id);
    frames.push(encodeCollection(meta, rows));
    collections.push({ ...meta, count: rows.length });
  }
  const local = read(path.join(root, 'data/collections.json'));
  // Match the primary-first tie-break used by the preview and earlier worker.
  local.sort((a, b) => Number(b.id === PRIMARY_COLLECTION) - Number(a.id === PRIMARY_COLLECTION));
  for (const c of local) include({ ...c, namespace: 'local' }, read(path.join(root, c.catalog)));
  for (const [prefix, info] of Object.entries(read(path.join(pkg, 'collections.json')))) {
    if (info.hidden) continue;
    const c = officialCollection(prefix, info);
    include(c, officialRows(c, info, read(path.join(pkg, 'json', prefix + '.json'))));
  }

  const bytes = encodeBundle(frames);
  const hash = sha256(bytes);
  const basename = 'catalog-' + hash.slice(0, 16) + '.iwix';
  const br = brotliCompressSync(bytes, { params: { [constants.BROTLI_PARAM_QUALITY]: 9 } });
  const gz = gzipSync(bytes, { level: 6 });
  const manifest = {
    version: 1, iconifyPackage: '@iconify/json@' + snapshot, sha256: hash,
    brotliUrl: './data/search/' + basename + '.br', gzipUrl: './data/search/' + basename + '.gz',
    rawBytes: bytes.length, brotliBytes: br.length, gzipBytes: gz.length,
    collectionCount: collections.length, rowCount: collections.reduce((n, c) => n + c.count, 0),
    collections,
  };
  fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(path.join(out, basename + '.br'), br);
  fs.writeFileSync(path.join(out, basename + '.gz'), gz);
  const temporary = path.join(out, '.manifest-' + process.pid);
  fs.writeFileSync(temporary, JSON.stringify(manifest) + '\n');
  fs.renameSync(temporary, path.join(out, 'manifest.json'));
  console.log(`${manifest.rowCount} rows from ${manifest.collectionCount} collections; ${br.length} Brotli bytes, ${gz.length} gzip bytes.`);
}

if (values.iconify) buildIndex(path.resolve(values.iconify));
else {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'iconwiki-index-'));
  try { buildIndex(fetchSnapshot(directory)); }
  finally { fs.rmSync(directory, { recursive: true, force: true }); }
}
