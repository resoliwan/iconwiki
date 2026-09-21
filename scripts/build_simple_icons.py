"""Build a local Simple Icons SVG catalog from a pinned official package."""

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
ASSETS = ROOT / "assets" / "simple-icons"

VERSION = "16.32.0"
PACKAGE_URL = f"https://registry.npmjs.org/simple-icons/-/simple-icons-{VERSION}.tgz"
PACKAGE_SHA256 = "df6676b2dca83e8807d60ef3a55b50c86b289cb98e4252c55d977d032e8b0c85"
UPSTREAM_URL = "https://github.com/simple-icons/simple-icons"
PACKAGE_PATH = "package/package.json"
METADATA_PATH = "package/data/simple-icons.json"
LICENSE_PATH = "package/LICENSE.md"
SVG_PREFIX = "package/icons/"
EXPECTED_COUNT = 3_461
GIT_COMMIT = "3173436c1255ab7cdc9c38ab85ca0fca333688d9"
USER_AGENT = "iconwiki/1.0"


def download(url: str) -> bytes:
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


def alias_terms(aliases: dict[str, object]) -> set[str]:
    terms: set[str] = set()
    for alias_type in ("aka", "old"):
        values = aliases.get(alias_type, [])
        if isinstance(values, list):
            terms.update(value for value in values if isinstance(value, str))

    localized = aliases.get("loc", {})
    if isinstance(localized, dict):
        terms.update(value for value in localized.values() if isinstance(value, str))

    duplicates = aliases.get("dup", [])
    if isinstance(duplicates, list):
        for duplicate in duplicates:
            if isinstance(duplicate, dict) and isinstance(duplicate.get("title"), str):
                terms.add(duplicate["title"])
    return terms


def keyword_terms(title: str, slug: str, aliases: dict[str, object]) -> list[str]:
    phrases = {title, slug, "brand", "logo", "simple icons", *alias_terms(aliases)}
    words = {
        word
        for phrase in phrases
        for word in re.findall(r"[^\W_]+", phrase, flags=re.UNICODE)
    }
    return sorted(phrases | words, key=lambda value: (value.casefold(), value))


