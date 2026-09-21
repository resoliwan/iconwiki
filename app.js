import { filterCatalogItems, loadCatalog } from './catalog.js?v=progressive-results-1';
import { buildSmartResults, ChromeSmartSearch, isDesktopChrome } from './smart-search.js?v=progressive-results-1';

const $ = selector => document.querySelector(selector);
const RESULT_BATCH_SIZE = 100;
const SMART_PREFERENCE_KEY = 'iconwiki-ai-expansion-enabled';
const FILTER_PIN_PREFERENCE_KEY = 'iconwiki-filter-panel-pinned';
const MONOCHROME_COLLECTIONS = new Set(['material-design-icons', 'tabler', 'lucide', 'phosphor', 'heroicons', 'font-awesome-free', 'bootstrap-icons', 'iconoir', 'ionicons', 'fluent-emoji-high-contrast']);
const LICENSE_FILTERS = [
  { id: 'permissive', name: 'Permissive' },
  { id: 'attribution', name: 'Attribution / ShareAlike' },
  { id: 'restricted', name: 'Restricted / Brand' },
];
const state = {
  items: [], collections: [], byId: new Map(), query: '', withinFilter: '', filterCollections: new Set(),
  filterLicenseClasses: new Set(), resultType: 'all', displayMode: 'images', skinTones: false,
  selected: null, smartEnabled: false, smartExpansion: null, filtersPinned: false,
  smartStatus: { message: '', busy: false, phase: '', percent: null },
  smartModelStatus: { message: '', busy: false, phase: '', percent: null },
};
const chromeSmartSearch = new ChromeSmartSearch();
const smartSupported = isDesktopChrome() && chromeSmartSearch.supported;
const SMART_UNSUPPORTED_MESSAGE = 'AI expansion is supported only in desktop Google Chrome. This browser is not supported.';
let smartTimer;
let smartRequest = 0;
let smartPrepareAttempt = null;
let smartRetryArmed = false;
let toastTimer;
let currentResults = [];
let currentSearch = null;
let renderedResultCount = 0;
function smartErrorMessage(error, fallback) {
  const message = error?.message || fallback;
  return /not eligible|not supported|unavailable in this browser/i.test(message)
    ? SMART_UNSUPPORTED_MESSAGE
    : message;
}
function toast(message) {
  $('#toast').textContent = message;
  $('#toast').hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 4200);
}
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function button(text, className, action) {
  const node = el('button', className, text);
  node.type = 'button';
  node.addEventListener('click', action);
  return node;
}
function encodedSelection(selected, options) {
  if (selected.size === options.length) return '';
  return selected.size ? [...selected].join(',') : 'none';
}
function readSelection(value, options) {
  const valid = new Set(options.map(option => option.id));
  if (!value) return new Set(valid);
  if (value === 'none') return new Set();
  return new Set(value.split(',').filter(id => valid.has(id)));
}
function readSmartPreference() {
  try { return localStorage.getItem(SMART_PREFERENCE_KEY) === 'true'; }
  catch { return false; }
}
function saveSmartPreference() {
  try { localStorage.setItem(SMART_PREFERENCE_KEY, String(state.smartEnabled)); }
  catch { /* The toggle still works for the current page if storage is unavailable. */ }
}
function renderSmartToggle() {
  const toggle = $('#smart-search');
  toggle.checked = state.smartEnabled;
  toggle.closest('.inline-toggle').classList.toggle('unsupported', !smartSupported);
  if (!smartSupported) toggle.closest('.inline-toggle').title = SMART_UNSUPPORTED_MESSAGE;
}
function readFilterPinPreference() {
  try { return localStorage.getItem(FILTER_PIN_PREFERENCE_KEY) === 'true'; }
  catch { return false; }
}
function saveFilterPinPreference() {
  try { localStorage.setItem(FILTER_PIN_PREFERENCE_KEY, String(state.filtersPinned)); }
  catch { /* The toggle still works for the current page if storage is unavailable. */ }
}
function renderFilterPinToggle() {
  const toggle = $('#filter-pin');
  toggle.checked = state.filtersPinned;
  $('#filters-panel').classList.toggle('pinned', state.filtersPinned);
  $('#close-filters').disabled = state.filtersPinned;
}
function renderMultiFilter({ root, summary, container, options, selected, allLabel, singularLabel, pluralLabel, update }) {
  const selectedNames = options.filter(option => selected.has(option.id)).map(option => option.name);
  summary.textContent = selected.size === options.length ? allLabel
    : selected.size === 0 ? `No ${pluralLabel}`
      : selected.size === 1 ? selectedNames[0]
        : `${selected.size} ${pluralLabel}`;
  summary.title = selected.size > 1 && selected.size < options.length ? selectedNames.join(', ') : '';
  const fragment = document.createDocumentFragment();
  const actions = el('div', 'multi-filter-actions');
  const selectAll = button('Select all', '', () => update(new Set(options.map(option => option.id))));
  const clearAll = button('Clear all', '', () => update(new Set()));
  selectAll.setAttribute('aria-label', `Select all ${pluralLabel}`);
  clearAll.setAttribute('aria-label', `Clear all ${pluralLabel}`);
  actions.append(selectAll, clearAll);
  fragment.append(actions);
  for (const option of options) {
    const label = el('label', 'multi-filter-option');
    const check = el('input');
    check.type = 'checkbox';
    check.checked = selected.has(option.id);
    check.setAttribute('aria-label', option.name);
    check.addEventListener('change', () => {
      const next = new Set(selected);
      if (check.checked) next.add(option.id);
      else next.delete(option.id);
      update(next);
    });
    label.append(check, document.createTextNode(option.name));
    fragment.append(label);
  }
  container.replaceChildren(fragment);
  root.setAttribute('aria-label', `${singularLabel} filter: ${summary.textContent}`);
}
function renderFilterControls() {
  renderMultiFilter({
    root: $('#collection-filter'), summary: $('#collection-filter-summary'), container: $('#collection-options'),
    options: state.collections.map(collection => ({ id: collection.id, name: collection.name })),
    selected: state.filterCollections, allLabel: 'All libraries', singularLabel: 'Library', pluralLabel: 'libraries',
    update: next => { state.filterCollections = next; renderFilterControls(); renderGrid(); },
  });
  renderMultiFilter({
    root: $('#license-filter'), summary: $('#license-filter-summary'), container: $('#license-options'),
    options: LICENSE_FILTERS, selected: state.filterLicenseClasses,
    allLabel: 'All licenses', singularLabel: 'License', pluralLabel: 'licenses',
    update: next => { state.filterLicenseClasses = next; renderFilterControls(); renderGrid(); },
  });
}
function art(item) {
  const node = el('span', 'emoji');
  node.setAttribute('aria-hidden', 'true');
  if (item.kind === 'image') {
    if (MONOCHROME_COLLECTIONS.has(item.collection) || item.collection === 'fluent-system-icons' && item.variant !== 'color') node.classList.add('monochrome');
    const img = el('img');
    img.src = item.src;
    img.alt = '';
    img.loading = 'lazy';
    node.append(img);
  } else if (item.kind === 'font') {
    node.classList.add('material-symbol');
    node.textContent = item.glyph;
  } else {
    const monochrome = item.collection === 'noto-emoji-monochrome';
    if (monochrome) node.classList.add('noto-emoji-monochrome');
    node.textContent = monochrome ? item.emoji.replaceAll('\uFE0F', '\uFE0E') : item.emoji;
  }
  return node;
}
function updateURL() {
  const url = new URL(location.href);
  const collectionOptions = state.collections.map(collection => ({ id: collection.id }));
  for (const [key, value] of Object.entries({ q: state.query, filter: state.withinFilter, collection: encodedSelection(state.filterCollections, collectionOptions), license: encodedSelection(state.filterLicenseClasses, LICENSE_FILTERS), match: state.resultType === 'all' ? '' : state.resultType, display: state.displayMode === 'labels' ? 'labels' : '', smart: state.smartEnabled ? '1' : '', tones: state.skinTones ? '1' : '', id: state.selected || '' })) {
    if (value) url.searchParams.set(key, value);
    else url.searchParams.delete(key);
  }
  url.searchParams.delete('language');
  url.searchParams.delete('view');
  history.replaceState(null, '', url);
}
function readURL() {
  const params = new URLSearchParams(location.search);
  state.query = params.get('q') || '';
  state.withinFilter = params.get('filter') || '';
  state.filterCollections = readSelection(params.get('collection'), state.collections);
  state.filterLicenseClasses = readSelection(params.get('license'), LICENSE_FILTERS);
  state.resultType = ['exact', 'keyword', 'prefix', 'similar'].includes(params.get('match')) ? params.get('match') : 'all';
  state.displayMode = params.get('display') === 'labels' ? 'labels' : 'images';
  const requestedSmartEnabled = params.has('smart') ? params.get('smart') === '1' : readSmartPreference();
  state.smartEnabled = smartSupported && requestedSmartEnabled;
  if (!smartSupported || params.has('smart')) saveSmartPreference();
  state.filtersPinned = readFilterPinPreference();
  state.skinTones = params.get('tones') === '1';
  state.selected = state.byId.has(params.get('id')) ? params.get('id') : null;
  $('#search').value = state.query;
  $('#within-filter').value = state.withinFilter;
  $('#skin-tones').checked = state.skinTones;
  $('#result-filter').value = state.resultType;
  $('#display-mode').value = state.displayMode;
  renderSmartToggle();
  renderFilterPinToggle();
  renderFilterControls();
}
function renderExpansionTerms() {
  const panel = $('#expansion-panel');
  const expansion = state.smartExpansion?.sourceQuery === state.query.trim() ? state.smartExpansion : null;
  const terms = expansion?.terms || [];
  const status = state.smartModelStatus.message ? state.smartModelStatus : state.smartStatus;
  const showTerms = state.smartEnabled && terms.length > 0;
  panel.hidden = !status.message && !showTerms;
  const progress = $('#ai-progress');
  progress.hidden = !status.message;
  $('#ai-progress-label').textContent = status.message;
  const progressBar = $('#ai-progress-bar');
  const showPercent = status.phase === 'download' && Number.isFinite(status.percent);
  progressBar.hidden = !showPercent;
  progressBar.value = showPercent ? status.percent : 0;
  const fragment = document.createDocumentFragment();
  for (const term of terms) {
    fragment.append(el('span', 'expansion-term', term));
  }
  $('#expansion-terms').replaceChildren(fragment);
}
function resultCard(item, search) {
  const card = button('', 'emoji-card', () => select(item.id));
  card.dataset.id = item.id;
  card.setAttribute('aria-label', item.name);
  card.setAttribute('aria-pressed', String(state.selected === item.id));
  const matchType = search.matchTypeById.get(item.id);
  card.title = `${item.name}\n${item.id}${matchType && matchType !== 'browse' ? `\n${matchType} match` : ''}`;
  card.append(art(item));
  if (state.displayMode === 'labels') {
    const caption = el('span', 'card-caption');
    caption.append(el('span', 'card-name', item.name));
    if (matchType && matchType !== 'browse') {
      const mark = el('span', `match-mark ${matchType}`, matchType.toUpperCase());
      mark.title = matchType === 'similar'
        ? `AI expansion term: ${search.relatedTermById.get(item.id)}`
        : `${matchType} match`;
      caption.append(mark);
    }
    card.append(caption);
  }
  return card;
}
function renderNextResultBatch() {
  if (!currentSearch || renderedResultCount >= currentResults.length) {
    $('#load-more').hidden = true;
    return;
  }
  const end = Math.min(renderedResultCount + RESULT_BATCH_SIZE, currentResults.length);
  const fragment = document.createDocumentFragment();
  for (const item of currentResults.slice(renderedResultCount, end)) {
    fragment.append(resultCard(item, currentSearch));
  }
  $('#grid').append(fragment);
  renderedResultCount = end;
  const remaining = currentResults.length - renderedResultCount;
  const loadMore = $('#load-more');
  loadMore.hidden = remaining === 0;
  loadMore.textContent = remaining
    ? `Load ${Math.min(RESULT_BATCH_SIZE, remaining).toLocaleString()} more`
    : '';
  $('#result-count').textContent = remaining
    ? `${currentResults.length.toLocaleString()} results · showing ${renderedResultCount.toLocaleString()}`
    : `${currentResults.length.toLocaleString()} results`;
}
function renderGrid() {
  const expansion = state.smartExpansion?.sourceQuery === state.query.trim() ? state.smartExpansion : null;
  const activeExpansion = state.smartEnabled ? expansion : null;
  currentSearch = buildSmartResults(state.items, {
    ...state,
    collections: [...state.filterCollections],
    licenseClasses: [...state.filterLicenseClasses],
  }, activeExpansion, state.resultType);
  currentResults = filterCatalogItems(currentSearch.results, state.withinFilter);
  renderedResultCount = 0;
  $('#grid').replaceChildren();
  $('#grid').classList.toggle('image-only', state.displayMode === 'images');
  $('#grid').setAttribute('aria-busy', 'false');
  $('#empty').hidden = currentResults.length > 0;
  $('#result-count').textContent = `${currentResults.length.toLocaleString()} results`;
  $('#load-more').hidden = true;
  renderNextResultBatch();
  renderExpansionTerms();
  updateURL();
}
function panelHeading(label) {
  const top = el('div', 'detail-top');
  const close = button('×', 'close-button', closePanel);
  close.setAttribute('aria-label', 'Close details');
  top.append(el('span', '', label), close);
  return top;
}
function closePanel() {
  const oldId = state.selected;
  state.selected = null;
  renderPanel();
  const old = [...$('#grid').children].find(node => node.dataset.id === oldId);
  for (const card of $('#grid').children) card.setAttribute('aria-pressed', 'false');
  updateURL();
  (old || $('#search')).focus({ preventScroll: true });
}
function select(id) {
  state.selected = id;
  renderPanel();
  for (const card of $('#grid').children) card.setAttribute('aria-pressed', String(card.dataset.id === id));
  updateURL();
  $('#detail .close-button')?.focus({ preventScroll: true });
}
async function copy(value, message) {
  try { await navigator.clipboard.writeText(value); toast(message); }
  catch { toast('Clipboard access is unavailable. Select and copy the text from the details panel.'); }
}
function renderDetail(item) {
  const panel = $('#detail');
  const collection = state.collections.find(c => c.id === item.collection);
  panel.append(panelHeading('IMAGE DETAILS'));
  const preview = el('div', 'preview');
  preview.append(art(item));
  panel.append(preview, el('h2', '', item.name));
  const actions = el('div', 'detail-actions');
  if (item.kind === 'emoji') actions.append(button('Copy emoji', 'button', () => copy(item.emoji, 'Emoji copied.')));
  actions.append(button('Copy ID', 'button subtle', () => copy(item.id, 'Asset ID copied.')));
  panel.append(actions);
  const metadata = el('dl', 'metadata');
  function row(label, value) {
    const node = el('div');
    const dd = el('dd');
    if (typeof value === 'string') dd.textContent = value;
    else dd.append(value);
    node.append(el('dt', '', label), dd);
    metadata.append(node);
  }
  row('Library', collection?.name || item.collection);
  row('Category', item.group || '—');
  row('ID', el('code', '', item.id));
  if (item.codepoints) row('Code', el('code', '', item.codepoints.map(c => `U+${c}`).join(' ')));
  if (item.version) row('Introduced', `Emoji ${item.version}`);
  if (collection?.sourceUrl) {
    const link = el('a', '', 'Official source ↗');
    link.href = collection.sourceUrl;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    row('Source', link);
  }
  if (collection?.licenseUrl) {
    const link = el('a', '', collection.license);
    link.href = collection.licenseUrl;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    row('Data license', link);
  }
  if (item.licenseClass || collection?.licenseClass) row('License class', {
    permissive: 'Permissive',
    attribution: 'Attribution / ShareAlike',
    restricted: 'Restricted / Brand',
  }[item.licenseClass || collection.licenseClass] || item.licenseClass || collection.licenseClass);
  panel.append(metadata, el('h3', 'section-label', 'Keywords'));
  const tags = el('div', 'tags');
  for (const keyword of item.keywords || []) tags.append(button(keyword, 'tag', () => {
    state.query = keyword;
    $('#search').value = keyword;
    renderGrid();
  }));
  panel.append(tags);
  if (collection?.note) panel.append(el('p', 'hint', collection.note));
}
function renderPanel() {
  const panel = $('#detail');
  const visible = Boolean(state.selected);
  panel.hidden = !visible;
  $('#workspace').classList.toggle('with-detail', visible);
  panel.replaceChildren();
  if (!visible) return;
  renderDetail(state.byId.get(state.selected));
  panel.scrollTop = 0;
}

