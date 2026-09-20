"""Build the local Bootstrap Icons SVG catalog from a pinned official release."""

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
ASSETS = ROOT / "assets" / "bootstrap-icons"

VERSION = "1.13.1"
ARCHIVE_URL = (
    f"https://codeload.github.com/twbs/icons/tar.gz/refs/tags/v{VERSION}"
)
ARCHIVE_SHA256 = "1d83797ae4553ac02cb3fb27b1adb7d0839b56f3918985a4d62f205419d5377e"
ARCHIVE_ROOT = f"icons-{VERSION}"
SVG_PREFIX = f"{ARCHIVE_ROOT}/icons/"
CODEPOINTS_PATH = f"{ARCHIVE_ROOT}/font/bootstrap-icons.json"
LICENSE_PATH = f"{ARCHIVE_ROOT}/LICENSE"
EXPECTED_COUNT = 2_078
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
            "Bootstrap Icons archive checksum mismatch: "
            f"expected {ARCHIVE_SHA256}, got {archive_sha256}"
        )

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    icons: list[dict[str, object]] = []
    with tarfile.open(fileobj=BytesIO(archive_bytes), mode="r:gz") as archive:
        codepoints = json.loads(member_bytes(archive, CODEPOINTS_PATH))
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
            raise RuntimeError(
                f"Unexpected Bootstrap Icons count: {len(members)}"
            )

        with tempfile.TemporaryDirectory(dir=ASSETS.parent) as temporary:
            staging = Path(temporary) / "bootstrap-icons"
            staging.mkdir()

            for member in members:
                filename = member.name[len(SVG_PREFIX) :]
                slug = filename.removesuffix(".svg")
                svg_bytes = member_bytes(archive, member.name)
                (staging / filename).write_bytes(svg_bytes)

                words = slug.split("-")
                is_fill = words[-1] == "fill"
                style = "fill" if is_fill else "outline"
                display_name = slug.replace("-", " ")
                codepoint = codepoints.get(slug)
                if not isinstance(codepoint, int):
                    raise RuntimeError(f"Missing Bootstrap codepoint: {slug}")

                icons.append(
                    {
                        "id": f"bootstrap-icons:{slug}",
                        "collection": "bootstrap-icons",
                        "kind": "image",
                        "name": display_name,
                        "keywords": sorted(
                            {display_name, *words, "bootstrap", style},
                            key=str.casefold,
                        ),
                        "group": style.title(),
                        "variant": style,
                        "unicode": f"{codepoint:X}",
                        "src": f"./assets/bootstrap-icons/{filename}",
                    }
                )

            if ASSETS.exists():
                shutil.rmtree(ASSETS)
            staging.replace(ASSETS)

        license_bytes = member_bytes(archive, LICENSE_PATH)

    ids = [str(icon["id"]) for icon in icons]
    sources = [str(icon["src"]) for icon in icons]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate Bootstrap Icons IDs were generated.")
    if len(sources) != len(set(sources)):
        raise RuntimeError("Duplicate Bootstrap Icons asset paths were generated.")
    if any(not (ROOT / source.removeprefix("./")).is_file() for source in sources):
        raise RuntimeError("A Bootstrap Icons catalog asset is missing.")

    catalog_bytes = (
        json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    (DATA / "bootstrap-icons.json").write_bytes(catalog_bytes)
    (SOURCES / "BOOTSTRAP-ICONS-LICENSE.txt").write_bytes(license_bytes)
    (SOURCES / "bootstrap-icons-manifest.json").write_text(
        json.dumps(
            {
                "name": "Bootstrap Icons",
                "version": VERSION,
                "archiveUrl": ARCHIVE_URL,
                "upstreamUrl": "https://github.com/twbs/icons",
                "archiveSha256": archive_sha256,
                "assetCount": len(icons),
                "catalog": "../bootstrap-icons.json",
                "catalogSha256": sha256(catalog_bytes),
                "assets": "../../assets/bootstrap-icons/*.svg",
                "license": "MIT",
                "licenseFile": "BOOTSTRAP-ICONS-LICENSE.txt",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Built {len(icons):,} Bootstrap Icons v{VERSION} SVGs.")


if __name__ == "__main__":
    main()
