import { filterCatalogItems, loadCatalog } from './catalog.js?v=progressive-results-1';
import { buildSmartResults, ChromeSmartSearch, isDesktopChrome } from './smart-search.js?v=silent-ai-1';

const $ = selector => document.querySelector(selector);
const RESULT_BATCH_SIZE = 100;
const mobileLayout = matchMedia('(max-width:760px)');
const SMART_PREFERENCE_KEY = 'iconwiki-ai-expansion-enabled';
const MONOCHROME_COLLECTIONS = new Set(['material-design-icons', 'tabler', 'lucide', 'phosphor', 'heroicons', 'font-awesome-free', 'bootstrap-icons', 'iconoir', 'ionicons', 'fluent-emoji-high-contrast', 'simple-icons', 'health-icons', 'octicons', 'radix-icons', 'codicons', 'pixelarticons', 'weather-icons', 'mingcute', 'carbon-icons', 'ant-design-icons', 'maki', 'clarity-icons', 'eva-icons', 'css-gg', 'solar-icons', 'keyline-icons', 'tdesign-icons', 'flowbite-icons', 'coreui-icons-free', 'akar-icons', 'proicons']);
const LICENSE_FILTERS = [
  { id: 'permissive', name: 'Permissive' },
  { id: 'attribution', name: 'Attribution / ShareAlike' },
  { id: 'restricted', name: 'Restricted / Brand' },
];
const state = {
  items: [], collections: [], byId: new Map(), query: '', withinFilter: '', filterCollections: new Set(),
  filterLicenseClasses: new Set(), resultType: 'all', displayMode: 'images', skinTones: false,
  selected: null, smartEnabled: false, smartExpansion: null,
};
const chromeSmartSearch = new ChromeSmartSearch();
const smartSupported = isDesktopChrome() && chromeSmartSearch.supported;
const SMART_UNSUPPORTED_MESSAGE = 'AI expansion is supported only in desktop Google Chrome. This browser is not supported.';
let smartTimer;
let smartRequest = 0;
let smartRetryArmed = false;
let toastTimer;
let currentResults = [];
let currentSearch = null;
let renderedResultCount = 0;
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
function renderChoiceGroup(container, options, selected, update) {
  const focused = container.contains(document.activeElement) ? document.activeElement.dataset.choice : null;
  const allSelected = selected.size === options.length;
  const fragment = document.createDocumentFragment();
  const addChoice = (id, name, active, action) => {
    const choice = button(name, 'filter-choice', action);
    choice.dataset.choice = id;
    choice.setAttribute('aria-label', name);
    choice.setAttribute('aria-pressed', String(active));
    fragment.append(choice);
  };
  addChoice('all', 'All', allSelected, () => update(new Set(options.map(option => option.id))));
  for (const option of options) {
    addChoice(option.id, option.name, !allSelected && selected.has(option.id), () => {
      const next = allSelected ? new Set() : new Set(selected);
      if (next.has(option.id)) next.delete(option.id);
      else next.add(option.id);
      update(next.size ? next : new Set(options.map(option => option.id)));
    });
  }
  container.replaceChildren(fragment);
  if (focused) [...container.children].find(node => node.dataset.choice === focused)?.focus({ preventScroll: true });
}
function renderFilterControls() {
  renderChoiceGroup($('#collection-options'), state.collections, state.filterCollections, next => {
    state.filterCollections = next; renderFilterControls(); renderGrid();
  });
  renderChoiceGroup($('#license-options'), LICENSE_FILTERS, state.filterLicenseClasses, next => {
    state.filterLicenseClasses = next; renderFilterControls(); renderGrid();
  });
  const matchOptions = [...$('#result-filter').options];
  const focusedMatch = $('#match-options').contains(document.activeElement) ? document.activeElement.dataset.choice : null;
  $('#match-options').replaceChildren(...matchOptions.map(option => {
    const choice = button(option.value === 'all' ? 'All' : option.text, 'filter-choice', () => {
      state.resultType = option.value;
      $('#result-filter').value = option.value;
      renderFilterControls(); renderGrid();
    });
    choice.dataset.choice = option.value;
    choice.setAttribute('aria-label', option.value === 'all' ? 'All' : option.text);
    choice.setAttribute('aria-pressed', String(state.resultType === option.value));
    return choice;
  }));
  if (focusedMatch) [...$('#match-options').children].find(node => node.dataset.choice === focusedMatch)?.focus({ preventScroll: true });
  filterLibraryChoices();
}
function filterLibraryChoices() {
  const query = $('#library-search').value.trim().toLowerCase();
  for (const choice of $('#collection-options').children) choice.hidden = choice.dataset.choice !== 'all' && !choice.textContent.toLowerCase().includes(query);
}
function renderActiveFilters() {
  const container = $('#active-filters');
  const oldButtons = [...container.children];
  const focusedIndex = oldButtons.indexOf(document.activeElement);
  const fragment = document.createDocumentFragment();
  const add = (label, clear) => {
    const chip = button('', 'active-filter', () => { clear(); renderFilterControls(); renderGrid(); });
    chip.setAttribute('aria-label', `Remove ${label}`);
    chip.append(el('span', '', label));
    const cross = el('span', 'ui-symbol', 'close'); cross.setAttribute('aria-hidden', 'true'); chip.append(cross);
    fragment.append(chip);
  };
  for (const [key, options, label] of [['filterCollections', state.collections, 'Library'], ['filterLicenseClasses', LICENSE_FILTERS, 'License']]) {
    if (state[key].size === options.length) continue;
    if (!state[key].size) add(`${label} — None`, () => { state[key] = new Set(options.map(option => option.id)); });
    for (const option of options.filter(option => state[key].has(option.id))) {
      add(`${label} — ${option.name}`, () => {
        state[key].delete(option.id);
        if (!state[key].size) state[key] = new Set(options.map(option => option.id));
      });
    }
  }
  if (state.resultType !== 'all') add(`Match — ${$('#result-filter').selectedOptions[0].text}`, () => { state.resultType = 'all'; $('#result-filter').value = 'all'; });
  if (state.withinFilter) add(`Filter — ${state.withinFilter}`, () => { state.withinFilter = ''; $('#within-filter').value = ''; });
  if (state.skinTones) add('Skin tone variants', () => { state.skinTones = false; $('#skin-tones').checked = false; });
  if (state.smartEnabled) add('AI expansion', () => { state.smartEnabled = false; ++smartRequest; setSmartExpansion(null); saveSmartPreference(); renderSmartToggle(); });
  container.replaceChildren(fragment);
  $('#clear-filters').hidden = !container.children.length;
  if (focusedIndex !== -1) (container.children[Math.min(focusedIndex, container.children.length - 1)] || $('#toggle-filters')).focus({ preventScroll: true });
}
function art(item) {
  const node = el('span', 'emoji');
  node.setAttribute('aria-hidden', 'true');
  if (item.kind === 'image') {
    if (!item.colored && (MONOCHROME_COLLECTIONS.has(item.collection) || item.collection === 'fluent-system-icons' && item.variant !== 'color' || item.collection === 'icon-park' && item.variant !== 'multi-color')) node.classList.add('monochrome');
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
  state.skinTones = params.get('tones') === '1';
  state.selected = state.byId.has(params.get('id')) ? params.get('id') : null;
  $('#search').value = state.query;
  $('#within-filter').value = state.withinFilter;
  $('#skin-tones').checked = state.skinTones;
  $('#result-filter').value = state.resultType;
  $('#display-mode').value = state.displayMode;
  syncViewButtons();
  renderSmartToggle();
  renderFilterControls();
}
function renderExpansionTerms() {
  const panel = $('#expansion-panel');
  const expansion = state.smartExpansion?.sourceQuery === state.query.trim() ? state.smartExpansion : null;
  const terms = expansion?.terms || [];
  const showTerms = state.smartEnabled && terms.length > 0;
  panel.hidden = !showTerms;
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
  renderActiveFilters();
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
    const link = el('a', '', item.license || collection.license);
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
  syncMobileOverlay();
  panel.replaceChildren();
  if (!visible) return;
  renderDetail(state.byId.get(state.selected));
  panel.scrollTop = 0;
}

function setSmartIdle() {
  const toggle = $('#smart-search');
  toggle.closest('.inline-toggle').classList.remove('busy');
  toggle.setAttribute('aria-busy', 'false');
  renderExpansionTerms();
}

function armChromeAIRetry() {
  if (smartRetryArmed) return;
  smartRetryArmed = true;
  const resume = () => {
    document.removeEventListener('pointerdown', resume, true);
    document.removeEventListener('keydown', resume, true);
    smartRetryArmed = false;
    if (state.smartEnabled && state.query.trim()) void runSmartSearch();
  };
  document.addEventListener('pointerdown', resume, { once: true, capture: true });
  document.addEventListener('keydown', resume, { once: true, capture: true });
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
    setSmartIdle();
    renderGrid();
    return;
  }
  const toggle = $('#smart-search');
  toggle.closest('.inline-toggle').classList.add('busy');
  toggle.setAttribute('aria-busy', 'true');
  try {
    const expansion = await chromeSmartSearch.expand(query, 'auto', null, partial => {
      if (request !== smartRequest || query !== state.query.trim()) return;
      setSmartExpansion(partial);
      renderGrid();
    }, { refresh });
    if (request !== smartRequest || query !== state.query.trim()) return;
    setSmartExpansion(expansion);
    setSmartIdle();
    renderGrid();
    if (expansion?.unavailable && !navigator.userActivation?.isActive) armChromeAIRetry();
  } catch {
    if (request !== smartRequest) return;
    setSmartExpansion(null);
    setSmartIdle();
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
  setSmartIdle();
  renderGrid();
  scheduleSmartSearch();
});
$('#search').addEventListener('keydown', event => {
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
$('#skin-tones').addEventListener('change', event => { state.skinTones = event.target.checked; renderGrid(); });
$('#result-filter').addEventListener('change', event => { state.resultType = event.target.value; renderFilterControls(); renderGrid(); });
function setDisplayMode(value) {
  state.displayMode = value;
  $('#display-mode').value = value;
  syncViewButtons();
  renderGrid();
}
function syncViewButtons() {
  for (const button of document.querySelectorAll('[data-view]')) {
    button.setAttribute('aria-pressed', String(button.dataset.view === state.displayMode));
  }
}
$('#display-mode').addEventListener('change', event => setDisplayMode(event.target.value));
for (const button of document.querySelectorAll('[data-view]')) {
  button.addEventListener('click', () => setDisplayMode(button.dataset.view));
}
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
    setSmartIdle();
    renderGrid();
  } else {
    runSmartSearch();
  }
});
function clearFilters() {
  ++smartRequest;
  state.withinFilter = ''; state.filterCollections = new Set(state.collections.map(collection => collection.id));
  state.filterLicenseClasses = new Set(LICENSE_FILTERS.map(option => option.id)); state.resultType = 'all';
  state.skinTones = false; state.smartEnabled = false; setSmartExpansion(null);
  $('#within-filter').value = ''; $('#result-filter').value = 'all'; $('#skin-tones').checked = false; $('#library-search').value = '';
  saveSmartPreference(); renderSmartToggle(); renderFilterControls(); setSmartIdle(); renderGrid();
}
function reset() {
  state.query = ''; $('#search').value = ''; clearFilters();
}
$('#library-search').addEventListener('input', filterLibraryChoices);
$('#reset').addEventListener('click', reset);
$('#reset-filters').addEventListener('click', clearFilters);
$('#clear-filters').addEventListener('click', () => { clearFilters(); $('#toggle-filters').focus({ preventScroll: true }); });
$('#load-more').addEventListener('click', renderNextResultBatch);
if ('IntersectionObserver' in window) {
  new IntersectionObserver(entries => {
    if (!$('#load-more').hidden && entries.some(entry => entry.isIntersecting)) renderNextResultBatch();
  }, { rootMargin: '400px 0px' }).observe($('#load-more'));
}
function setFiltersOpen(open, { focus = true } = {}) {
  $('#filters-panel').hidden = !open;
  $('#toggle-filters').setAttribute('aria-expanded', String(open));
  $('#toggle-filters .ui-symbol').textContent = open ? 'close' : 'tune';
  document.body.classList.toggle('desktop-filters-open', open && !mobileLayout.matches);
  syncMobileOverlay();
  if (focus) $(open ? '#close-filters' : '#toggle-filters').focus({ preventScroll: true });
}
$('#close-filters').addEventListener('click', () => setFiltersOpen(false));
$('#browse-button').addEventListener('click', () => {
  if (!$('#detail').hidden) closePanel();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    if (!$('#detail').hidden) closePanel();
    else if (!$('#filters-panel').hidden) setFiltersOpen(false);
    $('.mobile-more').open = false;
  }
  const modal = mobileLayout.matches ? (!$('#filters-panel').hidden ? $('#filters-panel') : !$('#detail').hidden ? $('#detail') : null) : null;
  if (modal && event.key === 'Tab') {
    const nodes = [...modal.querySelectorAll('button,input,select,summary,a[href]')].filter(node => !node.disabled && node.getClientRects().length);
    const first = nodes[0], last = nodes.at(-1);
    if (event.shiftKey && (document.activeElement === first || !modal.contains(document.activeElement))) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && (document.activeElement === last || !modal.contains(document.activeElement))) { event.preventDefault(); first?.focus(); }
  }
  if (event.key === '/' && !modal && !/INPUT|TEXTAREA|SELECT/.test(event.target.tagName) && !event.metaKey && !event.ctrlKey) {
    event.preventDefault(); $('#search').focus();
  }
});
function syncMobileOverlay() {
  const drawerOpen = mobileLayout.matches && !$('#filters-panel').hidden;
  const detailOpen = mobileLayout.matches && !$('#detail').hidden;
  $('#filter-backdrop').hidden = !drawerOpen;
  document.body.classList.toggle('mobile-overlay', drawerOpen || detailOpen);
  for (const node of document.querySelectorAll('.topbar,.rail,.browse-toolbar,.result-summary,.hero,#grid,#load-more,#empty')) node.inert = drawerOpen || detailOpen;
  $('#detail').inert = drawerOpen;
  for (const [node, open] of [[$('#filters-panel'), drawerOpen], [$('#detail'), detailOpen]]) {
    if (open) { node.setAttribute('role', 'dialog'); node.setAttribute('aria-modal', 'true'); }
    else { node.removeAttribute('role'); node.removeAttribute('aria-modal'); }
  }
}
function applyResponsiveLayout() {
  setFiltersOpen(false, { focus: false });
}
$('#toggle-filters').addEventListener('click', () => setFiltersOpen($('#filters-panel').hidden));
$('#filter-backdrop').addEventListener('click', () => setFiltersOpen(false));
mobileLayout.addEventListener('change', applyResponsiveLayout);
applyResponsiveLayout();
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
