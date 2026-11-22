import { prepareCatalog } from './catalog.js?v=progressive-results-1';

export const PRIMARY_COLLECTION = 'material-symbols-outlined';

// The primary callback is an explicit gate: the UI acknowledges its first paint
// before any other catalog request starts. Failed catalogs can be retried alone.
export async function loadProgressively(collections, { read, accept, failed, primaryReady = async () => {}, usePreview = true, previewLoaded = false, concurrency = 3 }) {
  const primary = collections.find(c => c.id === PRIMARY_COLLECTION);
  const load = async (collection, url, isPreview = false) => {
    try {
      const raw = await read(url);
      const items = prepareCatalog(raw.map(item => ({ ...item,
        licenseClass: item.licenseClass || collection.licenseClass || 'restricted',
      })));
      await accept(collection, items, isPreview);
      return true;
    } catch (error) { failed(collection, error); return false; }
  };
  const queue = collections.filter(c => c !== primary).map(collection => [collection, collection.catalog]);
  if (primary) {
    const hasPreview = usePreview && Boolean(primary.previewCatalog && primary.remainingCatalog);
    const ready = previewLoaded || await load(primary, hasPreview ? primary.previewCatalog : primary.catalog, hasPreview);
    if (ready && !previewLoaded) await primaryReady();
    if (ready && hasPreview) queue.unshift([primary, primary.remainingCatalog]);
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, queue.length) }, async () => {
    while (queue.length) await load(...queue.shift());
  }));
}
