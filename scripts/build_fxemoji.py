"""Build the local FxEmojis SVG catalog from Mozilla's final snapshot."""

from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import tarfile
import tempfile
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = DATA / "sources"
ASSETS = ROOT / "assets" / "fxemoji"

VERSION = "0.0.2"
COMMIT = "270af343bee346d8221f87806d2b1eee0438431a"
ARCHIVE_URL = f"https://github.com/mozilla/fxemoji/archive/{COMMIT}.tar.gz"
ARCHIVE_SHA256 = "752f06bbe9048272fbabe474a42943c5a4960d35fb1f44f488e320e2fc8a381d"
UPSTREAM_URL = "https://github.com/mozilla/fxemoji"
PREFIX = f"fxemoji-{COMMIT}/"
USER_AGENT = "iconwiki/1.0"
EXPECTED_COUNT = 1035


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def member_bytes(archive: tarfile.TarFile, name: str) -> bytes:
    source = archive.extractfile(archive.getmember(name))
    if source is None:
        raise RuntimeError(f"Could not read {name}")
    return source.read()


def humanize(raw: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", raw).replace("_", " ").strip().lower()


def main() -> None:
    archive_bytes = download(ARCHIVE_URL)
    actual_sha256 = sha256(archive_bytes)
    if actual_sha256 != ARCHIVE_SHA256:
        raise RuntimeError(f"FxEmojis checksum mismatch: {actual_sha256}")
    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)
    icons: list[dict[str, object]] = []
    unicode_items = json.loads((DATA / "unicode.json").read_text(encoding="utf-8"))
    unicode_by_codepoints = {
        tuple(item.get("codepoints", [])): item
        for item in unicode_items
        if item.get("status") != "component"
    }

    with tarfile.open(fileobj=BytesIO(archive_bytes), mode="r:gz") as archive:
        package = json.loads(member_bytes(archive, PREFIX + "package.json"))
        if package.get("version") != VERSION:
            raise RuntimeError("Unexpected FxEmojis version.")
        license_bytes = member_bytes(archive, PREFIX + "LICENSE.md")
        members = sorted((
            m for m in archive.getmembers()
            if m.isfile() and m.name.startswith(PREFIX + "svgs/FirefoxEmoji/") and m.name.endswith(".svg")
            and not re.search(r"\.layer\d+\.svg$", m.name)
        ), key=lambda m: m.name)
        if len(members) != EXPECTED_COUNT:
            raise RuntimeError(f"Unexpected FxEmojis count: {len(members)}")

        with tempfile.TemporaryDirectory(dir=ASSETS.parent) as temporary:
            staging = Path(temporary) / "fxemoji"
            for member in members:
                relative = Path(member.name).relative_to(PREFIX + "svgs/FirefoxEmoji")
                filename = relative.name
                match = re.fullmatch(r"u([0-9A-Fa-f_]+)(?:-(.+))?\.svg", filename)
                if match:
                    codepoints = match.group(1).upper().split("_")
                    slug = "-".join(codepoints)
                    raw_name = match.group(2) or slug
                else:
                    codepoints = []
                    slug = Path(filename).stem.lower()
                    raw_name = slug
                unicode_item = unicode_by_codepoints.get(tuple(codepoints))
                display_name = unicode_item["name"] if unicode_item else humanize(raw_name)
                svg_bytes = member_bytes(archive, member.name)
                svg_text = svg_bytes.decode("utf-8")
                viewbox = re.search(r'viewBox="([^"]+)"', svg_text)
                if not viewbox:
                    raise RuntimeError(f"Missing viewBox: {filename}")
                target_dir = staging / relative.parent
                target_dir.mkdir(parents=True, exist_ok=True)
                (target_dir / filename).write_bytes(svg_bytes)
                icons.append({
                    "id": f"fxemoji:{slug}", "collection": "fxemoji", "kind": "image",
                    "name": display_name,
                    "keywords": sorted({display_name, *display_name.split(), "emoji", "firefox", *([] if not unicode_item else unicode_item.get("keywords", []))}, key=str.casefold),
                    "group": unicode_item.get("group", "Emoji") if unicode_item else "Emoji",
                    "codepoints": codepoints, "viewBox": viewbox.group(1),
                    "src": f"./assets/fxemoji/{relative.as_posix()}",
                })
            if ASSETS.exists():
                shutil.rmtree(ASSETS)
            staging.replace(ASSETS)

    ids = [str(icon["id"]) for icon in icons]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate FxEmojis IDs were generated.")
    catalog_bytes = (json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    (DATA / "fxemoji.json").write_bytes(catalog_bytes)
    (SOURCES / "FXEMOJI-LICENSE.md").write_bytes(license_bytes)
    (SOURCES / "fxemoji-manifest.json").write_text(json.dumps({
        "name": "FxEmojis", "version": VERSION, "gitCommit": COMMIT,
        "archiveUrl": ARCHIVE_URL, "archiveSha256": actual_sha256,
        "upstreamUrl": UPSTREAM_URL, "assetCount": len(icons),
        "catalog": "../fxemoji.json", "catalogSha256": sha256(catalog_bytes),
        "assets": "../../assets/fxemoji/**/*.svg", "license": "CC-BY-4.0",
        "licenseFile": "FXEMOJI-LICENSE.md",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(icons):,} FxEmojis SVGs from the final upstream snapshot.")


if __name__ == "__main__":
    main()
