"""Build a local Fluent UI System Icons catalog from a pinned official package."""

from __future__ import annotations

from io import BytesIO
import hashlib
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
ASSETS = ROOT / "assets" / "fluent-system-icons"

VERSION = "1.1.341"
GIT_HEAD = "2e4da95009de778ae0f41ec6c17bc67c97f4dc56"
PACKAGE_URL = (
    "https://registry.npmjs.org/@fluentui/svg-icons/-/"
    f"svg-icons-{VERSION}.tgz"
)
PACKAGE_SHA256 = "262ee509b6d1464ae4bcd3318ffbf9ecede78984b3fc05804e4bd025aed90b14"
LICENSE_URL = (
    "https://raw.githubusercontent.com/microsoft/fluentui-system-icons/"
    f"{GIT_HEAD}/LICENSE"
)
LICENSE_SHA256 = "69bc45dc42b9acb96a69823adbc6ae538374e3c0bde169b855b32c48eaaef52f"
UPSTREAM_URL = "https://github.com/microsoft/fluentui-system-icons"
SIZE = 24
STYLES = ("regular", "filled", "color")
EXPECTED_COUNTS = {"regular": 2_618, "filled": 2_654, "color": 196}
ICON_PATTERN = re.compile(
    rf"^package/icons/(?P<slug>.+)_{SIZE}_(?P<style>{'|'.join(STYLES)})\.svg$"
)
USER_AGENT = "iconwiki/1.0"


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def archive_member_bytes(archive: tarfile.TarFile, member: tarfile.TarInfo) -> bytes:
    source = archive.extractfile(member)
    if source is None:
        raise RuntimeError(f"Could not read {member.name}")
    return source.read()


def main() -> None:
    package_bytes = download(PACKAGE_URL)
    package_sha256 = sha256(package_bytes)
    if package_sha256 != PACKAGE_SHA256:
        raise RuntimeError(
            "Fluent UI package checksum mismatch: "
            f"expected {PACKAGE_SHA256}, got {package_sha256}"
        )

    license_bytes = download(LICENSE_URL)
    license_sha256 = sha256(license_bytes)
    if license_sha256 != LICENSE_SHA256:
        raise RuntimeError(
            "Fluent UI license checksum mismatch: "
            f"expected {LICENSE_SHA256}, got {license_sha256}"
        )

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    icons: list[dict[str, object]] = []
    style_counts = {style: 0 for style in STYLES}

    with tarfile.open(fileobj=BytesIO(package_bytes), mode="r:gz") as archive:
        package = json.load(archive.extractfile("package/package.json"))
        if package.get("version") != VERSION or package.get("license") != "MIT":
            raise RuntimeError("Unexpected Fluent UI package metadata.")

        members: list[tuple[tarfile.TarInfo, re.Match[str]]] = []
        for member in archive.getmembers():
            if not member.isfile():
                continue
            match = ICON_PATTERN.match(member.name)
            if match:
                members.append((member, match))
        members.sort(key=lambda pair: pair[0].name)

        with tempfile.TemporaryDirectory(dir=ASSETS.parent) as temporary:
            staging = Path(temporary) / "fluent-system-icons"
            for style in STYLES:
                (staging / style).mkdir(parents=True)

            for member, match in members:
                source_slug = match.group("slug")
                style = match.group("style")
                slug = source_slug.replace("/", "-").replace("_", "-").lower()
                filename = f"{slug}.svg"
                svg_bytes = archive_member_bytes(archive, member)
                svg_text = svg_bytes.decode("utf-8")
                view_box_match = re.search(r'viewBox="([^"]+)"', svg_text)
                if not view_box_match or not view_box_match.group(1).startswith("0 0 "):
                    raise RuntimeError(f"Unexpected Fluent UI viewBox: {member.name}")
                view_box = view_box_match.group(1)
                (staging / style / filename).write_bytes(svg_bytes)

                display_name = slug.replace("-", " ")
                icons.append(
                    {
                        "id": f"fluent-system-icons:{slug}:{style}",
                        "collection": "fluent-system-icons",
                        "kind": "image",
                        "name": f"{display_name} ({style})",
                        "src": f"./assets/fluent-system-icons/{style}/{filename}",
                        "keywords": sorted(
                            {
                                display_name,
                                *slug.split("-"),
                                style,
                                "fluent",
                                "microsoft",
                            },
                            key=str.casefold,
                        ),
                        "group": style.title(),
                        "variant": style,
                        "size": SIZE,
                        "viewBox": view_box,
                    }
                )
                style_counts[style] += 1

            if ASSETS.exists():
                shutil.rmtree(ASSETS)
            staging.replace(ASSETS)

    if style_counts != EXPECTED_COUNTS:
        raise RuntimeError(f"Unexpected Fluent UI asset counts: {style_counts}")
    ids = [str(icon["id"]) for icon in icons]
    sources = [str(icon["src"]) for icon in icons]
    if len(ids) != len(set(ids)) or len(sources) != len(set(sources)):
        raise RuntimeError("Fluent UI IDs and asset paths must be unique.")
    if any(not (ROOT / source.removeprefix("./")).is_file() for source in sources):
        raise RuntimeError("A Fluent UI catalog asset is missing.")

    catalog_bytes = (
        json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    (DATA / "fluent-system-icons.json").write_bytes(catalog_bytes)
    (SOURCES / "FLUENT-SYSTEM-ICONS-LICENSE.txt").write_bytes(license_bytes)
    (SOURCES / "fluent-system-icons-manifest.json").write_text(
        json.dumps(
            {
                "name": "Microsoft Fluent UI System Icons",
                "version": VERSION,
                "package": "@fluentui/svg-icons",
                "packageUrl": PACKAGE_URL,
                "packageSha256": package_sha256,
                "gitHead": GIT_HEAD,
                "upstreamUrl": UPSTREAM_URL,
                "canonicalSize": SIZE,
                "styles": list(STYLES),
                "styleCounts": style_counts,
                "assetCount": len(icons),
                "catalog": "../fluent-system-icons.json",
                "catalogSha256": sha256(catalog_bytes),
                "assets": "../../assets/fluent-system-icons/*/*.svg",
                "license": "MIT",
                "licenseUrl": LICENSE_URL,
                "licenseSha256": license_sha256,
                "licenseFile": "FLUENT-SYSTEM-ICONS-LICENSE.txt",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Built {len(icons):,} Microsoft Fluent UI System Icons "
        f"from @fluentui/svg-icons {VERSION}."
    )


if __name__ == "__main__":
    main()