function setSmartStatus(message = '', busy = false, details = {}) {
  state.smartStatus = { message, busy, phase: details.phase || '', percent: details.percent ?? null };
  const toggle = $('#smart-search');
  const anyBusy = busy || state.smartModelStatus.busy;
  toggle.closest('.inline-toggle').classList.toggle('busy', anyBusy);
  toggle.setAttribute('aria-busy', String(anyBusy));
  if (smartSupported) toggle.closest('.inline-toggle').title = message || 'Expand related terms automatically, or press Enter to run again.';
  renderExpansionTerms();
}

function setSmartModelStatus(message = '', busy = false, details = {}) {
  state.smartModelStatus = { message, busy, phase: details.phase || '', percent: details.percent ?? null };
  const toggle = $('#smart-search');
  const anyBusy = busy || state.smartStatus.busy;
  toggle.closest('.inline-toggle').classList.toggle('busy', anyBusy);
  toggle.setAttribute('aria-busy', String(anyBusy));
  renderExpansionTerms();
}

function armChromeAIRetry() {
  if (smartRetryArmed) return;
  smartRetryArmed = true;
  const resume = () => {
    document.removeEventListener('pointerdown', resume, true);
    document.removeEventListener('keydown', resume, true);
    smartRetryArmed = false;
    void prepareChromeAI({ allowRetry: false });
  };
  document.addEventListener('pointerdown', resume, { once: true, capture: true });
  document.addEventListener('keydown', resume, { once: true, capture: true });
}

