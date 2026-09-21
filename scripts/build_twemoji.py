"""Build a local Twemoji SVG catalog from a pinned stable release."""

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
ASSETS = ROOT / "assets" / "twemoji"

VERSION = "17.0.3"
COMMIT = "b6b55fef1e8636b540a6d016a4729ca8cdf2e60b"
ARCHIVE_URL = f"https://github.com/jdecked/twemoji/archive/{COMMIT}.tar.gz"
ARCHIVE_SHA256 = "705d79de1460e5e775f362f0d0f01fbe3ef8d65bf4648c490e4649704584f747"
ARCHIVE_ROOT = f"twemoji-{COMMIT}"
EXPECTED_UPSTREAM_ASSET_COUNT = 4_009
EXPECTED_CATALOG_COUNT = 3_953

CATALOG_PATH = DATA / "twemoji.json"
LICENSE_PATH = SOURCES / "TWEMOJI-GRAPHICS-LICENSE.txt"
MANIFEST_PATH = SOURCES / "twemoji-manifest.json"


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


def normalized(codes: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Match Twemoji filenames while ignoring emoji presentation selectors."""

    return tuple(f"{int(code, 16):x}" for code in codes if int(code, 16) != 0xFE0F)


def asset_digest(digests: dict[str, str]) -> str:
    rows = "".join(f"{name}:{digests[name]}\n" for name in sorted(digests))
    return sha256_bytes(rows.encode())


def main() -> None:
    unicode_rows = json.loads((DATA / "unicode.json").read_text(encoding="utf-8"))
    unicode_by_sequence = {normalized(row["codepoints"]): row for row in unicode_rows}
    if len(unicode_rows) != EXPECTED_CATALOG_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_CATALOG_COUNT:,} Unicode rows, found {len(unicode_rows):,}."
        )
    if len(unicode_by_sequence) != len(unicode_rows):
        raise RuntimeError("Unicode metadata contains duplicate normalized sequences.")

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="twemoji-build-") as temp_name:
        temp = Path(temp_name)
        archive_path = temp / "twemoji.tar.gz"
        staged_assets = temp / "assets"
        staged_assets.mkdir()
        download(ARCHIVE_URL, archive_path)

        archive_digest = sha256_file(archive_path)
        if archive_digest != ARCHIVE_SHA256:
            raise RuntimeError(
                f"Twemoji archive checksum changed: expected {ARCHIVE_SHA256}, got {archive_digest}"
            )

        svg_prefix = f"{ARCHIVE_ROOT}/assets/svg/"
        upstream_asset_count = 0
        matched_sequences: set[tuple[str, ...]] = set()
        asset_digests: dict[str, str] = {}
        license_bytes = None

        with tarfile.open(archive_path, mode="r:gz") as archive:
            for member in archive:
                if not member.isfile():
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                if member.name == f"{ARCHIVE_ROOT}/LICENSE-GRAPHICS":
                    license_bytes = extracted.read()
                    continue
                if not member.name.startswith(svg_prefix) or not member.name.endswith(".svg"):
                    continue

                upstream_asset_count += 1
                source_stem = Path(member.name).stem
                sequence = normalized(tuple(source_stem.split("-")))
                row = unicode_by_sequence.get(sequence)
                if row is None:
                    continue
                if sequence in matched_sequences:
                    raise RuntimeError(f"Duplicate Twemoji asset for normalized sequence: {sequence}")

                filename = f"{'-'.join(row['codepoints'])}.svg"
                payload = extracted.read()
                (staged_assets / filename).write_bytes(payload)
                asset_digests[filename] = sha256_bytes(payload)
                matched_sequences.add(sequence)

        if license_bytes is None:
            raise RuntimeError("The pinned Twemoji archive is missing LICENSE-GRAPHICS.")
        if upstream_asset_count != EXPECTED_UPSTREAM_ASSET_COUNT:
            raise RuntimeError(
                f"Expected {EXPECTED_UPSTREAM_ASSET_COUNT:,} upstream SVGs, "
                f"found {upstream_asset_count:,}."
            )

        missing = set(unicode_by_sequence) - matched_sequences
        if missing:
            examples = ["-".join(sequence) for sequence in sorted(missing)[:5]]
            raise RuntimeError(f"Twemoji is missing Unicode catalog sequences: {examples}")

        items = []
        for row in unicode_rows:
            codepoints = row["codepoints"]
            slug = "-".join(codepoints)
            items.append(
                {
                    "id": f"twemoji:{slug}",
                    "collection": "twemoji",
                    "kind": "image",
                    "name": row["name"],
                    "src": f"./assets/twemoji/{slug}.svg",
                    "emoji": row["emoji"],
                    "keywords": row.get("keywords", []),
                    "group": row.get("group", "Other"),
                    "subgroup": row.get("subgroup", ""),
                    "codepoints": codepoints,
                    "version": row.get("version", ""),
                    "skinTone": row.get("skinTone", False),
                }
            )

        if len(items) != EXPECTED_CATALOG_COUNT or len(asset_digests) != len(items):
            raise RuntimeError(
                f"Expected {EXPECTED_CATALOG_COUNT:,} Twemoji items, "
                f"built {len(items):,} catalog rows and {len(asset_digests):,} SVGs."
            )
        if len({item["id"] for item in items}) != len(items):
            raise RuntimeError("Twemoji catalog contains duplicate IDs.")

        catalog_bytes = (
            json.dumps(items, ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        if ASSETS.exists():
            shutil.rmtree(ASSETS)
        shutil.move(staged_assets, ASSETS)
        CATALOG_PATH.write_bytes(catalog_bytes)
        LICENSE_PATH.write_bytes(license_bytes)

        manifest = {
            "collection": "twemoji",
            "name": "Twemoji",
            "version": VERSION,
            "commit": COMMIT,
            "unicodeVersion": "17.0",
            "sourceUrl": "https://github.com/jdecked/twemoji",
            "archiveUrl": ARCHIVE_URL,
            "archiveSha256": archive_digest,
            "style": "color SVG",
            "license": "CC-BY-4.0",
            "licenseFile": LICENSE_PATH.name,
            "catalog": f"../{CATALOG_PATH.name}",
            "catalogSha256": sha256_bytes(catalog_bytes),
            "assets": "../../assets/twemoji/*.svg",
            "assetCount": len(asset_digests),
            "assetsSha256": asset_digest(asset_digests),
            "upstreamAssetCount": upstream_asset_count,
            "skippedNonCatalogAssets": upstream_asset_count - len(asset_digests),
            "attribution": "Twemoji graphics licensed under CC BY 4.0",
        }
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    total_size = sum(path.stat().st_size for path in ASSETS.glob("*.svg"))
    print(f"Built {len(items):,} Twemoji SVGs ({total_size / 1024 / 1024:.1f} MiB).")


if __name__ == "__main__":
    main()
