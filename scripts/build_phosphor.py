"""Build the local Phosphor SVG catalog from a pinned official package."""

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
ASSETS = ROOT / "assets" / "phosphor"

VERSION = "2.1.1"
PACKAGE_URL = f"https://registry.npmjs.org/@phosphor-icons/core/-/core-{VERSION}.tgz"
PACKAGE_SHA256 = "313332be6190b724da24107addd781799b48bf76b13963f24501112ffe1baadd"
UPSTREAM_URL = "https://github.com/phosphor-icons/core"
STYLES = ("regular", "fill", "thin", "light", "bold", "duotone")
USER_AGENT = "iconwiki/1.0"


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def base_slug(filename: str, style: str) -> str:
    suffix = ".svg" if style == "regular" else f"-{style}.svg"
    if not filename.endswith(suffix):
        raise ValueError(f"Unexpected Phosphor filename: {filename}")
    return filename[: -len(suffix)]


archive_bytes = download(PACKAGE_URL)
archive_sha256 = hashlib.sha256(archive_bytes).hexdigest()
if archive_sha256 != PACKAGE_SHA256:
    raise RuntimeError(
        f"Phosphor package checksum mismatch: expected {PACKAGE_SHA256}, got {archive_sha256}"
    )

if ASSETS.exists():
    shutil.rmtree(ASSETS)
ASSETS.mkdir(parents=True)
SOURCES.mkdir(parents=True, exist_ok=True)

icons = []
style_counts = {style: 0 for style in STYLES}
license_bytes = None

with tarfile.open(fileobj=BytesIO(archive_bytes), mode="r:gz") as archive:
    license_member = archive.getmember("package/LICENSE")
    license_file = archive.extractfile(license_member)
    if license_file is None:
        raise RuntimeError("The Phosphor package did not include its license.")
    license_bytes = license_file.read()

    for style in STYLES:
        prefix = f"package/assets/{style}/"
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
            slug = base_slug(filename, style)
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError(f"Could not read {member.name}")
            svg_bytes = source.read()
            output_name = f"{slug}.svg"
            (style_dir / output_name).write_bytes(svg_bytes)

            display_name = slug.replace("-", " ")
            icons.append(
                {
                    "id": f"phosphor:{slug}:{style}",
                    "collection": "phosphor",
                    "kind": "image",
                    "name": f"{display_name} ({style})",
                    "keywords": sorted({display_name, *slug.split("-"), style}),
                    "group": style.title(),
                    "variant": style,
                    "weight": style,
                    "viewBox": "0 0 256 256",
                    "src": f"./assets/phosphor/{style}/{output_name}",
                }
            )
            style_counts[style] += 1

if not license_bytes:
    raise RuntimeError("The Phosphor license was empty.")
if min(style_counts.values()) < 1_500:
    raise RuntimeError(f"Unexpected Phosphor asset counts: {style_counts}")
if len({icon["id"] for icon in icons}) != len(icons):
    raise RuntimeError("Duplicate Phosphor IDs were generated.")

(DATA / "phosphor.json").write_text(
    json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n",
    encoding="utf-8",
)
(SOURCES / "PHOSPHOR-LICENSE.txt").write_bytes(license_bytes)
(SOURCES / "phosphor-manifest.json").write_text(
    json.dumps(
        {
            "name": "Phosphor Icons",
            "version": VERSION,
            "package": "@phosphor-icons/core",
            "packageUrl": PACKAGE_URL,
            "upstreamUrl": UPSTREAM_URL,
            "sha256": archive_sha256,
            "styles": list(STYLES),
            "styleCounts": style_counts,
            "assetCount": len(icons),
            "license": "MIT",
            "licenseFile": "PHOSPHOR-LICENSE.txt",
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

print(f"Built {len(icons):,} Phosphor SVG variants from @phosphor-icons/core {VERSION}.")
