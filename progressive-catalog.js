import { prepareCatalog } from './catalog.js?v=progressive-results-1';

export const PRIMARY_COLLECTION = 'material-symbols-outlined';

// The primary callback is an explicit gate: the UI acknowledges its first paint
// before any other catalog request starts. Failed catalogs can be retried alone.
export async function loadProgressively(collections, { read, accept, failed, primaryReady = async () => {}, concurrency = 3 }) {
  const primary = collections.find(c => c.id === PRIMARY_COLLECTION);
  const load = async collection => {
    try {
      const raw = await read(collection.catalog);
      const items = prepareCatalog(raw.map(item => ({ ...item,
        licenseClass: item.licenseClass || collection.licenseClass || 'restricted',
      })));
      await accept(collection, items);
      return true;
    } catch (error) { failed(collection, error); return false; }
  };
  if (primary && await load(primary)) await primaryReady();
  const queue = collections.filter(c => c !== primary);
  await Promise.all(Array.from({ length: Math.min(concurrency, queue.length) }, async () => {
    while (queue.length) await load(queue.shift());
  }));
}
