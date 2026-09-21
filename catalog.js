export const normalize = value => String(value).normalize('NFKC').toLowerCase().replace(/\ufe0f/g, '').trim();

export function prepareCatalog(items) {
  const ids = new Set();
  return items.map((item, order) => {
    if (!item.id || ids.has(item.id) || !item.name || !item.collection ||
        !['emoji', 'image', 'font'].includes(item.kind) ||
        (item.kind === 'emoji' && !item.emoji) ||
        (item.kind === 'image' && !item.src) ||
        (item.kind === 'font' && !item.glyph)) throw new Error('Check the catalog format and asset IDs.');
    ids.add(item.id);
    const names = [item.name].map(normalize);
    const keywords = (item.keywords || []).map(normalize);
    return { ...item, _order: order, _names: names, _keywords: keywords,
      _nameTokens: names.flatMap(s => s.split(/[\s_,;:()\-]+/)).filter(Boolean),
      _keywordTokens: keywords.flatMap(s => s.split(/[\s_,;:()\-]+/)).filter(Boolean),
      _codes: normalize((item.codepoints || []).join(' ')),
    };
  });
}

export async function loadCatalog() {
  async function read(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Could not load data: ${url}`);
    return response.json();
  }
  const collections = await read('./data/collections.json');
  const chunks = await Promise.all(collections.map(c => read(c.catalog)));
  const licenseClasses = new Map(collections.map(collection => [collection.id, collection.licenseClass || 'restricted']));
  const items = chunks.flat().map(item => ({
    ...item,
    licenseClass: item.licenseClass || licenseClasses.get(item.collection) || 'restricted',
  }));
  return { collections, items: prepareCatalog(items) };
}

export function searchCatalogMatches(items, { query = '', group = '', collection = '', collections = null, licenseClass = '', licenseClasses = null, skinTones = true } = {}) {
  const q = normalize(query);
  const allowedCollections = collections === null ? null : new Set(collections);
  const allowedLicenseClasses = licenseClasses === null ? null : new Set(licenseClasses);
  const terms = q.split(/\s+/).filter(Boolean);
  const codeQuery = terms.length && terms.every(term => /^(?:u\+|0x)[0-9a-f]+$/.test(term))
    ? terms.map(term => term.replace(/^(?:u\+|0x)/, '')).join(' ')
    : '';
  const scored = [];
  for (const item of items) {
    if (item.status === 'component' || group && item.group !== group || collection && item.collection !== collection ||
        allowedCollections && !allowedCollections.has(item.collection) || licenseClass && item.licenseClass !== licenseClass ||
        allowedLicenseClasses && !allowedLicenseClasses.has(item.licenseClass) || !skinTones && item.skinTone) continue;
    if (!q) { scored.push({ item, score: 0, matchType: 'browse' }); continue; }
    if (normalize(item.emoji || '') === q || normalize(item.id) === q || codeQuery && item._codes === codeQuery) {
      scored.push({ item, score: 1000, matchType: 'exact' });
    } else if (item._names.includes(q)) {
      scored.push({ item, score: 900, matchType: 'exact' });
    } else if (terms.every(term => item._nameTokens.includes(term))) {
      scored.push({ item, score: 700, matchType: 'keyword' });
    } else if (item._keywords.includes(q)) {
      scored.push({ item, score: 600, matchType: 'keyword' });
    } else if (terms.every(term => [...item._nameTokens, ...item._keywordTokens].includes(term))) {
      scored.push({ item, score: 100, matchType: 'keyword' });
    }
  }
  return scored.sort((a, b) => b.score - a.score || a.item._order - b.item._order);
}

export function searchCatalog(items, options = {}) {
  return searchCatalogMatches(items, options).map(row => row.item);
}

export function filterCatalogItems(items, query = '') {
  if (!normalize(query)) return items;
  const matchingIds = new Set(searchCatalogMatches(items, { query }).map(({ item }) => item.id));
  return items.filter(item => matchingIds.has(item.id));
}
