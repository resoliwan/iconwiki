"""Build the free Pixelarticons SVG catalog from a pinned official package."""

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
ASSETS = ROOT / "assets" / "pixelarticons"

VERSION = "2.4.1"
PACKAGE_URL = (
    f"https://registry.npmjs.org/pixelarticons/-/pixelarticons-{VERSION}.tgz"
)
PACKAGE_SHA256 = "d18e8944e6479beb425bbcdc7f4df699b0841a92e6ce02d01eb433821be3435f"
UPSTREAM_URL = "https://github.com/halfmage/pixelarticons"
SVG_PREFIX = "package/svg/"
LICENSE_PATH = "package/LICENSE"
EXPECTED_COUNT = 1_036
EXPECTED_STYLE_COUNTS = {"regular": 651, "sharp": 332, "solid": 53}
USER_AGENT = "iconwiki/1.0"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def member_bytes(archive: tarfile.TarFile, name: str) -> bytes:
    member = archive.getmember(name)
    if not member.isfile():
        raise RuntimeError(f"Expected a regular archive member: {name}")
    source = archive.extractfile(member)
    if source is None:
        raise RuntimeError(f"Could not read archive member: {name}")
    return source.read()


def icon_style(slug: str) -> str:
    if slug.endswith("-sharp"):
        return "sharp"
    if slug.endswith("-solid"):
        return "solid"
    return "regular"


def main() -> None:
    package_bytes = fetch(PACKAGE_URL)
    package_sha256 = sha256(package_bytes)
    if package_sha256 != PACKAGE_SHA256:
        raise RuntimeError(
            "Pixelarticons package checksum mismatch: "
            f"expected {PACKAGE_SHA256}, got {package_sha256}"
        )

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    icons: list[dict[str, object]] = []
    style_counts = {style: 0 for style in EXPECTED_STYLE_COUNTS}

    with tarfile.open(fileobj=BytesIO(package_bytes), mode="r:gz") as archive:
        package = json.loads(member_bytes(archive, "package/package.json"))
        if (
            package.get("name") != "pixelarticons"
            or package.get("version") != VERSION
            or package.get("license") != "MIT"
        ):
            raise RuntimeError("Unexpected Pixelarticons package metadata.")

        members = sorted(
            (
                member
                for member in archive.getmembers()
                if member.isfile()
                and member.name.startswith(SVG_PREFIX)
                and member.name.endswith(".svg")
                and "/" not in member.name[len(SVG_PREFIX) :]
            ),
            key=lambda member: member.name,
        )
        if len(members) != EXPECTED_COUNT:
            raise RuntimeError(f"Unexpected Pixelarticons count: {len(members)}")

        with tempfile.TemporaryDirectory(dir=ASSETS.parent) as temporary:
            staging = Path(temporary) / "pixelarticons"
            staging.mkdir()

            for member in members:
                filename = member.name[len(SVG_PREFIX) :]
                if not re.fullmatch(r"[a-z0-9-]+\.svg", filename):
                    raise RuntimeError(f"Unexpected Pixelarticons filename: {filename}")

                slug = filename.removesuffix(".svg")
                style = icon_style(slug)
                svg_bytes = member_bytes(archive, member.name)
                svg_text = svg_bytes.decode("utf-8")
                if (
                    'viewBox="0 0 24 24"' not in svg_text
                    or 'fill="currentColor"' not in svg_text
                ):
                    raise RuntimeError(f"Unexpected Pixelarticons SVG: {member.name}")
                (staging / filename).write_bytes(svg_bytes)

                display_name = slug.replace("-", " ")
                icons.append(
                    {
                        "id": f"pixelarticons:{slug}",
                        "collection": "pixelarticons",
                        "kind": "image",
                        "name": display_name,
                        "src": f"./assets/pixelarticons/{filename}",
                        "keywords": sorted(
                            {display_name, *slug.split("-"), "pixel", "pixelarticons", style},
                            key=str.casefold,
                        ),
                        "group": style.title(),
                        "variant": style,
                        "size": 24,
                        "viewBox": "0 0 24 24",
                    }
                )
                style_counts[style] += 1

            if ASSETS.exists():
                shutil.rmtree(ASSETS)
            staging.replace(ASSETS)

        license_bytes = member_bytes(archive, LICENSE_PATH)

    if style_counts != EXPECTED_STYLE_COUNTS:
        raise RuntimeError(f"Unexpected Pixelarticons style counts: {style_counts}")

    ids = [str(icon["id"]) for icon in icons]
    sources = [str(icon["src"]) for icon in icons]
    if len(ids) != len(set(ids)) or len(sources) != len(set(sources)):
        raise RuntimeError("Pixelarticons IDs and asset paths must be unique.")
    if any(not (ROOT / source.removeprefix("./")).is_file() for source in sources):
        raise RuntimeError("A Pixelarticons catalog asset is missing.")

    catalog_bytes = (
        json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    (DATA / "pixelarticons.json").write_bytes(catalog_bytes)
    (SOURCES / "PIXELARTICONS-LICENSE.txt").write_bytes(license_bytes)
    (SOURCES / "pixelarticons-manifest.json").write_text(
        json.dumps(
            {
                "name": "Pixelarticons",
                "version": VERSION,
                "package": "pixelarticons",
                "packageUrl": PACKAGE_URL,
                "packageSha256": package_sha256,
                "upstreamUrl": UPSTREAM_URL,
                "styles": list(EXPECTED_STYLE_COUNTS),
                "styleCounts": style_counts,
                "assetCount": len(icons),
                "catalog": "../pixelarticons.json",
                "catalogSha256": sha256(catalog_bytes),
                "assets": "../../assets/pixelarticons/*.svg",
                "license": "MIT",
                "licenseFile": "PIXELARTICONS-LICENSE.txt",
                "scope": "Free SVGs shipped in the official npm package; Pro upgrade assets are excluded.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Built {len(icons):,} free Pixelarticons v{VERSION} SVGs.")


if __name__ == "__main__":
    main()
