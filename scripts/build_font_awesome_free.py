"""Build the local Font Awesome Free SVG catalog from a pinned official release."""

from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = DATA / "sources"
ASSETS = ROOT / "assets" / "font-awesome-free"

VERSION = "7.3.1"
ARCHIVE_URL = (
    f"https://codeload.github.com/FortAwesome/Font-Awesome/tar.gz/refs/tags/{VERSION}"
)
ARCHIVE_SHA256 = "d5a20554faa1ad30148b05f090a556e23495c446435c8dfc1624d3c0e3c2640b"
ARCHIVE_ROOT = f"Font-Awesome-{VERSION}"
PACKAGE_ROOT = (
    f"{ARCHIVE_ROOT}/js-packages/@fortawesome/fontawesome-free"
)
METADATA_PATH = f"{ARCHIVE_ROOT}/metadata/icons.json"
LICENSE_PATH = f"{ARCHIVE_ROOT}/LICENSE.txt"
STYLES = ("brands", "regular", "solid")
EXPECTED_STYLE_COUNTS = {"brands": 609, "regular": 273, "solid": 2_001}
USER_AGENT = "moa-icon-catalog/1.0"


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


def main() -> None:
    archive_bytes = fetch(ARCHIVE_URL)
    archive_sha256 = sha256(archive_bytes)
    if archive_sha256 != ARCHIVE_SHA256:
        raise RuntimeError(
            "Font Awesome archive checksum mismatch: "
            f"expected {ARCHIVE_SHA256}, got {archive_sha256}"
        )

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    icons: list[dict[str, object]] = []
    style_counts: dict[str, int] = {}

    with tarfile.open(fileobj=BytesIO(archive_bytes), mode="r:gz") as archive:
        metadata = json.loads(member_bytes(archive, METADATA_PATH))

        with tempfile.TemporaryDirectory(dir=ASSETS.parent) as temporary:
            staging = Path(temporary) / "font-awesome-free"
            staging.mkdir()

            for style in STYLES:
                prefix = f"{PACKAGE_ROOT}/svgs/{style}/"
                members = sorted(
                    (
                        member
                        for member in archive.getmembers()
                        if member.isfile()
                        and member.name.startswith(prefix)
                        and member.name.endswith(".svg")
                        and "/" not in member.name[len(prefix) :]
                    ),
                    key=lambda member: member.name,
                )
                style_counts[style] = len(members)
                style_dir = staging / style
                style_dir.mkdir()

                for member in members:
                    filename = member.name[len(prefix) :]
                    slug = filename.removesuffix(".svg")
                    details = metadata.get(slug)
                    if not isinstance(details, dict):
                        details = {}

                    svg_bytes = member_bytes(archive, member.name)
                    (style_dir / filename).write_bytes(svg_bytes)

                    label = str(details.get("label") or slug.replace("-", " "))
                    search = details.get("search") or {}
                    aliases = details.get("aliases") or {}
                    terms = search.get("terms") or []
                    alias_names = aliases.get("names") or []
                    keywords = {
                        slug.replace("-", " "),
                        *slug.split("-"),
                        label,
                        style,
                        *(str(term) for term in terms),
                        *(str(alias) for alias in alias_names),
                    }

                    icons.append(
                        {
                            "id": f"font-awesome-free:{slug}:{style}",
                            "collection": "font-awesome-free",
                            "kind": "image",
                            "name": f"{label} ({style})",
                            "keywords": sorted(keywords, key=str.casefold),
                            "group": style.title(),
                            "variant": style,
                            "licenseClass": "restricted" if style == "brands" else "attribution",
                            "unicode": str(details.get("unicode") or "").upper(),
                            "src": f"./assets/font-awesome-free/{style}/{filename}",
                        }
                    )

            if style_counts != EXPECTED_STYLE_COUNTS:
                raise RuntimeError(
                    "Unexpected Font Awesome SVG counts: "
                    f"expected {EXPECTED_STYLE_COUNTS}, got {style_counts}"
                )

            if ASSETS.exists():
                shutil.rmtree(ASSETS)
            staging.replace(ASSETS)

        license_bytes = member_bytes(archive, LICENSE_PATH)

    ids = [str(icon["id"]) for icon in icons]
    sources = [str(icon["src"]) for icon in icons]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate Font Awesome IDs were generated.")
    if len(sources) != len(set(sources)):
        raise RuntimeError("Duplicate Font Awesome asset paths were generated.")
    if any(not (ROOT / source.removeprefix("./")).is_file() for source in sources):
        raise RuntimeError("A Font Awesome catalog asset is missing.")

    catalog_bytes = (
        json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    (DATA / "font-awesome-free.json").write_bytes(catalog_bytes)
    (SOURCES / "FONT-AWESOME-FREE-LICENSE.txt").write_bytes(license_bytes)
    (SOURCES / "font-awesome-free-manifest.json").write_text(
        json.dumps(
            {
                "name": "Font Awesome Free",
                "version": VERSION,
                "archiveUrl": ARCHIVE_URL,
                "upstreamUrl": "https://github.com/FortAwesome/Font-Awesome",
                "archiveSha256": archive_sha256,
                "styles": list(STYLES),
                "styleCounts": style_counts,
                "assetCount": len(icons),
                "catalog": "../font-awesome-free.json",
                "catalogSha256": sha256(catalog_bytes),
                "assets": "../../assets/font-awesome-free/*/*.svg",
                "license": "CC-BY-4.0",
                "licenseFile": "FONT-AWESOME-FREE-LICENSE.txt",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Built {len(icons):,} Font Awesome Free v{VERSION} SVG variants "
        f"({style_counts})."
    )


if __name__ == "__main__":
    main()