async function prepareChromeAI({ allowRetry = true } = {}) {
  if (!smartSupported || chromeSmartSearch.languageModel) return chromeSmartSearch.languageModel;
  if (smartPrepareAttempt) return smartPrepareAttempt;
  setSmartModelStatus('Preparing Chrome AI…', true);
  smartPrepareAttempt = chromeSmartSearch.prepare((message, details) => {
    setSmartModelStatus(message, true, details);
  });
  try {
    const model = await smartPrepareAttempt;
    setSmartModelStatus();
    return model;
  } catch (error) {
    smartPrepareAttempt = null;
    if (allowRetry && !navigator.userActivation?.hasBeenActive) {
      setSmartModelStatus('Click or type to start the Chrome AI download.');
      armChromeAIRetry();
      return null;
    }
    const message = smartErrorMessage(error, 'Chrome AI could not be downloaded.');
    setSmartModelStatus(message);
    return null;
  }
}

function setSmartExpansion(expansion) {
  state.smartExpansion = expansion;
}

async function runSmartSearch({ refresh = false } = {}) {
  clearTimeout(smartTimer);
  const query = state.query.trim();
  const request = ++smartRequest;
  if (!state.smartEnabled || !query) {
    setSmartExpansion(null);
    setSmartStatus();
    renderGrid();
    return;
  }
  setSmartStatus('Starting smart search…', true);
  try {
    const expansion = await chromeSmartSearch.expand(query, 'auto', (message, details) => {
      if (request === smartRequest) setSmartStatus(message, true, details);
    }, partial => {
      if (request !== smartRequest || query !== state.query.trim()) return;
      setSmartExpansion(partial);
      setSmartStatus('Finding related icons…', true);
      renderGrid();
    }, { refresh });
    if (request !== smartRequest || query !== state.query.trim()) return;
    setSmartExpansion(expansion);
    setSmartStatus();
    renderGrid();
    if (refresh && !expansion?.terms.length) toast(expansion?.local
      ? 'Chrome AI is unavailable and no local expansion was found. Showing direct matches.'
      : 'No additional related terms found.');
  } catch (error) {
    if (request !== smartRequest) return;
    setSmartExpansion(null);
    const message = smartErrorMessage(error, 'Chrome AI could not expand this search.');
    setSmartStatus(message);
    toast(message);
    renderGrid();
  }
}

