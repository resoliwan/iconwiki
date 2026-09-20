const KEY = 'icon-library.matches.v1';

export function validateMatching(value) {
  if (!value || value.schemaVersion !== 1 || !Array.isArray(value.matches)) {
    throw new Error('Open a matching JSON file with schemaVersion 1 and a matches array.');
  }
  const keys = new Set();
  for (const row of value.matches) {
    if (!row || typeof row.word !== 'string' || !row.word.trim() ||
        typeof row.meaning !== 'string' || typeof row.assetId !== 'string' || !row.assetId ||
        !['pending_review', 'approved'].includes(row.status)) throw new Error('Check each match word, meaning, asset ID, and status.');
    if (!isEnglishText(row.word) || !isEnglishText(row.meaning)) {
      throw new Error('Match word and meaning values must be stored in English.');
    }
    const key = matchKey(row);
    if (keys.has(key)) throw new Error('The matching file contains a duplicate word and meaning pair.');
    keys.add(key);
  }
  return value;
}

export function isEnglishText(value) {
  return /^[\x20-\x7E]*$/.test(value);
}

export const matchKey = row => JSON.stringify([row.word.trim().toLowerCase(), row.meaning.trim()]);
export const emptyMatching = () => ({ schemaVersion: 1, matches: [] });
export function upsertMatch(document, row) {
  const next = structuredClone(document);
  const index = next.matches.findIndex(old => matchKey(old) === matchKey(row));
  if (index >= 0) next.matches[index] = row;
  else next.matches.push(row);
  return validateMatching(next);
}
export function loadDraft() {
  const text = localStorage.getItem(KEY);
  return text ? validateMatching(JSON.parse(text)) : emptyMatching();
}
export function saveDraft(document) { localStorage.setItem(KEY, JSON.stringify(validateMatching(document))); }
export function downloadMatching(document) {
  const blob = new Blob([JSON.stringify(validateMatching(document), null, 2) + '\n'], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = documentElement('a');
  link.href = url;
  link.download = 'word-matches.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function documentElement(tag) { return globalThis.document.createElement(tag); }
