import { normalize } from './catalog.js';
import { isAndQuery } from './smart-search.js';
import { NAME_TOKEN, KEYWORD_TOKEN, KEYWORD_PHRASE } from './scripts/search_index_codec.mjs';

// The numeric ranks preserve searchCatalogMatches' score ordering and make a
// stable counting sort possible. Zero denotes a row outside the result set.
const types = ['', 'browse', 'prefix', 'prefix', 'keyword', 'keyword', 'keyword', 'exact', 'exact'];
const NAME_EXACT = 1, ANY_EXACT = 2, NAME_PREFIX = 4, ANY_PREFIX = 8;
const boundaries = /[\s_,;:()\-]+/;
const onlyBoundaries = /^[\s_,;:()\-]+$/;
const slugOf = row => typeof row === 'string' ? row : row[0];
const nameOf = row => (Array.isArray(row) && row[1]) || slugOf(row).replaceAll('-', ' ');

function lowerBound(words, value) {
  let lo = 0, hi = words.length;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (words[mid] < value) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

function ordered(ranks, limit = Infinity) {
  const counts = new Uint32Array(types.length);
  for (const rank of ranks) counts[rank]++;
  const offsets = new Uint32Array(types.length);
  let total = 0;
  for (let rank = counts.length - 1; rank > 0; rank--) {
    offsets[rank] = total;
    total += counts[rank];
  }
  const ids = new Uint32Array(Math.min(total, limit));
  for (let id = 0; id < ranks.length; id++) {
    const rank = ranks[id];
    if (rank && offsets[rank] < ids.length) ids[offsets[rank]++] = id;
  }
  return ids;
}

function tokenMatches(block, terms) {
  const usePrefix = terms.every(term => term.length >= 2);
  let common;
  for (const term of terms) {
    const exact = block.postings.get(term);
    const start = usePrefix ? lowerBound(block.dictionary, term) : block.dictionary.length;
    if (!exact && !block.dictionary[start]?.startsWith(term)) return null;
    const matches = new Uint8Array(block.rows.length);
    if (exact) {
      for (const value of exact) {
        if (value & NAME_TOKEN) matches[value >>> 3] |= NAME_EXACT | ANY_EXACT;
        else if (value & KEYWORD_TOKEN) matches[value >>> 3] |= ANY_EXACT;
      }
    }
    for (let n = start; n < block.dictionary.length; n++) {
      const word = block.dictionary[n];
      if (!word.startsWith(term)) break;
      // Multi-word phrases have no token flags and cannot match a token prefix.
      if (boundaries.test(word)) continue;
      for (const value of block.postings.get(word)) {
        if (value & NAME_TOKEN) matches[value >>> 3] |= NAME_PREFIX | ANY_PREFIX;
        else if (value & KEYWORD_TOKEN) matches[value >>> 3] |= ANY_PREFIX;
      }
    }
    if (common) {
      for (let i = 0; i < common.length; i++) common[i] &= matches[i];
    } else common = matches;
  }
  return common;
}

export function createPackedSearch(blocks) {
  // An internal row id is an offset into the concatenated blocks. Scalar ids
  // keep full-catalog browse pages compact and preserve catalog tie order.
  const starts = [], byCollection = new Map(), special = new Map();
  let size = 0;
  function register(key, id) {
    const ids = special.get(key);
    if (ids) ids.push(id);
    else special.set(key, [id]);
  }
  for (const [number, block] of blocks.entries()) {
    const collection = block.collectionId ?? block.id;
    byCollection.set(collection, number);
    starts.push(size);
    for (let i = 0; i < block.rows.length; i++) {
      const row = block.rows[i];
      if (Array.isArray(row)) {
        if (row[5]) register('emoji:' + normalize(row[5]), size + i);
        if (row[6]) register('code:' + normalize(row[6]), size + i);
      }
      // Such names have no first token to look up in the postings.
      const rawName = (Array.isArray(row) && row[1]) || slugOf(row);
      if (!/[a-z0-9]/i.test(rawName)) {
        const name = normalize(nameOf(row));
        if (onlyBoundaries.test(name)) register('name:' + name, size + i);
      }
    }
    size += block.rows.length;
  }

  function ref(id) {
    let lo = 0, hi = starts.length;
    while (lo + 1 < hi) {
      const mid = (lo + hi) >>> 1;
      if (starts[mid] <= id) lo = mid;
      else hi = mid;
    }
    return { block: blocks[lo], index: id - starts[lo] };
  }

  function idNumber(id, normalized = false) {
    if (!id) return -1;
    const split = id.indexOf(':');
    if (split < 1) return -1;
    const b = byCollection.get(id.slice(0, split));
    if (b === undefined) return -1;
    const slug = id.slice(split + 1);
    const index = blocks[b].rows.findIndex(row => normalized ? normalize(slugOf(row)) === slug : slugOf(row) === slug);
    return index < 0 ? -1 : starts[b] + index;
  }
  let lastId, lastRef;
  function resolveId(id) {
    if (!id) return null;
    if (id !== lastId) {
      const number = idNumber(id);
      lastId = id;
      lastRef = number >= 0 ? ref(number) : null;
    }
    return lastRef;
  }

  let filterKey, eligible;
  function eligibility({ group = '', collection = '', collections = null, licenseClass = '', licenseClasses = null, skinTones = true }) {
    const key = JSON.stringify([group, collection, collections, licenseClass, licenseClasses, skinTones]);
    if (filterKey === key) return eligible;
    const libraries = collections && new Set(collections);
    const licenses = licenseClasses && new Set(licenseClasses);
    const rows = new Uint8Array(size);
    for (const [b, block] of blocks.entries()) {
      const library = block.collectionId ?? block.id;
      if ((collection && collection !== library) || (libraries && !libraries.has(library))) continue;
      const groupIndex = group ? block.groups.indexOf(group) : -1;
      if (group && groupIndex < 0) continue;
      const allowed = block.classes.map(value => {
        const license = value || block.defaultClass || block.metadata?.licenseClass || 'restricted';
        return (!licenseClass || license === licenseClass) && (!licenses || licenses.has(license));
      });
      if (!allowed.includes(true)) continue;
      for (let i = 0; i < block.rows.length; i++) {
        const row = block.rows[i];
        const fields = Array.isArray(row) ? row : null;
        const flags = fields?.[4] || 0;
        if (!(flags & 2) && (skinTones || !(flags & 1)) && allowed[fields?.[3] || 0] &&
            (groupIndex < 0 || groupIndex === (fields?.[2] || 0))) rows[starts[b] + i] = 1;
      }
    }
    filterKey = key;
    eligible = rows;
    return rows;
  }

  function ranksFor(query, allowed) {
    const q = normalize(query || '');
    if (!q) return allowed.slice();
    const terms = [...new Set(q.split(/\s+/))];
    const nameTerms = [...new Set(q.split(boundaries).filter(Boolean))];
    const ranks = new Uint8Array(size);
    for (const [b, block] of blocks.entries()) {
      const base = starts[b];
      const live = allowed.subarray(base, base + block.rows.length);
      if (!live.includes(1)) continue;
      const hits = tokenMatches(block, terms);
      if (hits) {
        for (let i = 0; i < hits.length; i++) {
          const bits = hits[i];
          if (!bits || !live[i]) continue;
          ranks[base + i] = bits & NAME_EXACT ? 6 : bits & ANY_EXACT ? 4 : bits & NAME_PREFIX ? 3 : 2;
        }
      }
      for (const value of block.postings.get(q) || []) {
        const i = value >>> 3;
        if (value & KEYWORD_PHRASE && live[i] && ranks[base + i] < 5) ranks[base + i] = 5;
      }
      // Exact display names may contain separators absent from their indexed
      // tokens, e.g. "arrow-left". Only check the rarest constituent's rows.
      let rarest;
      for (const term of nameTerms) {
        const list = block.postings.get(term);
        if (!list) { rarest = null; break; }
        if (!rarest || list.length < rarest.length) rarest = list;
      }
      for (const value of rarest || []) {
        const i = value >>> 3;
        if (value & NAME_TOKEN && live[i] && normalize(nameOf(block.rows[i])) === q) ranks[base + i] = 7;
      }
    }
    function mark(key, rank) {
      for (const id of special.get(key) || []) if (allowed[id]) ranks[id] = rank;
    }
    if (!nameTerms.length) mark('name:' + q, 7);
    mark('emoji:' + q, 8);
    const codeTerms = q.split(/\s+/);
    if (codeTerms.every(t => /^(?:u\+|0x)[0-9a-f]+$/.test(t))) {
      mark('code:' + codeTerms.map(t => t.slice(2)).join(' '), 8);
    }
    const id = idNumber(q, true);
    if (id >= 0 && allowed[id]) ranks[id] = 8;
    return ranks;
  }

  let cached;
  function search({ options = {}, expansion, resultType = 'all', withinFilter, expansionTerm, limit = Infinity, selected }) {
    const key = JSON.stringify([options, expansion, resultType, withinFilter]);
    if (cached?.key !== key) {
      const allowed = eligibility(options);
      const query = isAndQuery(options.query) && (!expansion?.sourceLanguage || expansion.sourceLanguage === 'en')
        ? options.query : expansion?.englishQuery || options.query;
      const ranks = ranksFor(query, allowed);
      const related = new Map();
      const hitsByTerm = new Map();
      for (const term of expansion?.terms || []) {
        const hits = ordered(ranksFor(term, allowed), 120);
        hitsByTerm.set(term, hits);
        if (resultType === 'all' || resultType === 'similar') {
          for (const id of hits) {
            if (!ranks[id] && !related.has(id)) related.set(id, term);
          }
        }
      }
      const within = normalize(withinFilter || '') ? ranksFor(withinFilter, allowed) : null;
      if (within || resultType !== 'all') {
        for (let i = 0; i < size; i++) {
          if ((within && !within[i]) || (resultType !== 'all' && resultType !== types[ranks[i]])) ranks[i] = 0;
        }
        if (within) for (const id of related.keys()) if (!within[id]) related.delete(id);
      }
      const termCounts = [];
      for (const [term, hits] of hitsByTerm) {
        const members = hits.filter(id => ranks[id] || related.has(id));
        hitsByTerm.set(term, members);
        termCounts.push([term, members.length]);
      }
      cached = { key, ranks, ids: ordered(ranks), related, hitsByTerm, termCounts };
    }
    const { ids, ranks, related, hitsByTerm, termCounts } = cached;
    if (expansionTerm) {
      const members = hitsByTerm.get(expansionTerm) || [];
      const visible = Array.from(members.slice(0, limit), id => ranks[id]
        ? { ...ref(id), matchType: types[ranks[id]] }
        : { ...ref(id), matchType: 'similar', relatedTerm: expansionTerm });
      return { total: members.length, visible, termCounts, selected: resolveId(selected) };
    }
    const total = ids.length + related.size;
    const visible = [];
    for (let i = 0; i < Math.min(ids.length, limit); i++) {
      const id = ids[i];
      visible.push({ ...ref(id), matchType: types[ranks[id]] });
    }
    if (visible.length < limit) for (const [id, relatedTerm] of related) {
      visible.push({ ...ref(id), matchType: 'similar', relatedTerm });
      if (visible.length >= limit) break;
    }
    return { total, visible, termCounts, selected: resolveId(selected) };
  }
  return { search, resolveId };
}
