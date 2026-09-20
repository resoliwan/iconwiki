# Moa

Moa is a local, static icon browser built to make searching across icon and emoji libraries fast and easy.

It loads each catalog into browser memory, searches English names and keywords, displays every result at a consistent size, and opens a detail panel when an item is selected. The included matching workflow can save an English word and its selected visual asset as JSON.

## Included libraries

| Library | Version | License | Items |
| --- | ---: | --- | ---: |
| Unicode Emoji | 17.0 | [Unicode-3.0](./data/sources/UNICODE-LICENSE.txt) | 3,953 |
| Google Noto Emoji | 2.051 | [Apache-2.0](./data/sources/NOTO-EMOJI-SVG-LICENSE.txt) | 3,691 |
| Microsoft Fluent Emoji Color | — | [MIT](./data/sources/FLUENT-EMOJI-LICENSE.txt) | 3,145 |
| Google Material Symbols Outlined | — | [Apache-2.0](./data/sources/MATERIAL-SYMBOLS-LICENSE.txt) | 3,912 |
| Pictogrammers Material Design Icons | 7.4.47 | [Apache-2.0](./data/sources/MATERIAL-DESIGN-ICONS-LICENSE.txt) | 7,447 |
| OpenMoji Color | 17.0.0 | [CC-BY-SA-4.0](./data/sources/OPENMOJI-LICENSE.txt) | 4,495 |
| Tabler Icons | 3.47.0 | [MIT](./data/sources/TABLER-LICENSE.txt) | 5,148 |
| Lucide | 0.577.0 | [ISC](./data/sources/LUCIDE-LICENSE.txt) | 1,703 |
| Phosphor Icons | 2.1.1 | [MIT](./data/sources/PHOSPHOR-LICENSE.txt) | 9,072 |
| Heroicons | 2.2.0 | [MIT](./data/sources/HEROICONS-LICENSE.txt) | 648 |
| Font Awesome Free | 7.3.1 | [CC-BY-4.0](./data/sources/FONT-AWESOME-FREE-LICENSE.txt) | 2,883 |
| Bootstrap Icons | 1.13.1 | [MIT](./data/sources/BOOTSTRAP-ICONS-LICENSE.txt) | 2,078 |
| Microsoft Fluent UI System Icons | 1.1.341 | [MIT](./data/sources/FLUENT-SYSTEM-ICONS-LICENSE.txt) | 5,468 |
| Iconoir | 7.12.1 | [MIT](./data/sources/ICONOIR-LICENSE.txt) | 1,671 |
| Ionicons | 8.1.0 | [MIT](./data/sources/IONICONS-LICENSE.txt) | 1,357 |
| **Total** |  |  | **56,671** |

Counts describe the catalogs currently generated in this repository. Unicode Emoji uses the device emoji font; the other collections use self-hosted assets.

## Features

- Search English names, keywords, tags, aliases, and categories.
- Translate non-English searches to English and generate related terms with Chrome's built-in AI.
- Filter results by library, license class, direct or related match, input language, and skin tone variants.
- Compare emoji, color artwork, outline icons, filled icons, and alternate weights in one grid.
- Open an item to inspect its source, identifier, keywords, license, and asset path.
- Store word-to-icon decisions in a small JSON matching file.
- Run as a static site with no application server or database.

License classes are intentionally broad: **Permissive** covers MIT, ISC, Apache-2.0, and Unicode-3.0; **Attribution / ShareAlike** covers CC BY and CC BY-SA assets; **Restricted / Brand** identifies brand marks and other assets that may require additional permission. Commercial use is not a separate class because it can be allowed across more than one class when each license condition is followed.

## Run locally

```bash
npm start
```

Then open [http://127.0.0.1:4174](http://127.0.0.1:4174).

The HTTP server is only used to serve static files. Search and filtering run entirely in the browser.

## Chrome smart search

Select **Smart** to use Chrome's built-in AI. Non-English input is detected and translated to English with the Language Detector and Translator APIs. The Prompt API then generates related English icon terms. Direct matches remain first, and the match filter can show all, direct, or related results.

Chrome downloads its built-in models when needed. Expanded searches are cached in browser storage. If a built-in API is unavailable, direct local search continues to work.

## Matching files

The browser can open and update a JSON file with this structure:

```json
{
  "version": 1,
  "matches": {
    "cat": {
      "id": "unicode:1F408",
      "collection": "unicode",
      "name": "cat",
      "asset": "🐈"
    }
  }
}
```

Browsers with the File System Access API can update the selected file directly. Other browsers download an updated copy.

## Rebuild the catalogs

```bash
npm run data
```

The build scripts download or read each upstream source, generate compact catalog JSON, copy the required assets into the repository, and rebuild `data/collections.json`.

To add another library:

1. Add a builder in `scripts/`.
2. Generate its catalog JSON in `data/`.
3. Store its assets under `assets/` when required.
4. Add its license text under `data/sources/`.
5. Register the collection in `scripts/build_collections.py`.
6. Add the builder to the `data` script in `package.json`.

## Licensing

Moa's original source code is licensed under the [MIT License](./LICENSE).

Included icons, emoji artwork, fonts, and metadata retain their respective upstream licenses and are not covered by Moa's MIT License. See [Third-Party Notices](./THIRD_PARTY_NOTICES.md) and the license texts in [`data/sources/`](./data/sources/).

Brand icons may also be subject to their owners' trademark guidelines. Moa does not grant trademark rights or imply endorsement by any brand owner.
# moa
