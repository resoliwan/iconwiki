"""Write the runtime collection registry after all catalog builders finish."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

collections = [
    {
        "id": "unicode", "name": "Unicode Emoji", "version": "17.0",
        "catalog": "./data/unicode.json", "sourceUrl": "https://www.unicode.org/emoji/",
        "license": "Unicode-3.0", "licenseClass": "permissive", "licenseUrl": "./data/sources/UNICODE-LICENSE.txt",
        "note": "Character, name, and search metadata come from Unicode and CLDR. Artwork is rendered by the device emoji font.",
    },
    {
        "id": "noto-emoji", "name": "Noto Color Emoji", "version": "2.051",
        "catalog": "./data/noto-emoji.json", "sourceUrl": "https://github.com/googlefonts/noto-emoji",
        "license": "Apache-2.0", "licenseClass": "permissive", "licenseUrl": "./data/sources/NOTO-EMOJI-SVG-LICENSE.txt",
        "note": "Color SVG artwork is self-hosted from the official Noto Emoji release. Names and English keywords come from Unicode and CLDR.",
    },
    {
        "id": "noto-emoji-monochrome", "name": "Noto Emoji", "version": "3.006",
        "catalog": "./data/noto-emoji-monochrome.json", "sourceUrl": "https://fonts.google.com/noto/specimen/Noto+Emoji",
        "license": "OFL-1.1", "licenseClass": "permissive", "licenseUrl": "./data/sources/NOTO-EMOJI-FONT-LICENSE.txt",
        "note": "Monochrome Regular font artwork is self-hosted from Google Fonts. Names and English keywords come from Unicode and CLDR.",
    },
    {
        "id": "fluent-emoji", "name": "Microsoft Fluent Emoji Color",
        "catalog": "./data/fluent-emoji.json", "sourceUrl": "https://github.com/microsoft/fluentui-emoji",
        "license": "MIT", "licenseClass": "permissive", "licenseUrl": "./data/sources/FLUENT-EMOJI-LICENSE.txt",
        "note": "Color SVG artwork and English metadata are self-hosted from the official Fluent Emoji repository.",
    },
    {
        "id": "fluent-emoji-flat", "name": "Microsoft Fluent Emoji Flat",
        "catalog": "./data/fluent-emoji-flat.json", "sourceUrl": "https://github.com/microsoft/fluentui-emoji",
        "license": "MIT", "licenseClass": "permissive", "licenseUrl": "./data/sources/FLUENT-EMOJI-LICENSE.txt",
        "note": "Flat SVG artwork and English metadata are self-hosted from the official Fluent Emoji repository.",
    },
    {
        "id": "fluent-emoji-high-contrast", "name": "Microsoft Fluent Emoji High Contrast",
        "catalog": "./data/fluent-emoji-high-contrast.json", "sourceUrl": "https://github.com/microsoft/fluentui-emoji",
        "license": "MIT", "licenseClass": "permissive", "licenseUrl": "./data/sources/FLUENT-EMOJI-LICENSE.txt",
        "note": "High Contrast SVG artwork is self-hosted from the official Fluent Emoji repository. Skin-tone entries use the same tone-neutral high-contrast artwork supplied upstream.",
    },
    {
        "id": "twemoji", "name": "Twemoji", "version": "17.0.3",
        "catalog": "./data/twemoji.json", "sourceUrl": "https://github.com/jdecked/twemoji",
        "license": "CC-BY-4.0", "licenseClass": "attribution", "licenseUrl": "./data/sources/TWEMOJI-GRAPHICS-LICENSE.txt",
        "note": "Twemoji SVG artwork is self-hosted from the maintained jdecked release. Attribution: Twemoji (CC BY 4.0).",
    },
    {
        "id": "tossface", "name": "Tossface", "version": "1.6.1",
        "catalog": "./data/tossface.json", "sourceUrl": "https://toss.im/tossface/copyright",
        "license": "Tossface custom license", "licenseClass": "restricted", "licenseUrl": "./data/sources/TOSSFACE-COPYRIGHT-NOTICE.txt",
        "note": "Official Tossface SVG artwork is self-hosted without modification. Attribution: Tossface provided by the Toss team. Modification and sale of the typeface itself are prohibited; the latest official copyright guide controls.",
    },
    {
        "id": "blobmoji", "name": "Blobmoji", "version": "15.0",
        "catalog": "./data/blobmoji.json", "sourceUrl": "https://github.com/C1710/blobmoji",
        "license": "Apache-2.0", "licenseClass": "permissive", "licenseUrl": "./data/sources/BLOBMOJI-LICENSE.txt",
        "note": "Blobmoji SVG artwork is self-hosted from the final archived repository snapshot. Regional flag sources are public domain or otherwise copyright-exempt as documented upstream.",
    },
    {
        "id": "material-symbols-outlined", "name": "Google Material Symbols Outlined",
        "catalog": "./data/material-symbols-outlined.json", "sourceUrl": "https://fonts.google.com/icons",
        "license": "Apache-2.0", "licenseClass": "permissive", "licenseUrl": "./data/sources/MATERIAL-SYMBOLS-LICENSE.txt",
        "note": "Icon font and English search metadata are sourced from Google Fonts. The font is self-hosted for offline use.",
    },
    {
        "id": "material-design-icons", "name": "Pictogrammers Material Design Icons", "version": "7.4.47",
        "catalog": "./data/material-design-icons.json", "sourceUrl": "https://pictogrammers.com/library/mdi/",
        "license": "Apache-2.0", "licenseClass": "permissive", "licenseUrl": "./data/sources/MATERIAL-DESIGN-ICONS-LICENSE.txt",
        "note": "SVG artwork and English metadata are self-hosted from the official @mdi/svg package. Brand names may have separate trademark rules.",
    },
    {
        "id": "openmoji-color", "name": "OpenMoji Color", "version": "17.0.0",
        "catalog": "./data/openmoji-color.json", "sourceUrl": "https://openmoji.org/",
        "license": "CC-BY-SA-4.0", "licenseClass": "attribution", "licenseUrl": "./data/sources/OPENMOJI-LICENSE.txt",
        "note": "Color SVG artwork and English search metadata are sourced from OpenMoji. Attribution: OpenMoji (CC BY-SA 4.0).",
    },
    {
        "id": "tabler", "name": "Tabler Icons", "version": "3.47.0",
        "catalog": "./data/tabler.json", "sourceUrl": "https://tabler.io/icons",
        "license": "MIT", "licenseClass": "permissive", "licenseUrl": "./data/sources/TABLER-LICENSE.txt",
        "note": "The complete Tabler Icons v3.47.0 outline SVG set, with official English tags and categories, is self-hosted.",
    },
    {
        "id": "lucide", "name": "Lucide", "version": "0.577.0",
        "catalog": "./data/lucide.json", "sourceUrl": "https://lucide.dev/icons/",
        "license": "ISC", "licenseClass": "permissive", "licenseUrl": "./data/sources/LUCIDE-LICENSE.txt",
        "note": "The complete Lucide v0.577.0 default outline SVG set, with official English tags, aliases, and categories, is self-hosted.",
    },
    {
        "id": "phosphor", "name": "Phosphor Icons", "version": "2.1.1",
        "catalog": "./data/phosphor.json", "sourceUrl": "https://github.com/phosphor-icons/core",
        "license": "MIT", "licenseClass": "permissive", "licenseUrl": "./data/sources/PHOSPHOR-LICENSE.txt",
        "note": "Official Phosphor SVGs in regular, fill, thin, light, bold, and duotone styles.",
    },
    {
        "id": "heroicons", "name": "Heroicons", "version": "2.2.0",
        "catalog": "./data/heroicons.json", "sourceUrl": "https://github.com/tailwindlabs/heroicons",
        "license": "MIT", "licenseClass": "permissive", "licenseUrl": "./data/sources/HEROICONS-LICENSE.txt",
        "note": "Official 24 px Heroicons SVGs in outline and solid styles.",
    },
    {
        "id": "font-awesome-free", "name": "Font Awesome Free", "version": "7.3.1",
        "catalog": "./data/font-awesome-free.json", "sourceUrl": "https://github.com/FortAwesome/Font-Awesome",
        "license": "CC-BY-4.0", "licenseClass": "attribution", "licenseUrl": "./data/sources/FONT-AWESOME-FREE-LICENSE.txt",
        "note": "Official Free SVGs in solid, regular, and brands styles. Attribution is required; brand icons may also be subject to trademark restrictions.",
    },
    {
        "id": "bootstrap-icons", "name": "Bootstrap Icons", "version": "1.13.1",
        "catalog": "./data/bootstrap-icons.json", "sourceUrl": "https://github.com/twbs/icons",
        "license": "MIT", "licenseClass": "permissive", "licenseUrl": "./data/sources/BOOTSTRAP-ICONS-LICENSE.txt",
        "note": "The complete official Bootstrap Icons SVG set is self-hosted.",
    },
    {
        "id": "fluent-system-icons", "name": "Microsoft Fluent UI System Icons", "version": "1.1.341",
        "catalog": "./data/fluent-system-icons.json", "sourceUrl": "https://github.com/microsoft/fluentui-system-icons",
        "license": "MIT", "licenseClass": "permissive", "licenseUrl": "./data/sources/FLUENT-SYSTEM-ICONS-LICENSE.txt",
        "note": "Official 24 px SVGs in regular, filled, and color styles are self-hosted without duplicate sizes.",
    },
    {
        "id": "iconoir", "name": "Iconoir", "version": "7.12.1",
        "catalog": "./data/iconoir.json", "sourceUrl": "https://github.com/iconoir-icons/iconoir",
        "license": "MIT", "licenseClass": "permissive", "licenseUrl": "./data/sources/ICONOIR-LICENSE.txt",
        "note": "Official Iconoir SVGs in regular and solid styles are self-hosted.",
    },
    {
        "id": "ionicons", "name": "Ionicons", "version": "8.1.0",
        "catalog": "./data/ionicons.json", "sourceUrl": "https://github.com/ionic-team/ionicons",
        "license": "MIT", "licenseClass": "permissive", "licenseUrl": "./data/sources/IONICONS-LICENSE.txt",
        "note": "Official Ionicons SVGs in filled, outline, and sharp styles. Logo icons may also be subject to trademark restrictions.",
    },
    {
        "id": "simple-icons", "name": "Simple Icons", "version": "16.32.0",
        "catalog": "./data/simple-icons.json", "sourceUrl": "https://simpleicons.org/",
        "license": "CC0-1.0", "licenseClass": "restricted", "licenseUrl": "./data/sources/SIMPLE-ICONS-LICENSE.txt",
        "note": "Popular brand SVGs and official color metadata are self-hosted from Simple Icons. Brand names and logos remain subject to their owners' trademark rules.",
    },
    {
        "id": "game-icons", "name": "Game Icons",
        "catalog": "./data/game-icons.json", "sourceUrl": "https://game-icons.net/",
        "license": "CC-BY-3.0", "licenseClass": "attribution", "licenseUrl": "./data/sources/GAME-ICONS-LICENSE.txt",
        "note": "Game-oriented SVG artwork is self-hosted from Game-icons.net. Attribution to each icon's credited artist is required under CC BY 3.0.",
    },
    {
        "id": "pixelarticons", "name": "Pixelarticons", "version": "2.4.1",
        "catalog": "./data/pixelarticons.json", "sourceUrl": "https://pixelarticons.com/",
        "license": "MIT", "licenseClass": "permissive", "licenseUrl": "./data/sources/PIXELARTICONS-LICENSE.txt",
        "note": "The free 24 px Pixelarticons SVG set is self-hosted in regular, sharp, and solid styles.",
    },
    {
        "id": "weather-icons", "name": "Weather Icons", "version": "2.0.12",
        "catalog": "./data/weather-icons.json", "sourceUrl": "https://erikflowers.github.io/weather-icons/",
        "license": "OFL-1.1", "licenseClass": "permissive", "licenseUrl": "./data/sources/WEATHER-ICONS-LICENSE.txt",
        "note": "Weather, maritime, moon, wind, and meteorological SVG artwork is self-hosted from the final Weather Icons release.",
    },
    {
        "id": "fxemoji", "name": "Mozilla FxEmojis", "version": "0.0.2",
        "catalog": "./data/fxemoji.json", "sourceUrl": "https://github.com/mozilla/fxemoji",
        "license": "CC-BY-4.0", "licenseClass": "attribution", "licenseUrl": "./data/sources/FXEMOJI-LICENSE.md",
        "note": "Firefox OS emoji SVG artwork is self-hosted from Mozilla's final upstream snapshot. Attribution: Mozilla Foundation (CC BY 4.0).",
    },
]

missing = [item["catalog"] for item in collections if not (ROOT / item["catalog"].removeprefix("./")).is_file()]
if missing:
    raise RuntimeError(f"Missing collection catalogs: {missing}")
if len({item["id"] for item in collections}) != len(collections):
    raise RuntimeError("Collection IDs must be unique.")

(DATA / "collections.json").write_text(json.dumps(collections, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Registered {len(collections)} local collections.")
