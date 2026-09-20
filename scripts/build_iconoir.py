"""Build a local Iconoir SVG catalog from a pinned official package."""

from __future__ import annotations

from io import BytesIO
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
ASSETS = ROOT / "assets" / "iconoir"

VERSION = "7.12.1"
PACKAGE_URL = f"https://registry.npmjs.org/iconoir/-/iconoir-{VERSION}.tgz"
PACKAGE_SHA256 = "6a8ccf0c36a718c319238820d3af5dc25b3524e91f8d6df16c5c65c728b6124e"
UPSTREAM_URL = "https://github.com/iconoir-icons/iconoir"
STYLES = ("regular", "solid")
EXPECTED_COUNTS = {"regular": 1_383, "solid": 288}
USER_AGENT = "moa-icon-catalog/1.0"


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def archive_member_bytes(archive: tarfile.TarFile, name: str) -> bytes:
    member = archive.getmember(name)
    source = archive.extractfile(member)
    if source is None:
        raise RuntimeError(f"Could not read {name}")
    return source.read()


def main() -> None:
    package_bytes = download(PACKAGE_URL)
    package_sha256 = sha256(package_bytes)
    if package_sha256 != PACKAGE_SHA256:
        raise RuntimeError(
            f"Iconoir package checksum mismatch: expected {PACKAGE_SHA256}, "
            f"got {package_sha256}"
        )

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    icons: list[dict[str, object]] = []
    style_counts = {style: 0 for style in STYLES}

    with tarfile.open(fileobj=BytesIO(package_bytes), mode="r:gz") as archive:
        package = json.loads(archive_member_bytes(archive, "package/package.json"))
        if package.get("version") != VERSION or package.get("license") != "MIT":
            raise RuntimeError("Unexpected Iconoir package metadata.")
        license_bytes = archive_member_bytes(archive, "package/LICENSE")

        with tempfile.TemporaryDirectory(dir=ASSETS.parent) as temporary:
            staging = Path(temporary) / "iconoir"
            for style in STYLES:
                prefix = f"package/icons/{style}/"
                style_dir = staging / style
                style_dir.mkdir(parents=True)
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
                for member in members:
                    filename = Path(member.name).name
                    slug = filename.removesuffix(".svg")
                    svg_bytes = archive_member_bytes(archive, member.name)
                    svg_text = svg_bytes.decode("utf-8")
                    if 'viewBox="0 0 24 24"' not in svg_text:
                        raise RuntimeError(f"Unexpected Iconoir viewBox: {member.name}")
                    (style_dir / filename).write_bytes(svg_bytes)

                    display_name = slug.replace("-", " ")
                    icons.append(
                        {
                            "id": f"iconoir:{slug}:{style}",
                            "collection": "iconoir",
                            "kind": "image",
                            "name": f"{display_name} ({style})",
                            "src": f"./assets/iconoir/{style}/{filename}",
                            "keywords": sorted(
                                {display_name, *slug.split("-"), style, "iconoir"},
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

    if style_counts != EXPECTED_COUNTS:
        raise RuntimeError(f"Unexpected Iconoir asset counts: {style_counts}")
    ids = [str(icon["id"]) for icon in icons]
    sources = [str(icon["src"]) for icon in icons]
    if len(ids) != len(set(ids)) or len(sources) != len(set(sources)):
        raise RuntimeError("Iconoir IDs and asset paths must be unique.")
    if any(not (ROOT / source.removeprefix("./")).is_file() for source in sources):
        raise RuntimeError("An Iconoir catalog asset is missing.")

    catalog_bytes = (
        json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    (DATA / "iconoir.json").write_bytes(catalog_bytes)
    (SOURCES / "ICONOIR-LICENSE.txt").write_bytes(license_bytes)
    (SOURCES / "iconoir-manifest.json").write_text(
        json.dumps(
            {
                "name": "Iconoir",
                "version": VERSION,
                "package": "iconoir",
                "packageUrl": PACKAGE_URL,
                "packageSha256": package_sha256,
                "upstreamUrl": UPSTREAM_URL,
                "styles": list(STYLES),
                "styleCounts": style_counts,
                "assetCount": len(icons),
                "catalog": "../iconoir.json",
                "catalogSha256": sha256(catalog_bytes),
                "assets": "../../assets/iconoir/*/*.svg",
                "license": "MIT",
                "licenseFile": "ICONOIR-LICENSE.txt",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Built {len(icons):,} Iconoir SVG variants from iconoir {VERSION}.")


if __name__ == "__main__":
    main()
