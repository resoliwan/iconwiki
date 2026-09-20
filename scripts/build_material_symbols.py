"""Build a local Material Symbols Outlined catalog and font asset."""
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE = DATA / "sources"
ASSETS = ROOT / "assets" / "material-symbols"
SOURCE.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

METADATA_URL = "https://fonts.google.com/metadata/icons?incomplete=true"
CSS_URL = "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined&display=block"
LICENSE_URL = "https://raw.githubusercontent.com/google/material-design-icons/master/LICENSE"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/140 Safari/537.36"


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


metadata_bytes = fetch(METADATA_URL)
metadata_text = metadata_bytes.decode("utf-8")
metadata = json.loads(metadata_text[metadata_text.index("{"):])

css_bytes = fetch(CSS_URL)
css_text = css_bytes.decode("utf-8")
font_match = re.search(r"src:\s*url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)", css_text)
if not font_match:
    raise RuntimeError("The Google Fonts stylesheet did not include a WOFF2 asset.")
font_url = font_match.group(1)
font_bytes = fetch(font_url)
license_bytes = fetch(LICENSE_URL)

(ASSETS / "material-symbols-outlined.woff2").write_bytes(font_bytes)
(SOURCE / "material-symbols-outlined.css").write_bytes(css_bytes)
(SOURCE / "MATERIAL-SYMBOLS-LICENSE.txt").write_bytes(license_bytes)

icons = []
for icon in metadata["icons"]:
    if "Material Symbols Outlined" in icon.get("unsupported_families", []):
        continue
    glyph = icon["name"]
    keywords = sorted({glyph.replace("_", " "), *icon.get("tags", [])}, key=str.casefold)
    categories = icon.get("categories", [])
    icons.append({
        "id": f"material-symbols-outlined:{glyph}",
        "collection": "material-symbols-outlined",
        "kind": "font",
        "name": glyph.replace("_", " "),
        "glyph": glyph,
        "keywords": keywords,
        "group": categories[0] if categories else "Other",
        "categories": categories,
        "codepoints": [f"{icon['codepoint']:04X}"],
        "popularity": icon.get("popularity"),
    })

assert len(icons) > 3_800, f"Unexpected Material Symbols catalog size: {len(icons)}"
assert len({item["id"] for item in icons}) == len(icons)
(DATA / "material-symbols-outlined.json").write_text(
    json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n",
    encoding="utf-8",
)

collections_path = DATA / "collections.json"
collections = json.loads(collections_path.read_text(encoding="utf-8")) if collections_path.exists() else []
collection = {
    "id": "material-symbols-outlined",
    "name": "Google Material Symbols Outlined",
    "catalog": "./data/material-symbols-outlined.json",
    "sourceUrl": "https://fonts.google.com/icons",
    "license": "Apache-2.0",
    "licenseUrl": "./data/sources/MATERIAL-SYMBOLS-LICENSE.txt",
    "note": "Icon font and English search metadata are sourced from Google Fonts. The font is self-hosted for offline use.",
}
collections = [item for item in collections if item.get("id") != collection["id"]]
collections.append(collection)
collections_path.write_text(json.dumps(collections, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

sources = [
    {"url": METADATA_URL, "sha256": hashlib.sha256(metadata_bytes).hexdigest()},
    {"url": CSS_URL, "file": "material-symbols-outlined.css", "sha256": hashlib.sha256(css_bytes).hexdigest()},
    {"url": font_url, "file": "../../assets/material-symbols/material-symbols-outlined.woff2", "sha256": hashlib.sha256(font_bytes).hexdigest()},
    {"url": LICENSE_URL, "file": "MATERIAL-SYMBOLS-LICENSE.txt", "sha256": hashlib.sha256(license_bytes).hexdigest()},
]
(SOURCE / "material-symbols-manifest.json").write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")
print(f"Built {len(icons):,} Google Material Symbols Outlined icons.")
