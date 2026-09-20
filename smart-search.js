import { searchCatalogMatches } from './catalog.js';

const CACHE_KEY = 'moa.smart-search.v1';
const SUPPORTED_TRANSLATION_LANGUAGES = new Set([
  'ar', 'bg', 'bn', 'cs', 'da', 'de', 'el', 'en', 'es', 'fi', 'fr', 'he', 'hi',
  'hr', 'hu', 'id', 'it', 'ja', 'kn', 'ko', 'lt', 'mr', 'nl', 'no', 'pl', 'pt',
  'ro', 'ru', 'sk', 'sl', 'sv', 'ta', 'te', 'th', 'tr', 'uk', 'vi', 'zh', 'zh-Hant',
]);

// Small offline bridge for common visual searches. Non-English keys stay escaped so
// source files, generated indexes, and exported matching data remain ASCII/English.
const LOCAL_TRANSLATIONS = {
  ko: {
    '\uc5bc\uad74': 'face', '\ub098\ubb34': 'tree', '\uaf43': 'flower', '\ud480': 'grass', '\ud574': 'sun',
    '\ub2ec': 'moon', '\ubcc4': 'star', '\uad6c\ub984': 'cloud', '\ube44': 'rain', '\ub208': 'snow',
    '\uace0\uc591\uc774': 'cat', '\uac1c': 'dog', '\uc0c8': 'bird', '\ubb3c\uace0\uae30': 'fish', '\ud638\ub791\uc774': 'tiger',
    '\uc0ac\uc790': 'lion', '\ucf54\ub07c\ub9ac': 'elephant', '\uc6d0\uc22d\uc774': 'monkey', '\ud1a0\ub07c': 'rabbit',
    '\uc0ac\ub78c': 'person', '\uc544\uae30': 'baby', '\ub0a8\uc790': 'man', '\uc5ec\uc790': 'woman', '\uba38\ub9ac': 'head',
    '\ub208': 'eye', '\ucf54': 'nose', '\uc785': 'mouth', '\uadc0': 'ear', '\uc190': 'hand', '\ubc1c': 'foot',
    '\uc0ac\uacfc': 'apple', '\ubc14\ub098\ub098': 'banana', '\ud3ec\ub3c4': 'grape', '\ub538\uae30': 'strawberry',
    '\ube75': 'bread', '\uc6b0\uc720': 'milk', '\ubb3c': 'water', '\ucee4\ud53c': 'coffee', '\uc74c\uc2dd': 'food',
    '\uc9d1': 'house', '\ud559\uad50': 'school', '\ucc45': 'book', '\uc5f0\ud544': 'pencil', '\uc790\ub3d9\ucc28': 'car',
    '\ubc84\uc2a4': 'bus', '\uae30\ucc28': 'train', '\ube44\ud589\uae30': 'airplane', '\uc790\uc804\uac70': 'bicycle',
    '\uc6c3\ub2e4': 'smile', '\uc6b8\ub2e4': 'cry', '\ub6f0\ub2e4': 'jump', '\ub2ec\ub9ac\ub2e4': 'run', '\uac77\ub2e4': 'walk',
    '\uba39\ub2e4': 'eat', '\ub9c8\uc2dc\ub2e4': 'drink', '\uc790\ub2e4': 'sleep', '\uc77d\ub2e4': 'read', '\uc4f0\ub2e4': 'write',
  },
  ja: { '\u9854': 'face', '\u6728': 'tree', '\u82b1': 'flower', '\u732b': 'cat', '\u72ac': 'dog', '\u5bb6': 'house', '\u672c': 'book', '\u8eca': 'car' },
  zh: { '\u8138': 'face', '\u6811': 'tree', '\u82b1': 'flower', '\u732b': 'cat', '\u72d7': 'dog', '\u5bb6': 'house', '\u4e66': 'book', '\u8f66': 'car' },
  es: { cara: 'face', arbol: 'tree', flor: 'flower', gato: 'cat', perro: 'dog', casa: 'house', libro: 'book', coche: 'car' },
  fr: { visage: 'face', arbre: 'tree', fleur: 'flower', chat: 'cat', chien: 'dog', maison: 'house', livre: 'book', voiture: 'car' },
  de: { gesicht: 'face', baum: 'tree', blume: 'flower', katze: 'cat', hund: 'dog', haus: 'house', buch: 'book', auto: 'car' },
};

