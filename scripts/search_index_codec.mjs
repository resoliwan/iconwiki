// IWIX v1: a sequence of length-prefixed collection headers and postings blocks.
// Each posting stores the local row-number delta and three field-match bits.
import { normalize } from '../catalog.js';

const magic = new TextEncoder().encode('IWIX\x01');
export const NAME_TOKEN = 1,
  KEYWORD_TOKEN = 2,
  KEYWORD_PHRASE = 4;
const tokens = (text) => text.split(/[\s_,;:()\-]+/).filter(Boolean);

function putVarint(bytes, value) {
  while (value >= 128) {
    bytes.push((value % 128) + 128);
    value = Math.floor(value / 128);
  }
  bytes.push(value);
}

function intern(list, value) {
  let i = list.indexOf(value);
  if (i === -1) {
    i = list.length;
    list.push(value);
  }
  return i;
}

export function encodeCollection({ namespace, id, name, license, licenseClass }, items) {
  const groups = [''],
    classes = [licenseClass],
    variants = [''],
    credits = [''],
    rows = [],
    terms = new Map();
  const kind = items[0]?.kind || 'image';
  for (const item of items) {
    const rowNumber = rows.length;
    if (!item.id.startsWith(id + ':')) throw Error('Unexpected ID: ' + item.id);
    const slug = item.id.slice(id.length + 1);
    // Empty trailing fields use their defaults. Slugs double as display names
    // when replacing hyphens with spaces reconstructs the original exactly.
    const row = [
      slug,
      item.name === slug.replaceAll('-', ' ') ? '' : item.name,
      intern(groups, item.group || ''),
      intern(classes, item.licenseClass || licenseClass),
      Number(!!item.skinTone) + 2 * Number(item.status === 'component') + 4 * Number(!!item.colored),
      item.emoji || '',
      (item.codepoints || []).join(' '),
      intern(variants, item.variant || ''),
      item.src && item.src !== `./assets/${id}/${slug}.svg` ? item.src : '',
      intern(credits, item.attribution || item.author || ''),
      item.kind && item.kind !== kind ? item.kind : '',
      item.glyph && item.glyph !== slug ? item.glyph : '',
      item.licenseUrl ? item.license || '' : '',
      item.licenseUrl || '',
      item.sourceUrl || '',
    ];
    while (row.length > 1 && !row.at(-1)) row.pop();
    rows.push(row.length === 1 ? slug : row);

    const fields = new Map();
    const mark = (word, bit) => fields.set(word, (fields.get(word) || 0) | bit);
    for (const word of tokens(normalize(item.name))) mark(word, NAME_TOKEN);
    for (const keyword of item.keywords || []) {
      const phrase = normalize(keyword);
      if (!phrase) continue;
      mark(phrase, KEYWORD_PHRASE);
      for (const word of tokens(phrase)) mark(word, KEYWORD_TOKEN);
    }
    for (const [term, mask] of fields) {
      if (!terms.has(term)) terms.set(term, []);
      terms.get(term).push(rowNumber * 8 + mask);
    }
  }
  const dictionary = [...terms.keys()].sort(),
    bytes = [];
  for (const term of dictionary) {
    const list = terms.get(term);
    putVarint(bytes, list.length);
    let previous = 0;
    for (const packed of list) {
      putVarint(bytes, packed - previous * 8);
      previous = Math.floor(packed / 8);
    }
  }
  const header = Buffer.from(
    JSON.stringify({ namespace, id, name, license, kind, groups, classes, variants, credits, rows, dictionary }),
  );
  const sizes = Buffer.alloc(8);
  sizes.writeUInt32LE(header.length, 0);
  sizes.writeUInt32LE(bytes.length, 4);
  return Buffer.concat([sizes, header, Buffer.from(bytes)]);
}

export function encodeBundle(frames) {
  return Buffer.concat([magic, ...frames]);
}

// Iterate one decoded collection at a time for inspection or a search client.
// Input is the decompressed Uint8Array, suitable for use in a browser worker.
export function* decodeBundle(input) {
  const view = new DataView(input.buffer, input.byteOffset, input.byteLength);
  const decoder = new TextDecoder();
  if (decoder.decode(input.subarray(0, 5)) !== 'IWIX\x01') throw Error('Invalid IWIX version');
  let offset = 5;
  while (offset < input.length) {
    const h = view.getUint32(offset, true),
      b = view.getUint32(offset + 4, true);
    offset += 8;
    const header = JSON.parse(decoder.decode(input.subarray(offset, offset + h)));
    offset += h;
    const end = offset + b;
    if (end > input.length) throw Error('Truncated index');
    const nextInt = () => {
      let value = 0,
        factor = 1;
      while (offset < end) {
        const byte = input[offset++];
        value += factor * (byte & 127);
        if (byte < 128) return value;
        factor *= 128;
      }
      throw Error('Truncated posting');
    };
    const postings = new Map();
    for (const term of header.dictionary) {
      let row = 0;
      const list = new Uint32Array(nextInt());
      for (let i = 0; i < list.length; i++) {
        const delta = nextInt();
        row += Math.floor(delta / 8);
        if (row >= header.rows.length) throw Error('Invalid posting row');
        list[i] = row * 8 + (delta & 7);
      }
      postings.set(term, list);
    }
    if (offset !== end) throw Error('Mismatched block length');
    yield { ...header, postings };
  }
}
