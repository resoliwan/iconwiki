"""Build the pinned Lucide default outline SVG collection for the static browser."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE = DATA / "sources"
ASSETS = ROOT / "assets" / "lucide"

VERSION = "0.577.0"
COMMIT = "0ea8780434e2b4527dc860b18ff94883d080b59c"
ARCHIVE_URL = f"https://codeload.github.com/lucide-icons/lucide/tar.gz/refs/tags/{VERSION}"
ARCHIVE_SHA256 = "358bbe07eceafdabf53ffdb3f229bf1aabab55665dd8338b69a6e8139f539625"
ARCHIVE_ROOT = f"lucide-{VERSION}"
ICON_PREFIX = f"{ARCHIVE_ROOT}/icons/"
CATEGORY_PREFIX = f"{ARCHIVE_ROOT}/categories/"
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


def main() -> None:
    archive_bytes = fetch(ARCHIVE_URL)
    actual_sha256 = sha256(archive_bytes)
    if actual_sha256 != ARCHIVE_SHA256:
        raise RuntimeError(
            f"Lucide archive checksum mismatch: expected {ARCHIVE_SHA256}, got {actual_sha256}"
        )

    SOURCE.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    icons: list[dict[str, object]] = []
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
        category_titles: dict[str, str] = {}
        for member in archive.getmembers():
            if (
                member.isfile()
                and member.name.startswith(CATEGORY_PREFIX)
                and member.name.endswith(".json")
                and "/" not in member.name[len(CATEGORY_PREFIX) :]
            ):
                slug = Path(member.name).stem
                category = json.loads(member_bytes(archive, member.name))
                category_titles[slug] = category["title"]

        svg_members = sorted(
            [
            member
            for member in archive.getmembers()
            if member.isfile()
            and member.name.startswith(ICON_PREFIX)
            and member.name.endswith(".svg")
            and "/" not in member.name[len(ICON_PREFIX) :]
            ],
            key=lambda member: member.name,
        )
        if len(svg_members) != 1_703:
            raise RuntimeError(f"Unexpected Lucide icon count: {len(svg_members)}")

        with tempfile.TemporaryDirectory(dir=ASSETS.parent) as temporary:
            staging = Path(temporary) / "lucide"
            staging.mkdir()
            for member in svg_members:
                filename = member.name[len(ICON_PREFIX) :]
                slug = filename.removesuffix(".svg")
                metadata_name = f"{ICON_PREFIX}{slug}.json"
                metadata = json.loads(member_bytes(archive, metadata_name))
                category_ids = metadata.get("categories", [])
                categories = [category_titles.get(value, value.replace("-", " ").title()) for value in category_ids]
                aliases = [alias["name"] for alias in metadata.get("aliases", [])]
                keywords = sorted(
                    {slug.replace("-", " "), *metadata.get("tags", []), *aliases},
                    key=str.casefold,
                )
                svg_bytes = member_bytes(archive, member.name)
                (staging / filename).write_bytes(svg_bytes)
                icon: dict[str, object] = {
                    "id": f"lucide:{slug}",
                    "collection": "lucide",
                    "kind": "image",
                    "name": slug.replace("-", " "),
                    "src": f"./assets/lucide/{filename}",
                    "keywords": keywords,
                    "group": categories[0] if categories else "Other",
                    "categories": categories,
                    "style": "outline",
                }
                if aliases:
                    icon["aliases"] = aliases
                if metadata.get("deprecated"):
                    icon["deprecated"] = True
                    icon["deprecationReason"] = metadata.get("deprecationReason", "")
                    icon["toBeRemovedInVersion"] = metadata.get("toBeRemovedInVersion", "")
                icons.append(icon)

            if ASSETS.exists():
                shutil.rmtree(ASSETS)
            staging.replace(ASSETS)

        license_bytes = member_bytes(archive, LICENSE_PATH)

    ids = [item["id"] for item in icons]
    sources = [item["src"] for item in icons]
    if len(ids) != len(set(ids)) or len(sources) != len(set(sources)):
        raise RuntimeError("Lucide IDs and asset paths must be unique.")
    if any(not (ROOT / str(source).removeprefix("./")).is_file() for source in sources):
        raise RuntimeError("A Lucide catalog asset is missing.")

    catalog_bytes = (
        json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    (DATA / "lucide.json").write_bytes(catalog_bytes)
    (SOURCE / "LUCIDE-LICENSE.txt").write_bytes(license_bytes)
    manifest = {
        "collection": "lucide",
        "version": VERSION,
        "ref": VERSION,
        "commit": COMMIT,
        "sourceUrl": "https://github.com/lucide-icons/lucide",
        "archiveUrl": ARCHIVE_URL,
        "archiveSha256": actual_sha256,
        "style": "outline",
        "count": len(icons),
        "catalog": "../lucide.json",
        "catalogSha256": sha256(catalog_bytes),
        "assets": "../../assets/lucide/*.svg",
        "license": "LUCIDE-LICENSE.txt",
    }
    (SOURCE / "lucide-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built {len(icons):,} Lucide v{VERSION} outline SVGs.")


if __name__ == "__main__":
    main()
