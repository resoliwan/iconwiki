"""Build the local OpenMoji color SVG catalog from a pinned upstream commit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = DATA / "sources"
ASSETS = ROOT / "assets" / "openmoji"

VERSION = "17.0.0"
COMMIT = "f9fc506a3f913be9897ab0181d611d4c910a4104"
ARCHIVE_URL = f"https://github.com/hfg-gmuend/openmoji/archive/{COMMIT}.tar.gz"
ARCHIVE_SHA256 = "642e6034698fb28d209e4985112ae9b6eb3b8dea28c4ab187ed1883abfbad344"
ARCHIVE_ROOT = f"openmoji-{COMMIT}"
EXPECTED_COUNT = 4_495

CATALOG_PATH = DATA / "openmoji-color.json"
RAW_METADATA_PATH = SOURCES / f"openmoji-{VERSION}.json"
LICENSE_PATH = SOURCES / "OPENMOJI-LICENSE.txt"
MANIFEST_PATH = SOURCES / "openmoji-manifest.json"

GROUP_NAMES = {
    "smileys-emotion": "Smileys & Emotion",
    "people-body": "People & Body",
    "animals-nature": "Animals & Nature",
    "food-drink": "Food & Drink",
    "travel-places": "Travel & Places",
    "activities": "Activities",
    "objects": "Objects",
    "symbols": "Symbols",
    "flags": "Flags",
    "component": "Component",
    "extras-openmoji": "OpenMoji Extras",
    "extras-unicode": "Unicode Extras",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "LocalIconLibrary/1.0"})
    with urllib.request.urlopen(request, timeout=300) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output, length=1024 * 1024)


def split_keywords(*values: str) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        for keyword in value.split(","):
            keyword = keyword.strip()
            folded = keyword.casefold()
            if keyword and folded not in seen:
                seen.add(folded)
                result.append(keyword)
    return sorted(result, key=str.casefold)


def build_item(row: dict) -> dict:
    hexcode = row["hexcode"]
    source_group = row["group"]
    subgroup = row["subgroups"]
    skin_tone = bool(row["skintone"])
    item = {
        "id": f"openmoji-color:{hexcode}",
        "collection": "openmoji-color",
        "kind": "image",
        "name": row["annotation"],
        "src": f"./assets/openmoji/{hexcode}.svg",
        "emoji": row["emoji"],
        "keywords": split_keywords(row["annotation"], row["tags"], row["openmoji_tags"]),
        "group": GROUP_NAMES.get(source_group, source_group.replace("-", " ").title()),
        "subgroup": subgroup.replace("-", " ").title(),
        "sourceGroup": source_group,
        "sourceSubgroup": subgroup,
        "codepoints": hexcode.split("-"),
        "unicodeVersion": str(row["unicode"]),
        "skinTone": skin_tone,
        "author": row["openmoji_author"],
        "date": row["openmoji_date"],
    }
    if skin_tone:
        item["skinToneType"] = str(row["skintone_combination"])
        item["skinToneBaseEmoji"] = row["skintone_base_emoji"]
        item["skinToneBaseCodepoints"] = row["skintone_base_hexcode"].split("-")
    return item


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="openmoji-build-") as temp_name:
        temp = Path(temp_name)
        archive_path = temp / "openmoji.tar.gz"
        staged_assets = temp / "assets"
        staged_assets.mkdir()
        download(ARCHIVE_URL, archive_path)

        archive_digest = sha256_file(archive_path)
        if archive_digest != ARCHIVE_SHA256:
            raise RuntimeError(
                f"OpenMoji archive checksum changed: expected {ARCHIVE_SHA256}, got {archive_digest}"
            )

        metadata_bytes = None
        license_bytes = None
        asset_digests: dict[str, str] = {}
        svg_prefix = f"{ARCHIVE_ROOT}/color/svg/"
        with tarfile.open(archive_path, mode="r:gz") as archive:
            for member in archive:
                if not member.isfile():
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                if member.name == f"{ARCHIVE_ROOT}/data/openmoji.json":
                    metadata_bytes = extracted.read()
                elif member.name == f"{ARCHIVE_ROOT}/LICENSE.txt":
                    license_bytes = extracted.read()
                elif member.name.startswith(svg_prefix) and member.name.endswith(".svg"):
                    filename = Path(member.name).name
                    payload = extracted.read()
                    (staged_assets / filename).write_bytes(payload)
                    asset_digests[filename] = sha256_bytes(payload)

        if metadata_bytes is None or license_bytes is None:
            raise RuntimeError("The pinned OpenMoji archive is missing metadata or license files.")

        metadata = json.loads(metadata_bytes)
        if len(metadata) != EXPECTED_COUNT:
            raise RuntimeError(f"Expected {EXPECTED_COUNT:,} metadata rows, found {len(metadata):,}.")

        expected_files = {f"{row['hexcode']}.svg" for row in metadata}
        actual_files = set(asset_digests)
        if actual_files != expected_files:
            missing = sorted(expected_files - actual_files)[:5]
            extra = sorted(actual_files - expected_files)[:5]
            raise RuntimeError(f"SVG/metadata mismatch. Missing: {missing}; extra: {extra}")

        items = [build_item(row) for row in metadata]
        ids = [item["id"] for item in items]
        if len(set(ids)) != len(ids):
            raise RuntimeError("OpenMoji catalog contains duplicate IDs.")
        if any(not item["name"] or not item["keywords"] for item in items):
            raise RuntimeError("Every OpenMoji item must have an English name and search metadata.")

        catalog_bytes = (
            json.dumps(items, ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        if ASSETS.exists():
            shutil.rmtree(ASSETS)
        shutil.move(staged_assets, ASSETS)
        CATALOG_PATH.write_bytes(catalog_bytes)
        RAW_METADATA_PATH.write_bytes(metadata_bytes)
        LICENSE_PATH.write_bytes(license_bytes)

        manifest = {
            "collection": "openmoji-color",
            "name": "OpenMoji Color",
            "version": VERSION,
            "commit": COMMIT,
            "sourceUrl": "https://openmoji.org/",
            "repositoryUrl": "https://github.com/hfg-gmuend/openmoji",
            "archiveUrl": ARCHIVE_URL,
            "archiveSha256": archive_digest,
            "license": "CC-BY-SA-4.0",
            "licenseFile": "OPENMOJI-LICENSE.txt",
            "metadataFile": RAW_METADATA_PATH.name,
            "metadataSha256": sha256_bytes(metadata_bytes),
            "catalogFile": f"../{CATALOG_PATH.name}",
            "catalogSha256": sha256_bytes(catalog_bytes),
            "assetDirectory": "../../assets/openmoji",
            "assetCount": len(asset_digests),
            "assetsSha256": hashlib.sha256(
                "".join(f"{name}:{asset_digests[name]}\n" for name in sorted(asset_digests)).encode()
            ).hexdigest(),
            "attribution": "OpenMoji, licensed under CC BY-SA 4.0",
        }
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    total_size = sum(path.stat().st_size for path in ASSETS.glob("*.svg"))
    print(f"Built {len(items):,} OpenMoji color SVG icons ({total_size / 1024 / 1024:.1f} MiB).")


if __name__ == "__main__":
    main()
