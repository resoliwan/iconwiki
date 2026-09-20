"""Build Material Design Icons from a pinned official npm package."""

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
ASSETS = ROOT / "assets" / "material-design-icons"

VERSION = "7.4.47"
PACKAGE_URL = f"https://registry.npmjs.org/@mdi/svg/-/svg-{VERSION}.tgz"
PACKAGE_SHA256 = "de92e5dc9ce46c392ab5c53aa7190b19f82b40cb48872a083f788c7e13e91fef"
UPSTREAM_URL = "https://pictogrammers.com/library/mdi/"


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "local-icon-library/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def member_bytes(archive: tarfile.TarFile, name: str) -> bytes:
    source = archive.extractfile(archive.getmember(name))
    if source is None:
        raise RuntimeError(f"Could not read {name}")
    return source.read()


def main() -> None:
    package_bytes = download(PACKAGE_URL)
    actual_sha256 = hashlib.sha256(package_bytes).hexdigest()
    if actual_sha256 != PACKAGE_SHA256:
        raise RuntimeError(
            f"MDI package checksum mismatch: expected {PACKAGE_SHA256}, got {actual_sha256}"
        )

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=BytesIO(package_bytes), mode="r:gz") as archive:
        metadata = json.loads(member_bytes(archive, "package/meta.json"))
        license_bytes = member_bytes(archive, "package/LICENSE")
        with tempfile.TemporaryDirectory(prefix="mdi-build-", dir=ASSETS.parent) as temp_name:
            staged = Path(temp_name) / "material-design-icons"
            staged.mkdir()
            icons: list[dict[str, object]] = []
            for row in metadata:
                slug = row["name"]
                filename = f"{slug}.svg"
                (staged / filename).write_bytes(
                    member_bytes(archive, f"package/svg/{filename}")
                )
                tags = row.get("tags", [])
                aliases = row.get("aliases", [])
                name = slug.replace("-", " ")
                icons.append(
                    {
                        "id": f"material-design-icons:{slug}",
                        "collection": "material-design-icons",
                        "kind": "image",
                        "name": name,
                        "src": f"./assets/material-design-icons/{filename}",
                        "keywords": sorted(
                            {name, *slug.split("-"), *aliases, *row.get("styles", [])},
                            key=str.casefold,
                        ),
                        "group": tags[0] if tags else "Other",
                        "categories": tags,
                        "aliases": aliases,
                        "codepoints": [row["codepoint"]],
                        "introduced": row.get("version", ""),
                        "author": row.get("author", ""),
                        "deprecated": row.get("deprecated", False),
                    }
                )

            if len(icons) != 7_447:
                raise RuntimeError(f"Unexpected Material Design Icons count: {len(icons)}")
            if len({item["id"] for item in icons}) != len(icons):
                raise RuntimeError("Duplicate Material Design Icon IDs were generated.")
            if ASSETS.exists():
                shutil.rmtree(ASSETS)
            staged.replace(ASSETS)

    catalog_path = DATA / "material-design-icons.json"
    catalog_path.write_text(
        json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    (SOURCES / "MATERIAL-DESIGN-ICONS-LICENSE.txt").write_bytes(license_bytes)
    manifest = {
        "name": "Material Design Icons",
        "version": VERSION,
        "package": "@mdi/svg",
        "packageUrl": PACKAGE_URL,
        "packageSha256": actual_sha256,
        "upstreamUrl": UPSTREAM_URL,
        "assetCount": len(icons),
        "catalog": "../material-design-icons.json",
        "license": "Apache-2.0",
        "licenseFile": "MATERIAL-DESIGN-ICONS-LICENSE.txt",
    }
    (SOURCES / "material-design-icons-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built {len(icons):,} Material Design Icons v{VERSION} SVGs.")


if __name__ == "__main__":
    main()