const LOCAL_EXPANSIONS = {
  face: ['head', 'person', 'smile', 'expression', 'eyes', 'mouth', 'human'],
  tree: ['forest', 'wood', 'plant', 'nature', 'leaf', 'branch'],
  flower: ['plant', 'garden', 'nature', 'blossom'],
  cat: ['kitten', 'pet', 'animal', 'feline'],
  dog: ['puppy', 'pet', 'animal', 'canine'],
  house: ['home', 'building', 'door', 'family'],
  car: ['vehicle', 'transport', 'drive', 'road'],
  jump: ['leap', 'hop', 'person', 'movement'],
  smile: ['happy', 'face', 'laugh', 'joy'],
  rabbit: ['bunny', 'hare', 'pet', 'animal', 'carrot', 'easter', 'burrow'],
};

export function localTranslation(value, language) {
  const key = String(value).normalize('NFKC').trim().toLowerCase();
  return LOCAL_TRANSLATIONS[language]?.[key] || null;
}

export function guessLanguageFromScript(value) {
  const text = String(value).trim();
  if (!text) return 'en';
  const codepoints = [...text].map(character => character.codePointAt(0));
  const hasRange = (start, end) => codepoints.some(codepoint => codepoint >= start && codepoint <= end);
  if (hasRange(0xAC00, 0xD7AF) || hasRange(0x1100, 0x11FF)) return 'ko';
  if (hasRange(0x3040, 0x30FF)) return 'ja';
  if (hasRange(0x4E00, 0x9FFF)) return 'zh';
  if (hasRange(0x0400, 0x04FF)) return 'ru';
  if (hasRange(0x0600, 0x06FF)) return 'ar';
  if (hasRange(0x0590, 0x05FF)) return 'he';
  if (hasRange(0x0370, 0x03FF)) return 'el';
  if (hasRange(0x0900, 0x097F)) return 'hi';
  if (hasRange(0x0980, 0x09FF)) return 'bn';
  if (hasRange(0x0B80, 0x0BFF)) return 'ta';
  if (hasRange(0x0C00, 0x0C7F)) return 'te';
  if (hasRange(0x0C80, 0x0CFF)) return 'kn';
  if (hasRange(0x0E00, 0x0E7F)) return 'th';
  return null;
}

export function sanitizeExpansion(value, englishQuery) {
  const query = String(englishQuery).trim().toLowerCase();
  const seen = new Set([query]);
  const terms = [];
  for (const raw of value?.terms || []) {
    const term = String(raw).normalize('NFKC').trim().toLowerCase();
    if (!/^[a-z][a-z0-9 -]{0,39}$/.test(term) || seen.has(term)) continue;
    seen.add(term);
    terms.push(term);
    if (terms.length === 12) break;
  }
  return terms;
}

export function buildSmartResults(items, options, expansion = null, resultType = 'all') {
  const effectiveQuery = expansion?.englishQuery || options.query;
  const directMatches = searchCatalogMatches(items, { ...options, query: effectiveQuery });
  const direct = directMatches.map(row => row.item);
  const directIds = new Set(direct.map(item => item.id));
  const related = [];
  const relatedIds = new Set();
  const relatedTermById = new Map();
  const matchTypeById = new Map(directMatches.map(row => [row.item.id, row.matchType]));
  for (const term of expansion?.terms || []) {
    for (const { item } of searchCatalogMatches(items, { ...options, query: term }).slice(0, 120)) {
      if (directIds.has(item.id) || relatedIds.has(item.id)) continue;
      relatedIds.add(item.id);
      relatedTermById.set(item.id, term);
      matchTypeById.set(item.id, 'similar');
      related.push(item);
    }
  }
  const exact = directMatches.filter(row => row.matchType === 'exact').map(row => row.item);
  const keyword = directMatches.filter(row => row.matchType === 'keyword').map(row => row.item);
  const results = resultType === 'exact' ? exact
    : resultType === 'keyword' ? keyword
      : resultType === 'similar' ? related
        : [...direct, ...related];
  return { results, directIds, relatedIds, relatedTermById, matchTypeById, effectiveQuery };
}

function readCache(storage) {
  try { return JSON.parse(storage?.getItem(CACHE_KEY) || '{}'); }
  catch { return {}; }
}

function writeCache(storage, cache) {
  try { storage?.setItem(CACHE_KEY, JSON.stringify(cache)); }
  catch { /* Search still works when browser storage is unavailable. */ }
}

export class ChromeSmartSearch {
  constructor(scope = globalThis, storage = globalThis.localStorage) {
    this.scope = scope;
    this.storage = storage;
    this.detector = null;
    this.languageModel = null;
    this.translators = new Map();
  }

  get supported() {
    return 'LanguageModel' in this.scope;
  }

