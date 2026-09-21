"""Build the local Heroicons SVG catalog from a pinned official release."""

from __future__ import annotations

from io import BytesIO
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = DATA / "sources"
ASSETS = ROOT / "assets" / "heroicons"

VERSION = "2.2.0"
ARCHIVE_URL = f"https://github.com/tailwindlabs/heroicons/archive/refs/tags/v{VERSION}.tar.gz"
ARCHIVE_SHA256 = "42bd31001127631a20270e7bd87ac13647bfcd628dd533e2ff31497068b4f7af"
UPSTREAM_URL = "https://github.com/tailwindlabs/heroicons"
SIZE = 24
STYLES = ("outline", "solid")
USER_AGENT = "iconwiki/1.0"


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


archive_bytes = download(ARCHIVE_URL)
archive_sha256 = hashlib.sha256(archive_bytes).hexdigest()
if archive_sha256 != ARCHIVE_SHA256:
    raise RuntimeError(
        f"Heroicons archive checksum mismatch: expected {ARCHIVE_SHA256}, got {archive_sha256}"
    )

if ASSETS.exists():
    shutil.rmtree(ASSETS)
ASSETS.mkdir(parents=True)
SOURCES.mkdir(parents=True, exist_ok=True)

icons = []
style_counts = {style: 0 for style in STYLES}
license_bytes = None
archive_root = f"heroicons-{VERSION}"

with tarfile.open(fileobj=BytesIO(archive_bytes), mode="r:gz") as archive:
    license_member = archive.getmember(f"{archive_root}/LICENSE")
    license_file = archive.extractfile(license_member)
    if license_file is None:
        raise RuntimeError("The Heroicons release did not include its license.")
    license_bytes = license_file.read()

    for style in STYLES:
        prefix = f"{archive_root}/optimized/{SIZE}/{style}/"
        members = sorted(
            (
                member
                for member in archive.getmembers()
                if member.isfile()
                and member.name.startswith(prefix)
                and member.name.endswith(".svg")
            ),
            key=lambda member: member.name,
        )
        style_dir = ASSETS / style
        style_dir.mkdir()

        for member in members:
            filename = Path(member.name).name
            slug = filename.removesuffix(".svg")
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError(f"Could not read {member.name}")
            svg_bytes = source.read()
            (style_dir / filename).write_bytes(svg_bytes)

            display_name = slug.replace("-", " ")
            icons.append(
                {
                    "id": f"heroicons:{slug}:{style}",
                    "collection": "heroicons",
                    "kind": "image",
                    "name": f"{display_name} ({style})",
                    "keywords": sorted({display_name, *slug.split("-"), style}),
                    "group": style.title(),
                    "variant": style,
                    "size": SIZE,
                    "viewBox": f"0 0 {SIZE} {SIZE}",
                    "src": f"./assets/heroicons/{style}/{filename}",
                }
            )
            style_counts[style] += 1

if not license_bytes:
    raise RuntimeError("The Heroicons license was empty.")
if min(style_counts.values()) < 300:
    raise RuntimeError(f"Unexpected Heroicons asset counts: {style_counts}")
if len({icon["id"] for icon in icons}) != len(icons):
    raise RuntimeError("Duplicate Heroicons IDs were generated.")

(DATA / "heroicons.json").write_text(
    json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n",
    encoding="utf-8",
)
(SOURCES / "HEROICONS-LICENSE.txt").write_bytes(license_bytes)
(SOURCES / "heroicons-manifest.json").write_text(
    json.dumps(
        {
            "name": "Heroicons",
            "version": VERSION,
            "archiveUrl": ARCHIVE_URL,
            "upstreamUrl": UPSTREAM_URL,
            "sha256": archive_sha256,
            "canonicalSize": SIZE,
            "styles": list(STYLES),
            "styleCounts": style_counts,
            "assetCount": len(icons),
            "license": "MIT",
            "licenseFile": "HEROICONS-LICENSE.txt",
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

print(f"Built {len(icons):,} Heroicons SVG variants from v{VERSION}.")
