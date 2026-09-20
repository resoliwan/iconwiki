import { loadCatalog } from './catalog.js';
import { emptyMatching, isEnglishText, loadDraft, saveDraft, upsertMatch, validateMatching, downloadMatching } from './matching.js';
import { buildSmartResults, ChromeSmartSearch, guessLanguageFromScript } from './smart-search.js';

const $ = selector => document.querySelector(selector);
const MAX_RENDERED_RESULTS = 600;
const MONOCHROME_COLLECTIONS = new Set(['material-design-icons', 'tabler', 'lucide', 'phosphor', 'heroicons', 'font-awesome-free', 'bootstrap-icons', 'iconoir', 'ionicons']);
const state = { items: [], collections: [], byId: new Map(), query: '', collection: '', licenseClass: '', resultType: 'all', inputLanguage: 'auto', skinTones: false, selected: null, mode: 'detail', matching: emptyMatching(), word: '', meaning: '', smartEnabled: false, smartExpansion: null };
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
  for (const [key, value] of Object.entries({ q: state.query, collection: state.collection, license: state.licenseClass, match: state.resultType === 'all' ? '' : state.resultType, language: state.inputLanguage === 'auto' ? '' : state.inputLanguage, smart: state.smartEnabled ? '1' : '', tones: state.skinTones ? '1' : '', id: state.selected || '', view: state.mode === 'matches' ? 'matches' : '' })) {
    if (value) url.searchParams.set(key, value);
    else url.searchParams.delete(key);
  }
  history.replaceState(null, '', url);
}
function readURL() {
  const params = new URLSearchParams(location.search);
  state.query = params.get('q') || '';
  state.collection = params.get('collection') || '';
  state.licenseClass = params.get('license') || '';
  state.resultType = ['direct', 'related'].includes(params.get('match')) ? params.get('match') : 'all';
  state.inputLanguage = params.get('language') || 'auto';
  const detectedLanguage = guessLanguageFromScript(state.query);
  state.smartEnabled = params.get('smart') === '1' || Boolean(detectedLanguage && detectedLanguage !== 'en');
  state.skinTones = params.get('tones') === '1';
  state.selected = state.byId.has(params.get('id')) ? params.get('id') : null;
  state.mode = params.get('view') === 'matches' ? 'matches' : 'detail';
  $('#search').value = state.query;
  $('#skin-tones').checked = state.skinTones;
  $('#collection-filter').value = state.collection;
  $('#license-filter').value = state.licenseClass;
  $('#result-filter').value = state.resultType;
  $('#language-filter').value = state.inputLanguage;
  $('#smart-search').setAttribute('aria-pressed', String(state.smartEnabled));
}
function renderGrid() {
  const expansion = state.smartExpansion?.sourceQuery === state.query.trim() ? state.smartExpansion : null;
  const search = buildSmartResults(state.items, state, expansion, state.resultType);
  const { results } = search;
  const renderedResults = results.slice(0, MAX_RENDERED_RESULTS);
  const mapped = new Set(state.matching.matches.map(row => row.assetId));
  const fragment = document.createDocumentFragment();
  for (const item of renderedResults) {
    const card = button('', 'emoji-card', () => select(item.id));
    card.dataset.id = item.id;
    card.setAttribute('aria-label', item.name);
    card.setAttribute('aria-pressed', String(state.selected === item.id));
    card.title = `${item.name}\n${item.id}`;
    card.append(art(item), el('span', 'card-name', item.name));
    if (search.relatedIds.has(item.id)) {
      const related = el('span', 'related-mark', 'RELATED');
      related.title = `Related term: ${search.relatedTermById.get(item.id)}`;
      card.append(related);
    }
    if (mapped.has(item.id)) card.append(el('span', 'mapped-mark', '✓'));
    fragment.append(card);
  }
  $('#grid').replaceChildren(fragment);
  $('#grid').setAttribute('aria-busy', 'false');
  $('#empty').hidden = results.length > 0;
  $('#result-count').textContent = results.length > MAX_RENDERED_RESULTS
    ? `${results.length.toLocaleString()} results · showing first ${MAX_RENDERED_RESULTS.toLocaleString()}`
    : `${results.length.toLocaleString()} results`;
  $('#match-count').textContent = state.matching.matches.length;
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
  state.mode = 'detail';
  renderPanel();
  renderGrid();
  const old = [...$('#grid').children].find(node => node.dataset.id === oldId);
  (old || $('#search')).focus({ preventScroll: true });
}
function select(id) {
  state.selected = id;
  state.mode = 'detail';
  renderPanel();
  for (const card of $('#grid').children) card.setAttribute('aria-pressed', String(card.dataset.id === id));
  updateURL();
  $('#detail .close-button')?.focus({ preventScroll: true });
}
async function copy(value, message) {
  try { await navigator.clipboard.writeText(value); toast(message); }
  catch { toast('Clipboard access is unavailable. Select and copy the text from the details panel.'); }
}
function persistMatching() {
  try { saveDraft(state.matching); return true; }
  catch { toast('Browser storage is unavailable. Export the matches as JSON.'); return false; }
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

  const form = el('form', 'match-form');
  form.append(el('h3', 'section-label', 'Connect to a word'));
  const wordLabel = el('label', '', 'English word');
  const word = el('input');
  word.name = 'word'; word.required = true; word.placeholder = 'Example: cat'; word.value = state.word;
  word.addEventListener('input', () => { state.word = word.value; });
  wordLabel.append(word);
  const meaningLabel = el('label', '', 'English meaning · optional');
  const meaning = el('input');
  meaning.name = 'meaning'; meaning.placeholder = 'Example: a small domesticated animal'; meaning.value = state.meaning;
  meaning.addEventListener('input', () => { state.meaning = meaning.value; });
  meaningLabel.append(meaning);
  const submit = el('button', 'button', 'Connect this image');
  submit.type = 'submit';
  form.append(wordLabel, meaningLabel, submit, el('p', 'hint', 'Saved as a browser draft. Use Export above to keep a JSON file.'));
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (!word.value.trim()) { word.focus(); return; }
    if (!isEnglishText(word.value) || !isEnglishText(meaning.value)) {
      toast('Enter the word and meaning in English.');
      (!isEnglishText(word.value) ? word : meaning).focus();
      return;
    }
    const asset = item.kind === 'emoji' ? { emoji: item.emoji }
      : item.kind === 'font' ? { glyph: item.glyph }
      : { src: item.src };
    const row = { word: word.value.trim(), meaning: meaning.value.trim(), assetId: item.id, collection: item.collection,
      ...asset, status: 'pending_review' };
    state.matching = upsertMatch(state.matching, row);
    const saved = persistMatching();
    renderGrid();
    if (saved) toast(`Connected ${row.word}. Review it in Word Matches.`);
  });
  panel.append(form);
}
function renderMatches() {
  const panel = $('#detail');
  panel.append(panelHeading('WORD MATCHES'), el('h2', '', 'Word matches'), el('p', 'english-name', `${state.matching.matches.length} connected · Export JSON to keep a file.`));
  if (!state.matching.matches.length) panel.append(el('p', 'hint', 'Select an image and enter an English word to create the first match.'));
  const list = el('div', 'match-list');
  state.matching.matches.forEach((row, index) => {
    const item = state.byId.get(row.assetId);
    const card = el('div', 'match-row');
    const main = button('', 'match-row-main', () => {
      if (!item) { toast('The library for this match is not loaded.'); return; }
      state.word = row.word; state.meaning = row.meaning;
      select(item.id);
    });
    if (item) main.append(art(item));
    const text = el('div');
    text.append(el('strong', '', row.word), el('p', '', row.meaning || (item?.name || 'Library unavailable')));
    main.append(text);
    const controls = el('div', 'match-row-controls');
    const label = el('label');
    const check = el('input'); check.type = 'checkbox'; check.checked = row.status === 'approved';
    check.addEventListener('change', () => {
      row.status = check.checked ? 'approved' : 'pending_review';
      persistMatching();
    });
    label.append(check, document.createTextNode(' Approved'));
    controls.append(label, button('Remove', 'text-button', () => {
      state.matching.matches.splice(index, 1);
      persistMatching(); renderPanel(); renderGrid();
    }));
    card.append(main, controls); list.append(card);
  });
  panel.append(list);
}
function renderPanel() {
  const panel = $('#detail');
  const visible = state.mode === 'matches' || Boolean(state.selected);
  panel.hidden = !visible;
  $('#workspace').classList.toggle('with-detail', visible);
  $('#matches-button').classList.toggle('active', state.mode === 'matches');
  $('#browse-button').classList.toggle('active', state.mode !== 'matches');
  panel.replaceChildren();
  if (!visible) return;
  if (state.mode === 'matches') renderMatches();
  else renderDetail(state.byId.get(state.selected));
  panel.scrollTop = 0;
}

