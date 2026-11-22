import { prepareCatalog, filterCatalogItems } from './catalog.js';
import { buildSmartResults } from './smart-search.js';
import { createPackedSearch } from './packed-search.js';
import { loadPackedIndex, packedItem, hydratePackedItem } from './packed-index.js?v=git-art-1';

let manifest, searchIndex, preview = [], loading = false, failed = false, refreshManifest = false;
const read = (url, options = {}) => fetch(url, { ...options, signal: AbortSignal.timeout(60000) });

function progress() {
  postMessage({ type: 'progress', loaded: searchIndex ? manifest.collections.map(c => c.id) : [],
    failed: failed ? ['search index'] : [], total: manifest?.collectionCount || 0, loading,
    primaryReady: preview.length > 0 || !!searchIndex });
}

async function load() {
  if (loading || searchIndex) return;
  loading = true;
  failed = false;
  progress();
  try {
    if (!manifest || refreshManifest) {
      const response = await read('./data/search/manifest.json', refreshManifest ? { cache: 'reload' } : {});
      if (!response.ok) throw Error('Could not load the collection list');
      manifest = await response.json();
      refreshManifest = false;
      postMessage({ type: 'manifest', collections: manifest.collections, rowCount: manifest.rowCount });
      const material = manifest.collections.find(c => c.previewCatalog);
      if (material && !preview.length) {
        try {
          const response = await read(material.previewCatalog);
          if (response.ok) preview = prepareCatalog((await response.json()).map(item => ({ ...item, licenseClass: material.licenseClass })));
        } catch { /* The complete index also contains these icons. */ }
        if (preview.length) return;
      }
    }
    const { blocks } = await loadPackedIndex(manifest);
    searchIndex = createPackedSearch(blocks);
    preview = [];
  } catch (error) {
    if (error.status === 404 || error.status === 410) refreshManifest = true;
    failed = true;
  } finally {
    loading = false;
    progress();
  }
}

function publicItem(item) {
  return Object.fromEntries(Object.entries(item).filter(([key]) => !key.startsWith('_')));
}

function search(data) {
  const started = performance.now();
  if (searchIndex) {
    const {total, visible, selected} = searchIndex.search(data);
    const items = visible.map(({ block, index }) => packedItem(block, index));
    postMessage({ type: 'results', request: data.request, total, items,
      matches: items.map((item, i) => [item.id, visible[i].matchType]),
      related: items.map((item, i) => [item.id, visible[i].relatedTerm]),
      selected: selected && packedItem(selected.block, selected.index), duration: performance.now() - started });
    return;
  }
  const result = buildSmartResults(preview, data.options, data.expansion, data.resultType);
  const filtered = filterCatalogItems(result.results, data.withinFilter);
  const items = filtered.slice(0, data.limit).map(publicItem);
  const selected = preview.find(item => item.id === data.selected);
  postMessage({ type: 'results', request: data.request, total: filtered.length, items,
    matches: items.map(item => [item.id, result.matchTypeById.get(item.id)]),
    related: items.map(item => [item.id, result.relatedTermById.get(item.id)]),
    selected: selected && publicItem(selected), duration: performance.now() - started });
}

self.onmessage = async ({ data }) => {
  try {
    if (['init', 'retry', 'continue'].includes(data.type)) await load();
    if (data.type === 'search') search(data);
    if (data.type === 'detail') {
      const ref = searchIndex?.resolveId(data.id);
      if (ref) {
        const item = await hydratePackedItem(ref.block, ref.index, read);
        postMessage({ type: 'detail', item });
      }
    }
  } catch (error) {
    postMessage({ type: 'error', action: data.type, request: data.request, message: error.message });
  }
};
