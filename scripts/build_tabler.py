"""Build the pinned Tabler Icons outline SVG collection for the static browser."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import tarfile
import tempfile
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE = DATA / "sources"
ASSETS = ROOT / "assets" / "tabler"

VERSION = "3.47.0"
COMMIT = "c940317930743839f3ba8dd02ebdbba930fb8be5"
ARCHIVE_URL = f"https://codeload.github.com/tabler/tabler-icons/tar.gz/refs/tags/v{VERSION}"
ARCHIVE_SHA256 = "4fbbd791f93c252fa80372ac8a789617e56b101bab6b4b2f2fbeeb0e88d63eaa"
ARCHIVE_ROOT = f"tabler-icons-{VERSION}"
SVG_PREFIX = f"{ARCHIVE_ROOT}/icons/outline/"
LICENSE_PATH = f"{ARCHIVE_ROOT}/LICENSE"
USER_AGENT = "simpledic-icon-catalog/1.0"


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
    extracted = archive.extractfile(member)
    if extracted is None:
        raise RuntimeError(f"Could not read archive member: {name}")
    return extracted.read()


def metadata(svg: str, filename: str) -> tuple[list[str], str, str, str]:
    comment = re.match(r"\s*<!--(.*?)-->", svg, re.DOTALL)
    if not comment:
        raise RuntimeError(f"Missing Tabler metadata comment: {filename}")

    def value(key: str) -> str:
        match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", comment.group(1))
        if not match:
            raise RuntimeError(f"Missing Tabler {key} metadata: {filename}")
        return match.group(1).strip().strip('"')

    raw_tags = value("tags")
    if not raw_tags.startswith("[") or not raw_tags.endswith("]"):
        raise RuntimeError(f"Unexpected Tabler tags metadata: {filename}")
    tags = [tag.strip() for tag in raw_tags[1:-1].split(",") if tag.strip()]
    return tags, value("category"), value("version"), value("unicode")


def main() -> None:
    archive_bytes = fetch(ARCHIVE_URL)
    actual_sha256 = sha256(archive_bytes)
    if actual_sha256 != ARCHIVE_SHA256:
        raise RuntimeError(
            f"Tabler archive checksum mismatch: expected {ARCHIVE_SHA256}, got {actual_sha256}"
        )

    SOURCE.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    icons: list[dict[str, object]] = []
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
        members = sorted(
            [
            member
            for member in archive.getmembers()
            if member.isfile()
            and member.name.startswith(SVG_PREFIX)
            and member.name.endswith(".svg")
            and "/" not in member.name[len(SVG_PREFIX) :]
            ],
            key=lambda member: member.name,
        )
        if len(members) != 5_148:
            raise RuntimeError(f"Unexpected Tabler outline icon count: {len(members)}")

        with tempfile.TemporaryDirectory(dir=ASSETS.parent) as temporary:
            staging = Path(temporary) / "tabler"
            staging.mkdir()
            for member in members:
                filename = member.name[len(SVG_PREFIX) :]
                slug = filename.removesuffix(".svg")
                svg_bytes = member_bytes(archive, member.name)
                svg_text = svg_bytes.decode("utf-8")
                tags, category, introduced, codepoint = metadata(svg_text, filename)
                (staging / filename).write_bytes(svg_bytes)
                icons.append(
                    {
                        "id": f"tabler:{slug}",
                        "collection": "tabler",
                        "kind": "image",
                        "name": slug.replace("-", " "),
                        "src": f"./assets/tabler/{filename}",
                        "keywords": sorted({slug.replace("-", " "), *tags}, key=str.casefold),
                        "group": category,
                        "categories": [category],
                        "style": "outline",
                        "introduced": introduced,
                        "codepoints": [codepoint.upper()],
                    }
                )

            if ASSETS.exists():
                shutil.rmtree(ASSETS)
            staging.replace(ASSETS)

        license_bytes = member_bytes(archive, LICENSE_PATH)

    ids = [item["id"] for item in icons]
    sources = [item["src"] for item in icons]
    if len(ids) != len(set(ids)) or len(sources) != len(set(sources)):
        raise RuntimeError("Tabler IDs and asset paths must be unique.")
    if any(not (ROOT / str(source).removeprefix("./")).is_file() for source in sources):
        raise RuntimeError("A Tabler catalog asset is missing.")

    catalog_bytes = (
        json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    (DATA / "tabler.json").write_bytes(catalog_bytes)
    (SOURCE / "TABLER-LICENSE.txt").write_bytes(license_bytes)
    manifest = {
        "collection": "tabler",
        "version": VERSION,
        "ref": f"v{VERSION}",
        "commit": COMMIT,
        "sourceUrl": "https://github.com/tabler/tabler-icons",
        "archiveUrl": ARCHIVE_URL,
        "archiveSha256": actual_sha256,
        "style": "outline",
        "count": len(icons),
        "catalog": "../tabler.json",
        "catalogSha256": sha256(catalog_bytes),
        "assets": "../../assets/tabler/*.svg",
        "license": "TABLER-LICENSE.txt",
    }
    (SOURCE / "tabler-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built {len(icons):,} Tabler Icons v{VERSION} outline SVGs.")


if __name__ == "__main__":
    main()