def main() -> None:
    package_bytes = download(PACKAGE_URL)
    actual_sha256 = sha256(package_bytes)
    if actual_sha256 != PACKAGE_SHA256:
        raise RuntimeError(
            "Simple Icons package checksum mismatch: "
            f"expected {PACKAGE_SHA256}, got {actual_sha256}"
        )

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    icons: list[dict[str, object]] = []
    with tarfile.open(fileobj=BytesIO(package_bytes), mode="r:gz") as archive:
        package = json.loads(member_bytes(archive, PACKAGE_PATH))
        metadata_items = json.loads(member_bytes(archive, METADATA_PATH))
        if package.get("name") != "simple-icons":
            raise RuntimeError("The downloaded package is not Simple Icons.")
        if package.get("version") != VERSION:
            raise RuntimeError(
                f"Unexpected Simple Icons package version: {package.get('version')}"
            )
        if package.get("license") != "CC0-1.0":
            raise RuntimeError(
                f"Unexpected Simple Icons package license: {package.get('license')}"
            )
        if not isinstance(metadata_items, list):
            raise RuntimeError("Simple Icons metadata is not a list.")

        svg_members = {
            Path(member.name).stem: member.name
            for member in archive.getmembers()
            if member.isfile()
            and member.name.startswith(SVG_PREFIX)
            and member.name.endswith(".svg")
            and "/" not in member.name[len(SVG_PREFIX) :]
        }
        metadata_by_slug = {item["slug"]: item for item in metadata_items}
        if len(metadata_by_slug) != len(metadata_items):
            raise RuntimeError("Simple Icons metadata contains duplicate slugs.")
        if set(metadata_by_slug) != set(svg_members):
            missing_assets = sorted(set(metadata_by_slug) - set(svg_members))
            missing_metadata = sorted(set(svg_members) - set(metadata_by_slug))
            raise RuntimeError(
                "Simple Icons metadata and SVG files differ: "
                f"missing assets={missing_assets[:5]}, "
                f"missing metadata={missing_metadata[:5]}"
            )
        if len(svg_members) != EXPECTED_COUNT:
            raise RuntimeError(
                f"Unexpected Simple Icons count: {len(svg_members)}"
            )

        with tempfile.TemporaryDirectory(dir=ASSETS.parent) as temporary:
            staging = Path(temporary) / "simple-icons"
            staging.mkdir()

            for slug, metadata in sorted(metadata_by_slug.items()):
                if not re.fullmatch(r"[a-z0-9_]+", slug):
                    raise RuntimeError(f"Unsafe Simple Icons slug: {slug}")
                title = metadata.get("title")
                color = metadata.get("hex")
                source_url = metadata.get("source")
                if not isinstance(title, str) or not title:
                    raise RuntimeError(f"Missing Simple Icons title: {slug}")
                if not isinstance(color, str) or not re.fullmatch(r"[0-9A-F]{6}", color):
                    raise RuntimeError(f"Invalid Simple Icons brand color: {slug}")
                if not isinstance(source_url, str) or not source_url.startswith("https://"):
                    raise RuntimeError(f"Invalid Simple Icons source URL: {slug}")

                filename = f"{slug}.svg"
                svg_bytes = member_bytes(archive, svg_members[slug])
                svg_text = svg_bytes.decode("utf-8")
                if 'viewBox="0 0 24 24"' not in svg_text:
                    raise RuntimeError(f"Unexpected Simple Icons viewBox: {slug}")
                (staging / filename).write_bytes(svg_bytes)

                aliases = metadata.get("aliases", {})
                if not isinstance(aliases, dict):
                    raise RuntimeError(f"Invalid Simple Icons aliases: {slug}")
                icon: dict[str, object] = {
                    "id": f"simple-icons:{slug}",
                    "collection": "simple-icons",
                    "kind": "image",
                    "name": title,
                    "src": f"./assets/simple-icons/{filename}",
                    "keywords": keyword_terms(title, slug, aliases),
                    "group": "Brands",
                    "variant": "brand",
                    "licenseClass": "restricted",
                    "viewBox": "0 0 24 24",
                    "brandColor": f"#{color}",
                    "sourceUrl": source_url,
                }
                if aliases:
                    icon["aliases"] = aliases
                if "guidelines" in metadata:
                    icon["guidelinesUrl"] = metadata["guidelines"]
                if "license" in metadata:
                    icon["iconLicense"] = metadata["license"]
                icons.append(icon)

            if ASSETS.exists():
                shutil.rmtree(ASSETS)
            staging.replace(ASSETS)

        license_bytes = member_bytes(archive, LICENSE_PATH)

    ids = [str(icon["id"]) for icon in icons]
    sources = [str(icon["src"]) for icon in icons]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate Simple Icons IDs were generated.")
    if len(sources) != len(set(sources)):
        raise RuntimeError("Duplicate Simple Icons asset paths were generated.")
    if any(not (ROOT / source.removeprefix("./")).is_file() for source in sources):
        raise RuntimeError("A Simple Icons catalog asset is missing.")

    catalog_bytes = (
        json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    (DATA / "simple-icons.json").write_bytes(catalog_bytes)
    (SOURCES / "SIMPLE-ICONS-LICENSE.txt").write_bytes(license_bytes)
    manifest = {
        "name": "Simple Icons",
        "version": VERSION,
        "package": "simple-icons",
        "packageUrl": PACKAGE_URL,
        "packageSha256": actual_sha256,
        "gitCommit": GIT_COMMIT,
        "upstreamUrl": UPSTREAM_URL,
        "assetCount": len(icons),
        "catalog": "../simple-icons.json",
        "catalogSha256": sha256(catalog_bytes),
        "assets": "../../assets/simple-icons/*.svg",
        "license": "CC0-1.0",
        "licenseFile": "SIMPLE-ICONS-LICENSE.txt",
        "trademarkNotice": (
            "CC0 covers the Simple Icons project, but individual brand icons may be "
            "protected by separate licenses or trademarks; review per-icon metadata "
            "and brand guidelines before use."
        ),
        "disclaimerUrl": f"{UPSTREAM_URL}/blob/{GIT_COMMIT}/DISCLAIMER.md",
    }
    (SOURCES / "simple-icons-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built {len(icons):,} Simple Icons v{VERSION} brand SVGs.")


if __name__ == "__main__":
    main()
