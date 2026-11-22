import { artworkURL } from './iconify-source.js';
import { decodeBundle, KEYWORD_PHRASE } from './scripts/search_index_codec.mjs';

function supportedCompression() {
  try {
    new DecompressionStream('brotli');
    return 'brotli';
  } catch {
    return 'gzip';
  }
}

export async function loadPackedIndex(manifest, read = fetch) {
  if (manifest.version !== 1) throw Error('Unsupported search index version');
  const format = supportedCompression();
  const response = await read(format === 'brotli' ? manifest.brotliUrl : manifest.gzipUrl);
  if (!response.ok) {
    const error = new Error(`Search index download failed (${response.status})`);
    error.status = response.status;
    throw error;
  }
  // Static hosts can either send the stored bytes or mark the file as an HTTP
  // content encoding, in which case fetch has already decoded the payload.
  let bytes = new Uint8Array(await response.arrayBuffer());
  if (!(bytes.length === manifest.rawBytes && bytes[0] === 0x49)) {
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream(format));
    bytes = new Uint8Array(await new Response(stream).arrayBuffer());
  }
  if (bytes.length !== manifest.rawBytes) throw Error('Search index size mismatch');

  const blocks = [];
  for (const block of decodeBundle(bytes)) {
    const meta = manifest.collections[blocks.length];
    if (!meta || block.id !== meta.id || block.rows.length !== meta.count) throw Error('Search index and manifest disagree');
    block.metadata = meta;
    blocks.push(block);
  }
  if (blocks.length !== manifest.collectionCount) throw Error('Incomplete search index');
  return { manifest, blocks };
}

export function packedItem(block, rowIndex) {
  const raw = block.rows[rowIndex];
  const [slug, title, group = 0, cls = 0, flags = 0, emoji, codes, variant = 0, src, credit = 0, kind, glyph, license, licenseUrl, sourceUrl] =
    typeof raw === 'string' ? [raw] : raw;
  const meta = block.metadata;
  const item = {
    id: block.id + ':' + slug, collection: block.id, kind: kind || block.kind,
    name: title || slug.replaceAll('-', ' '),
    group: block.groups[group], licenseClass: block.classes[cls],
  };
  if (emoji) item.emoji = emoji;
  if (codes) item.codepoints = codes.split(' ');
  if (flags & 1) item.skinTone = true;
  if (flags & 2) item.status = 'component';
  if (flags & 4) item.colored = true;
  if (variant) item.variant = block.variants[variant];
  if (license) item.license = license;
  if (licenseUrl) item.licenseUrl = licenseUrl;
  if (sourceUrl) item.sourceUrl = sourceUrl;
  if (credit) item.attribution = block.credits[credit];
  if (meta.namespace === 'iconify') {
    item.artworkSet = artworkURL(meta.prefix);
    item.monochrome = !meta.palette;
    item.author = meta.author;
  } else if (item.kind === 'image') item.src = src || `./assets/${block.id}/${slug}.svg`;
  else if (item.kind === 'font') item.glyph = glyph || slug;
  return item;
}

// Iconify keywords already exist in the reverse index. Look up a single row
// there only when details open, keeping the search bundle free of forward lists.
function keywordsForRow(block, rowIndex) {
  const words = [];
  for (const [word, postings] of block.postings) {
    let start = 0, end = postings.length;
    while (start < end) {
      const mid = (start + end) >>> 1;
      if ((postings[mid] >>> 3) < rowIndex) start = mid + 1;
      else end = mid;
    }
    if (start < postings.length && postings[start] >>> 3 === rowIndex && (postings[start] & KEYWORD_PHRASE)) words.push(word);
  }
  return words;
}

let detailCatalog;
export async function hydratePackedItem(block, rowIndex, read = fetch) {
  const item = packedItem(block, rowIndex);
  if (block.namespace === 'iconify') {
    item.keywords = keywordsForRow(block, rowIndex);
    return item;
  }
  const url = block.metadata.catalog;
  // Keep only the most recently opened local library's extra metadata.
  if (detailCatalog?.url !== url) {
    const rows = Promise.resolve(read(url)).then(response => {
      if (!response.ok) throw Error(`Icon details download failed (${response.status})`);
      return response.json();
    });
    detailCatalog = { url, rows };
  }
  const pending = detailCatalog;
  try {
    const catalog = await pending.rows;
    const full = catalog[rowIndex]?.id === item.id ? catalog[rowIndex] : catalog.find(row => row.id === item.id);
    if (full) return { ...item, ...full };
  } catch {
    if (detailCatalog === pending) detailCatalog = null;
  }
  item.keywords = keywordsForRow(block, rowIndex);
  return item;
}