function setSmartStatus(message = '', busy = false) {
  const status = $('#smart-status');
  status.textContent = message;
  status.hidden = !message;
  $('#smart-search').classList.toggle('busy', busy);
}

function describeExpansion(expansion) {
  const related = expansion.terms.length ? `${expansion.terms.length} related terms` : 'No related terms';
  if (expansion.sourceLanguage !== 'en' || expansion.sourceQuery.toLowerCase() !== expansion.englishQuery.toLowerCase()) {
    return `Translated “${expansion.sourceQuery}” → “${expansion.englishQuery}” · ${related}${expansion.cached ? ' · cached' : ''}`;
  }
  return `Chrome AI · ${related}${expansion.cached ? ' · cached' : ''}`;
}

async function runSmartSearch() {
  clearTimeout(smartTimer);
  const query = state.query.trim();
  const request = ++smartRequest;
  if (!state.smartEnabled || !query) {
    state.smartExpansion = null;
    setSmartStatus();
    renderGrid();
    return;
  }
  setSmartStatus('Starting smart search…', true);
  try {
    const expansion = await chromeSmartSearch.expand(query, state.inputLanguage, message => {
      if (request === smartRequest) setSmartStatus(message, true);
    }, partial => {
      if (request !== smartRequest || query !== state.query.trim()) return;
      state.smartExpansion = partial;
      setSmartStatus(describeExpansion(partial), true);
      renderGrid();
    });
    if (request !== smartRequest || query !== state.query.trim()) return;
    state.smartExpansion = expansion;
    setSmartStatus(describeExpansion(expansion));
    renderGrid();
  } catch (error) {
    if (request !== smartRequest) return;
    state.smartExpansion = null;
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
  const detectedLanguage = guessLanguageFromScript(state.query);
  if (detectedLanguage && detectedLanguage !== 'en') {
    state.smartEnabled = true;
    $('#smart-search').setAttribute('aria-pressed', 'true');
  }
  state.smartExpansion = null;
  setSmartStatus(state.smartEnabled && state.query.trim() ? 'Waiting to expand…' : '');
  renderGrid();
  scheduleSmartSearch();
});
$('#skin-tones').addEventListener('change', event => { state.skinTones = event.target.checked; renderGrid(); });
$('#collection-filter').addEventListener('change', event => { state.collection = event.target.value; renderGrid(); });
$('#license-filter').addEventListener('change', event => { state.licenseClass = event.target.value; renderGrid(); });
$('#result-filter').addEventListener('change', event => { state.resultType = event.target.value; renderGrid(); });
$('#language-filter').addEventListener('change', event => {
  state.inputLanguage = event.target.value;
  state.smartExpansion = null;
  renderGrid();
  if (state.smartEnabled) runSmartSearch();
});
$('#smart-search').addEventListener('click', () => {
  state.smartEnabled = !state.smartEnabled;
  $('#smart-search').setAttribute('aria-pressed', String(state.smartEnabled));
  if (!state.smartEnabled) {
    ++smartRequest;
    state.smartExpansion = null;
    setSmartStatus();
    renderGrid();
  } else runSmartSearch();
});
function reset() {
  ++smartRequest;
  state.query = ''; state.collection = ''; state.licenseClass = ''; state.resultType = 'all'; state.smartExpansion = null;
  $('#search').value = ''; $('#collection-filter').value = ''; $('#license-filter').value = ''; $('#result-filter').value = 'all';
  setSmartStatus(); renderGrid();
}
$('#reset').addEventListener('click', reset);
$('#browse-button').addEventListener('click', () => { closePanel(); reset(); });
$('#matches-button').addEventListener('click', () => {
  state.mode = 'matches'; state.selected = null; renderPanel(); renderGrid();
  $('#detail .close-button').focus({ preventScroll: true });
});
$('#open-matching').addEventListener('click', () => $('#matching-file').click());
$('#matching-file').addEventListener('change', async event => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    const imported = validateMatching(JSON.parse(await file.text()));
    let merged = state.matching;
    for (const row of imported.matches) merged = upsertMatch(merged, row);
    state.matching = merged;
    const saved = persistMatching();
    state.mode = 'matches'; state.selected = null; renderPanel(); renderGrid();
    if (saved) toast(`Imported ${imported.matches.length} matches from ${file.name}. Existing word and meaning pairs were updated.`);
  } catch (error) { toast(`Could not open the file. ${error.message}`); }
  event.target.value = '';
});
$('#export-matching').addEventListener('click', () => {
  downloadMatching(state.matching);
  toast('The matching JSON download has started.');
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !$('#detail').hidden) closePanel();
  if (event.key === '/' && !/INPUT|TEXTAREA|SELECT/.test(event.target.tagName) && !event.metaKey && !event.ctrlKey) {
    event.preventDefault(); $('#search').focus();
  }
});
window.addEventListener('popstate', () => { readURL(); renderPanel(); renderGrid(); });

try {
  const { collections, items } = await loadCatalog();
  state.collections = collections; state.items = items;
  state.byId = new Map(items.map(item => [item.id, item]));
  for (const collection of collections) {
    const option = el('option', '', collection.name); option.value = collection.id;
    $('#collection-filter').append(option);
  }
  try { state.matching = loadDraft(); }
  catch { toast('Could not read the saved draft. Open an exported JSON file if one is available.'); }
  readURL(); renderPanel(); renderGrid();
  if (state.smartEnabled && state.query.trim()) runSmartSearch();
} catch (error) {
  $('#grid').setAttribute('aria-busy', 'false');
  $('#result-count').textContent = 'Data failed to load';
  const notice = el('p', 'hint', `${error.message} · Make sure the app is opened through its static server.`);
  $('#grid').replaceChildren(notice);
}
