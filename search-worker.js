import { filterCatalogItems } from './catalog.js?v=progressive-results-1';
import { buildSmartResults } from './smart-search.js?v=silent-ai-1';
import { loadProgressively, PRIMARY_COLLECTION } from './progressive-catalog.js';

let collections = [], items = [], byId = new Map(), revision = 0;
const loaded = new Set(), failures = new Map();
let releasePrimary;
const primaryPainted = new Promise(resolve => { releasePrimary = resolve; });
let loading = false, cached;
async function read(url) {
  const response = await fetch(url, { signal: AbortSignal.timeout(30000) });
  if (!response.ok) throw new Error(`Could not load ${url} (${response.status})`);
  return response.json();
}
function progress() {
  postMessage({ type: 'progress', loaded: [...loaded], failed: [...failures.keys()], total: collections.length, loading });
}
async function load(list) {
  loading = true;
  progress();
  await loadProgressively(list, {
    read,
    accept(collection, chunk) {
      // Stable order is independent of the network completion order.
      const rank = collection.id === PRIMARY_COLLECTION ? 0 : collections.indexOf(collection) + 1;
      for (const item of chunk) {
        item._order += rank * 1_000_000;
        byId.set(item.id, item);
      }
      items.push(...chunk);
      loaded.add(collection.id);
      failures.delete(collection.id);
      revision++;
      progress();
    },
    failed(collection) { failures.set(collection.id, collection); progress(); },
    primaryReady: () => primaryPainted,
  });
  loading = false;
  progress();
}
function publicItem(item) {
  return Object.fromEntries(Object.entries(item).filter(([key]) => !key.startsWith('_')));
}
self.onmessage = async ({ data }) => {
  try {
    if (data.type === 'init') {
      collections = await read('./data/collections.json');
      postMessage({ type: 'manifest', collections });
      await load(collections);
    } else if (data.type === 'continue') {
      releasePrimary();
    } else if (data.type === 'retry' && !loading) {
      await load([...failures.values()]);
    } else if (data.type === 'search') {
      const started = performance.now();
      const key = JSON.stringify([revision, data.options, data.expansion, data.resultType, data.withinFilter]);
      if (cached?.key !== key) {
        const search = buildSmartResults(items, data.options, data.expansion, data.resultType);
        cached = { key, search, results: filterCatalogItems(search.results, data.withinFilter) };
      }
      const visible = cached.results.slice(0, data.limit);
      postMessage({ type: 'results', request: data.request, total: cached.results.length,
        items: visible.map(publicItem),
        matches: visible.map(item => [item.id, cached.search.matchTypeById.get(item.id)]),
        related: visible.map(item => [item.id, cached.search.relatedTermById.get(item.id)]),
        selected: byId.has(data.selected) ? publicItem(byId.get(data.selected)) : null,
        duration: performance.now() - started,
      });
    }
  } catch (error) {
    postMessage({ type: 'error', request: data.request, message: error.message });
  }
};