  async createWithProgress(Api, options, progress) {
    return Api.create({
      ...options,
      monitor(monitor) {
        monitor.addEventListener('downloadprogress', event => {
          progress?.(`Downloading Chrome AI · ${Math.round(event.loaded * 100)}%`);
        });
      },
    });
  }

  async ensureLanguageModel(progress) {
    if (!this.supported) throw new Error('Chrome Prompt API is unavailable in this browser.');
    if (!this.languageModel) {
      progress?.('Starting Chrome AI…');
      this.languageModel = await this.createWithProgress(this.scope.LanguageModel, {
        expectedInputs: [{ type: 'text', languages: ['en'] }],
        expectedOutputs: [{ type: 'text', languages: ['en'] }],
      }, progress);
    }
    return this.languageModel;
  }

  async detectLanguage(text, selectedLanguage, progress) {
    if (selectedLanguage && selectedLanguage !== 'auto') return selectedLanguage;
    const scriptLanguage = guessLanguageFromScript(text);
    if (scriptLanguage) return scriptLanguage;
    if (!('LanguageDetector' in this.scope)) return 'en';
    try {
      if (!this.detector) {
        progress?.('Detecting input language…');
        this.detector = await this.createWithProgress(this.scope.LanguageDetector, {}, progress);
      }
      const results = await this.detector.detect(text);
      const best = results[0];
      return best?.confidence >= 0.45 ? best.detectedLanguage : 'en';
    } catch {
      return 'en';
    }
  }

  async translateToEnglish(text, sourceLanguage, progress) {
    if (sourceLanguage === 'en') return text;
    if (!SUPPORTED_TRANSLATION_LANGUAGES.has(sourceLanguage)) {
      throw new Error(`Chrome translation does not support ${sourceLanguage}.`);
    }
    if (!('Translator' in this.scope)) throw new Error('Chrome Translator API is unavailable in this browser.');
    let translator = this.translators.get(sourceLanguage);
    if (!translator) {
      progress?.(`Translating from ${sourceLanguage}…`);
      translator = await this.createWithProgress(this.scope.Translator, {
        sourceLanguage,
        targetLanguage: 'en',
      }, progress);
      this.translators.set(sourceLanguage, translator);
    }
    return (await translator.translate(text)).trim();
  }

  async expand(query, selectedLanguage = 'auto', progress, partial) {
    const source = String(query).normalize('NFKC').trim();
    if (!source) return null;
    const cache = readCache(this.storage);
    const directCacheKey = `en:${source.toLowerCase()}`;
    if (cache[directCacheKey] && selectedLanguage === 'en') {
      return { sourceQuery: source, sourceLanguage: 'en', ...cache[directCacheKey], cached: true };
    }

    const sourceLanguage = await this.detectLanguage(source, selectedLanguage, progress);
    const offlineTranslation = localTranslation(source, sourceLanguage);
    const englishQuery = offlineTranslation || await this.translateToEnglish(source, sourceLanguage, progress);
    const baseResult = { sourceQuery: source, sourceLanguage, englishQuery, terms: [] };
    partial?.(baseResult);
    const cacheKey = `en:${englishQuery.toLowerCase()}`;
    if (cache[cacheKey]) {
      return { sourceQuery: source, sourceLanguage, ...cache[cacheKey], cached: true };
    }
    let model;
    try { model = await this.ensureLanguageModel(progress); }
    catch {
      const terms = sanitizeExpansion({ terms: LOCAL_EXPANSIONS[englishQuery.toLowerCase()] || [] }, englishQuery);
      return { ...baseResult, terms, local: true };
    }
    progress?.('Finding related English terms…');
    const schema = {
      type: 'object',
      properties: {
        terms: {
          type: 'array',
          minItems: 4,
          maxItems: 12,
          items: { type: 'string' },
        },
      },
      required: ['terms'],
      additionalProperties: false,
    };
    const response = await model.prompt(
      `The English icon search query is "${englishQuery.replaceAll('"', '')}". ` +
      'Return related English terms for finding visually meaningful icons. Include concrete synonyms, objects, actions, expressions, or categories. Use lowercase terms of one to three words. Do not repeat the query.',
      { responseConstraint: schema },
    );
    const terms = sanitizeExpansion(JSON.parse(response), englishQuery);
    const result = { sourceQuery: source, sourceLanguage, englishQuery, terms };
    cache[cacheKey] = { englishQuery, terms };
    const entries = Object.entries(cache).slice(-200);
    writeCache(this.storage, Object.fromEntries(entries));
    return result;
  }
}
