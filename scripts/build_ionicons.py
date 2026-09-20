"""Build the local Ionicons SVG catalog from a pinned official npm release."""

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
SOURCES = DATA / "sources"
ASSETS = ROOT / "assets" / "ionicons"

VERSION = "8.1.0"
PACKAGE_URL = f"https://registry.npmjs.org/ionicons/-/ionicons-{VERSION}.tgz"
PACKAGE_SHA256 = "6ec604a301f9bb1a59ccc72a746cbb369bae87c5b45f6c67904dc878d9efb8b5"
UPSTREAM_URL = "https://github.com/ionic-team/ionicons"
SVG_PREFIX = "package/dist/svg/"
METADATA_PATH = "package/dist/ionicons.json"
PACKAGE_PATH = "package/package.json"
LICENSE_PATH = "package/LICENSE"
USER_AGENT = "moa-icon-catalog/1.0"


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


def split_variant(slug: str) -> tuple[str, str]:
    for suffix in ("-outline", "-sharp"):
        if slug.endswith(suffix):
            return slug.removesuffix(suffix), suffix.removeprefix("-")
    return slug, "filled"


def main() -> None:
    package_bytes = download(PACKAGE_URL)
    actual_sha256 = sha256(package_bytes)
    if actual_sha256 != PACKAGE_SHA256:
        raise RuntimeError(
            "Ionicons package checksum mismatch: "
            f"expected {PACKAGE_SHA256}, got {actual_sha256}"
        )

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    icons: list[dict[str, object]] = []
    style_counts = {"filled": 0, "outline": 0, "sharp": 0}

    with tarfile.open(fileobj=io.BytesIO(package_bytes), mode="r:gz") as archive:
        package_metadata = json.loads(member_bytes(archive, PACKAGE_PATH))
        icon_metadata = json.loads(member_bytes(archive, METADATA_PATH))
        if package_metadata.get("name") != "ionicons":
            raise RuntimeError("The downloaded package is not Ionicons.")
        if package_metadata.get("version") != VERSION:
            raise RuntimeError(
                f"Unexpected Ionicons package version: {package_metadata.get('version')}"
            )
        if package_metadata.get("license") != "MIT":
            raise RuntimeError(
                f"Unexpected Ionicons license: {package_metadata.get('license')}"
            )
        if icon_metadata.get("version") != VERSION:
            raise RuntimeError(
                f"Unexpected Ionicons metadata version: {icon_metadata.get('version')}"
            )

        svg_members = {
            Path(member.name).stem: member.name
            for member in archive.getmembers()
            if member.isfile()
            and member.name.startswith(SVG_PREFIX)
            and member.name.endswith(".svg")
            and "/" not in member.name[len(SVG_PREFIX) :]
        }
        metadata_items = icon_metadata.get("icons", [])
        metadata_names = {item["name"] for item in metadata_items}
        if metadata_names != set(svg_members):
            missing_assets = sorted(metadata_names - set(svg_members))
            missing_metadata = sorted(set(svg_members) - metadata_names)
            raise RuntimeError(
                "Ionicons metadata and SVG files differ: "
                f"missing assets={missing_assets[:5]}, "
                f"missing metadata={missing_metadata[:5]}"
            )
        if len(svg_members) != 1_357:
            raise RuntimeError(f"Unexpected Ionicons icon count: {len(svg_members)}")

        with tempfile.TemporaryDirectory(dir=ASSETS.parent) as temporary:
            staging = Path(temporary) / "ionicons"
            for style in style_counts:
                (staging / style).mkdir(parents=True)

            for metadata in sorted(metadata_items, key=lambda item: item["name"]):
                slug = metadata["name"]
                base_slug, style = split_variant(slug)
                filename = f"{slug}.svg"
                asset_path = staging / style / filename
                asset_path.write_bytes(member_bytes(archive, svg_members[slug]))

                base_name = base_slug.replace("-", " ")
                display_name = f"{base_name} ({style})"
                keywords = sorted(
                    {
                        base_name,
                        slug.replace("-", " "),
                        *base_slug.split("-"),
                        *metadata.get("tags", []),
                        style,
                    },
                    key=str.casefold,
                )
                icons.append(
                    {
                        "id": f"ionicons:{slug}",
                        "collection": "ionicons",
                        "kind": "image",
                        "name": display_name,
                        "keywords": keywords,
                        "group": style.title(),
                        "variant": style,
                        "licenseClass": "restricted" if base_slug.startswith("logo-") else "permissive",
                        "style": style,
                        "viewBox": "0 0 512 512",
                        "src": f"./assets/ionicons/{style}/{filename}",
                    }
                )
                style_counts[style] += 1

            if ASSETS.exists():
                shutil.rmtree(ASSETS)
            staging.replace(ASSETS)

        license_bytes = member_bytes(archive, LICENSE_PATH)

    ids = [str(icon["id"]) for icon in icons]
    sources = [str(icon["src"]) for icon in icons]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate Ionicons IDs were generated.")
    if len(sources) != len(set(sources)):
        raise RuntimeError("Duplicate Ionicons asset paths were generated.")
    if any(not (ROOT / source.removeprefix("./")).is_file() for source in sources):
        raise RuntimeError("An Ionicons catalog asset is missing.")
    if style_counts != {"filled": 515, "outline": 421, "sharp": 421}:
        raise RuntimeError(f"Unexpected Ionicons style counts: {style_counts}")

    catalog_bytes = (
        json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    (DATA / "ionicons.json").write_bytes(catalog_bytes)
    (SOURCES / "IONICONS-LICENSE.txt").write_bytes(license_bytes)
    manifest = {
        "name": "Ionicons",
        "version": VERSION,
        "packageUrl": PACKAGE_URL,
        "upstreamUrl": UPSTREAM_URL,
        "sha256": actual_sha256,
        "gitCommit": package_metadata.get("gitHead", "7f482f9492a1726e8c25af397d7ceccf23f58591"),
        "styles": list(style_counts),
        "styleCounts": style_counts,
        "assetCount": len(icons),
        "catalog": "../ionicons.json",
        "catalogSha256": sha256(catalog_bytes),
        "assets": "../../assets/ionicons/*/*.svg",
        "license": "MIT",
        "licenseFile": "IONICONS-LICENSE.txt",
    }
    (SOURCES / "ionicons-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Built {len(icons):,} Ionicons v{VERSION} SVGs "
        f"({style_counts['filled']:,} filled, "
        f"{style_counts['outline']:,} outline, "
        f"{style_counts['sharp']:,} sharp)."
    )


if __name__ == "__main__":
    main()