function scheduleSmartSearch() {
  clearTimeout(smartTimer);
  if (!state.smartEnabled || !state.query.trim()) return;
  smartTimer = setTimeout(runSmartSearch, 450);
}

$('#search').addEventListener('input', event => {
  ++smartRequest;
  state.query = event.target.value;
  setSmartExpansion(null);
  setSmartStatus(state.smartEnabled && state.query.trim() ? 'Waiting to expand…' : '');
  renderGrid();
  scheduleSmartSearch();
});
$('#search').addEventListener('keydown', event => {
  if (event.key === 'Tab') {
    event.preventDefault();
    $('#within-filter').focus();
    $('#within-filter').select();
    return;
  }
  if (event.key !== 'Enter' || event.isComposing || event.repeat) return;
  event.preventDefault();
  state.query = event.currentTarget.value;
  if (state.smartEnabled) runSmartSearch({ refresh: true });
  else renderGrid();
});
$('#within-filter').addEventListener('input', event => {
  state.withinFilter = event.target.value;
  renderGrid();
});
$('#within-filter').addEventListener('keydown', event => {
  if (event.key !== 'Tab') return;
  event.preventDefault();
  $('#search').focus();
  $('#search').select();
});
$('#skin-tones').addEventListener('change', event => { state.skinTones = event.target.checked; renderGrid(); });
$('#result-filter').addEventListener('change', event => { state.resultType = event.target.value; renderGrid(); });
$('#display-mode').addEventListener('change', event => { state.displayMode = event.target.value; renderGrid(); });
$('#smart-search').addEventListener('change', event => {
  if (!smartSupported) {
    event.target.checked = false;
    state.smartEnabled = false;
    saveSmartPreference();
    renderSmartToggle();
    renderExpansionTerms();
    updateURL();
    toast(SMART_UNSUPPORTED_MESSAGE);
    return;
  }
  state.smartEnabled = event.target.checked;
  saveSmartPreference();
  renderSmartToggle();
  if (!state.smartEnabled) {
    ++smartRequest;
    setSmartExpansion(null);
    setSmartStatus();
    renderGrid();
  } else {
    void prepareChromeAI({ allowRetry: false });
    runSmartSearch();
  }
});
function reset() {
  ++smartRequest;
  state.query = ''; state.withinFilter = ''; state.filterCollections = new Set(state.collections.map(collection => collection.id)); state.filterLicenseClasses = new Set(LICENSE_FILTERS.map(option => option.id)); state.resultType = 'all'; setSmartExpansion(null);
  $('#search').value = ''; $('#within-filter').value = ''; $('#result-filter').value = 'all'; renderFilterControls();
  setSmartStatus(); renderGrid();
}
const multiFilters = [...document.querySelectorAll('.multi-filter')];
for (const filter of multiFilters) {
  filter.addEventListener('toggle', () => {
    if (!filter.open) return;
    for (const other of multiFilters) if (other !== filter) other.open = false;
  });
}
document.addEventListener('pointerdown', event => {
  for (const filter of multiFilters) {
    if (filter.open && !filter.contains(event.target)) filter.open = false;
  }
});
$('#reset').addEventListener('click', reset);
$('#reset-filters').addEventListener('click', reset);
$('#load-more').addEventListener('click', renderNextResultBatch);
if ('IntersectionObserver' in window) {
  new IntersectionObserver(entries => {
    if (!$('#load-more').hidden && entries.some(entry => entry.isIntersecting)) renderNextResultBatch();
  }, { rootMargin: '400px 0px' }).observe($('#load-more'));
}
function setFiltersOpen(open, { focus = true } = {}) {
  if (!open && state.filtersPinned) return;
  $('#filters-panel').hidden = !open;
  $('#workspace').classList.toggle('filters-closed', !open);
  $('#browse-button').classList.toggle('active', open);
  $('#browse-button').setAttribute('aria-expanded', String(open));
  if (!open) {
    for (const filter of multiFilters) filter.open = false;
    if (focus) $('#browse-button').focus({ preventScroll: true });
  } else if (focus) $('#filter-pin').focus({ preventScroll: true });
}
$('#close-filters').addEventListener('click', () => setFiltersOpen(false));
$('#filter-pin').addEventListener('change', event => {
  state.filtersPinned = event.target.checked;
  saveFilterPinPreference();
  renderFilterPinToggle();
  if (state.filtersPinned) setFiltersOpen(true, { focus: false });
});
$('#browse-button').addEventListener('click', () => {
  const panelOpen = !$('#filters-panel').hidden;
  if (panelOpen && state.filtersPinned) {
    state.filtersPinned = false;
    saveFilterPinPreference();
    renderFilterPinToggle();
  }
  setFiltersOpen(!panelOpen);
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !$('#detail').hidden) closePanel();
  if (event.key === '/' && !/INPUT|TEXTAREA|SELECT/.test(event.target.tagName) && !event.metaKey && !event.ctrlKey) {
    event.preventDefault(); $('#search').focus();
  }
});
window.addEventListener('popstate', () => { readURL(); renderPanel(); renderGrid(); });
if ('ResizeObserver' in window) {
  new ResizeObserver(entries => {
    const height = entries[0]?.borderBoxSize?.[0]?.blockSize || entries[0]?.contentRect.height;
    if (height) document.documentElement.style.setProperty('--topbar-height', `${Math.ceil(height)}px`);
  }).observe($('.topbar'));
}

if (smartSupported) void prepareChromeAI();

try {
  const { collections, items } = await loadCatalog();
  state.collections = collections; state.items = items;
  state.byId = new Map(items.map(item => [item.id, item]));
  readURL(); renderPanel(); renderGrid();
  if (state.smartEnabled && state.query.trim()) runSmartSearch();
} catch (error) {
  $('#grid').setAttribute('aria-busy', 'false');
  $('#result-count').textContent = 'Data failed to load';
  const notice = el('p', 'hint', `${error.message} · Make sure the app is opened through its static server.`);
  $('#grid').replaceChildren(notice);
}
