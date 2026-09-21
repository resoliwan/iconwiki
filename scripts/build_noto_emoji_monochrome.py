"""Build the local monochrome Noto Emoji catalog and font asset."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = DATA / "sources"
ASSETS = ROOT / "assets" / "noto-emoji-monochrome"

VERSION = "3.006"
FONT_URL = "https://fonts.gstatic.com/s/notoemoji/v65/bMrnmSyK7YY-MEu6aWjPDs-ar6uWaGWuob-r0jwv.ttf"
LICENSE_URL = "https://raw.githubusercontent.com/google/fonts/e44c4b011a820c2cbe2fd2cfa8052037d7edb571/ofl/notoemoji/OFL.txt"
UPSTREAM_URL = "https://fonts.google.com/noto/specimen/Noto+Emoji"
FONT_SHA256 = "988621dc5c9a75eb6144f28faae30317a8e3421b68b28740747b3d739e2326b8"
USER_AGENT = "Mozilla/5.0 (compatible; Moa catalog builder)"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    unicode_rows = json.loads((DATA / "unicode.json").read_text(encoding="utf-8"))
    font_bytes = fetch(FONT_URL)
    if sha256_bytes(font_bytes) != FONT_SHA256:
        raise RuntimeError("Downloaded Noto Emoji font does not match the pinned checksum.")
    license_bytes = fetch(LICENSE_URL)

    ASSETS.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    font_path = ASSETS / "NotoEmoji-Regular.ttf"
    font_path.write_bytes(font_bytes)
    license_path = SOURCES / "NOTO-EMOJI-FONT-LICENSE.txt"
    license_path.write_bytes(license_bytes)

    icons = []
    for row in unicode_rows:
        item = dict(row)
        item["id"] = item["id"].replace("unicode:", "noto-emoji-monochrome:", 1)
        item["collection"] = "noto-emoji-monochrome"
        icons.append(item)

    if len(icons) != 3_953:
        raise RuntimeError(f"Unexpected Noto Emoji catalog size: {len(icons)}")
    if len({item["id"] for item in icons}) != len(icons):
        raise RuntimeError("Duplicate Noto Emoji IDs were generated.")

    catalog_path = DATA / "noto-emoji-monochrome.json"
    catalog_path.write_text(
        json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "name": "Noto Emoji",
        "version": VERSION,
        "upstreamUrl": UPSTREAM_URL,
        "style": "monochrome font",
        "assetCount": len(icons),
        "font": "../../assets/noto-emoji-monochrome/NotoEmoji-Regular.ttf",
        "fontSha256": sha256_file(font_path),
        "catalog": "../noto-emoji-monochrome.json",
        "catalogSha256": sha256_file(catalog_path),
        "license": "OFL-1.1",
        "licenseFile": license_path.name,
    }
    (SOURCES / "noto-emoji-monochrome-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built {len(icons):,} monochrome Noto Emoji glyphs from v{VERSION}.")


if __name__ == "__main__":
    main()
