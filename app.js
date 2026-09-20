import { loadCatalog } from './catalog.js';
import { buildSmartResults, ChromeSmartSearch } from './smart-search.js';

const $ = selector => document.querySelector(selector);
const MAX_RENDERED_RESULTS = 600;
const SMART_PREFERENCE_KEY = 'moa-ai-expansion-enabled';
const MONOCHROME_COLLECTIONS = new Set(['material-design-icons', 'tabler', 'lucide', 'phosphor', 'heroicons', 'font-awesome-free', 'bootstrap-icons', 'iconoir', 'ionicons']);
const LICENSE_FILTERS = [
  { id: 'permissive', name: 'Permissive' },
  { id: 'attribution', name: 'Attribution / ShareAlike' },
  { id: 'restricted', name: 'Restricted / Brand' },
];
const state = { items: [], collections: [], byId: new Map(), query: '', filterCollections: new Set(), filterLicenseClasses: new Set(), resultType: 'all', displayMode: 'images', skinTones: false, selected: null, smartEnabled: false, smartExpansion: null };
const chromeSmartSearch = new ChromeSmartSearch();
let smartTimer;
let smartRequest = 0;
let toastTimer;
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
  toggle.setAttribute('aria-checked', String(state.smartEnabled));
  $('#smart-state').textContent = state.smartEnabled ? 'ON' : 'OFF';
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
  } else node.textContent = item.emoji;
  return node;
}
function updateURL() {
  const url = new URL(location.href);
  const collectionOptions = state.collections.map(collection => ({ id: collection.id }));
  for (const [key, value] of Object.entries({ q: state.query, collection: encodedSelection(state.filterCollections, collectionOptions), license: encodedSelection(state.filterLicenseClasses, LICENSE_FILTERS), match: state.resultType === 'all' ? '' : state.resultType, display: state.displayMode === 'labels' ? 'labels' : '', smart: state.smartEnabled ? '1' : '', tones: state.skinTones ? '1' : '', id: state.selected || '' })) {
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
  state.filterCollections = readSelection(params.get('collection'), state.collections);
  state.filterLicenseClasses = readSelection(params.get('license'), LICENSE_FILTERS);
  state.resultType = ['exact', 'keyword', 'similar'].includes(params.get('match')) ? params.get('match') : 'all';
  state.displayMode = params.get('display') === 'labels' ? 'labels' : 'images';
  state.smartEnabled = params.has('smart') ? params.get('smart') === '1' : readSmartPreference();
  if (params.has('smart')) saveSmartPreference();
  state.skinTones = params.get('tones') === '1';
  state.selected = state.byId.has(params.get('id')) ? params.get('id') : null;
  $('#search').value = state.query;
  $('#skin-tones').checked = state.skinTones;
  $('#result-filter').value = state.resultType;
  $('#display-mode').value = state.displayMode;
  renderSmartToggle();
  renderFilterControls();
}
function renderExpansionTerms() {
  const panel = $('#expansion-panel');
  const expansion = state.smartExpansion?.sourceQuery === state.query.trim() ? state.smartExpansion : null;
  const terms = expansion?.terms || [];
  panel.hidden = !state.smartEnabled || !terms.length;
  const fragment = document.createDocumentFragment();
  for (const term of terms) {
    fragment.append(el('span', 'expansion-term', term));
  }
  $('#expansion-terms').replaceChildren(fragment);
}
function renderGrid() {
  const expansion = state.smartExpansion?.sourceQuery === state.query.trim() ? state.smartExpansion : null;
  const activeExpansion = state.smartEnabled ? expansion : null;
  const search = buildSmartResults(state.items, {
    ...state,
    collections: [...state.filterCollections],
    licenseClasses: [...state.filterLicenseClasses],
  }, activeExpansion, state.resultType);
  const { results } = search;
  const renderedResults = results.slice(0, MAX_RENDERED_RESULTS);
  const fragment = document.createDocumentFragment();
  for (const item of renderedResults) {
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
    fragment.append(card);
  }
  $('#grid').replaceChildren(fragment);
  $('#grid').classList.toggle('image-only', state.displayMode === 'images');
  $('#grid').setAttribute('aria-busy', 'false');
  $('#empty').hidden = results.length > 0;
  $('#result-count').textContent = results.length > MAX_RENDERED_RESULTS
    ? `${results.length.toLocaleString()} results · showing first ${MAX_RENDERED_RESULTS.toLocaleString()}`
    : `${results.length.toLocaleString()} results`;
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
  renderGrid();
  const old = [...$('#grid').children].find(node => node.dataset.id === oldId);
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

function setSmartStatus(_message = '', busy = false) {
  $('#smart-search').classList.toggle('busy', busy);
}

function setSmartExpansion(expansion) {
  state.smartExpansion = expansion;
}

async function runSmartSearch() {
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
    const expansion = await chromeSmartSearch.expand(query, 'auto', message => {
      if (request === smartRequest) setSmartStatus(message, true);
    }, partial => {
      if (request !== smartRequest || query !== state.query.trim()) return;
      setSmartExpansion(partial);
      setSmartStatus('', true);
      renderGrid();
    });
    if (request !== smartRequest || query !== state.query.trim()) return;
    setSmartExpansion(expansion);
    setSmartStatus();
    renderGrid();
  } catch (error) {
    if (request !== smartRequest) return;
    setSmartExpansion(null);
    setSmartStatus(error.message || 'Chrome AI could not expand this search.');
    renderGrid();
  }
}

function scheduleSmartSearch() {
  clearTimeout(smartTimer);
  if (!state.smartEnabled || !state.query.trim()) return;
  smartTimer = setTimeout(runSmartSearch, 450);
}

$('#search').addEventListener('input', event => {
  state.query = event.target.value;
  setSmartExpansion(null);
  setSmartStatus(state.smartEnabled && state.query.trim() ? 'Waiting to expand…' : '');
  renderGrid();
  scheduleSmartSearch();
});
$('#skin-tones').addEventListener('change', event => { state.skinTones = event.target.checked; renderGrid(); });
$('#result-filter').addEventListener('change', event => { state.resultType = event.target.value; renderGrid(); });
$('#display-mode').addEventListener('change', event => { state.displayMode = event.target.value; renderGrid(); });
$('#smart-search').addEventListener('click', () => {
  state.smartEnabled = !state.smartEnabled;
  saveSmartPreference();
  renderSmartToggle();
  if (!state.smartEnabled) {
    ++smartRequest;
    setSmartExpansion(null);
    setSmartStatus();
    renderGrid();
  } else runSmartSearch();
});
function reset() {
  ++smartRequest;
  state.query = ''; state.filterCollections = new Set(state.collections.map(collection => collection.id)); state.filterLicenseClasses = new Set(LICENSE_FILTERS.map(option => option.id)); state.resultType = 'all'; setSmartExpansion(null);
  $('#search').value = ''; $('#result-filter').value = 'all'; renderFilterControls();
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
$('#browse-button').addEventListener('click', () => { closePanel(); reset(); });
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
