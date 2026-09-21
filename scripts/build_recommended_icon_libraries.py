"""Build ten pinned icon libraries from normalized Iconify JSON packages."""

from __future__ import annotations

import argparse
import hashlib
from html import escape
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
USER_AGENT = "iconwiki/1.0"


def iconify_source(package: str, version: str, sha256: str, expected: int, variant: str = "") -> dict[str, object]:
    package_name = package.rsplit("/", 1)[-1]
    return {
        "package": package,
        "version": version,
        "url": f"https://registry.npmjs.org/{package}/-/{package_name}-{version}.tgz",
        "sha256": sha256,
        "expected": expected,
        "variant": variant,
    }


LIBRARIES = {
    "icon-park": {
        "name": "IconPark", "version": "1.2.4", "group": "UI", "license": "Apache-2.0",
        "license_class": "permissive", "license_file": "ICON-PARK-LICENSE.txt",
        "upstream": "https://github.com/bytedance/IconPark",
        "note": "Outline, solid, two-tone, and multi-color SVGs normalized by Iconify from the official IconPark artwork.",
        "sources": [
            iconify_source("@iconify-json/icon-park-outline", "1.2.4", "e4c29776086e46ed7d113b7d44798a36ca74df6dcfb949da142db34714ab7c8a", 2658, "outline"),
            iconify_source("@iconify-json/icon-park-solid", "1.2.4", "3af17a63c120891842d272ec34b4bec414e6c4801af8158a460b4c3cb4dc1248", 1947, "solid"),
            iconify_source("@iconify-json/icon-park-twotone", "1.2.4", "579560dd7c0e1c6f53297129f3a32cdcf4292871e2c5e82e502840c7ce68eabb", 1944, "two-tone"),
            iconify_source("@iconify-json/icon-park", "1.2.4", "c1a25212a31602aca93c3fa6f6b3288e89b9d7811afc132dfd78506e9d586b6f", 2658, "multi-color"),
        ],
        "license_sources": [{
            "file": "ICON-PARK-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/bytedance/IconPark/8dc132da4c85671ba6a5962c87aa2bdafbf158e9/LICENSE",
            "sha256": "81268f00802b1a9cffae4df43f78c3a0809845e03fef3da68f26ad2e4c49681e",
        }],
    },
    "mingcute": {
        "name": "MingCute Icons", "version": "1.2.8", "group": "UI", "license": "Apache-2.0",
        "license_class": "permissive", "license_file": "MINGCUTE-LICENSE.txt",
        "upstream": "https://github.com/mingcute-design/mingcute-icons",
        "note": "Core regular and filled SVGs normalized by Iconify from the official MingCute artwork.",
        "sources": [iconify_source("@iconify-json/mingcute", "1.2.8", "fec65f4430ac70a968e0e7fc7741e7064ba91e6da992b905f75c9d70c717bd2c", 3320)],
        "style_suffixes": [("-fill", "filled"), ("-line", "regular")],
        "license_sources": [{
            "file": "MINGCUTE-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/mingcute-design/mingcute-icons/ca98bb55513a22ff0dab713aaf7870b512944653/LICENSE",
            "sha256": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
        }],
    },
    "carbon-icons": {
        "name": "Carbon Icons", "version": "1.2.27", "group": "Enterprise UI", "license": "Apache-2.0",
        "license_class": "permissive", "license_file": "CARBON-ICONS-LICENSE.txt",
        "upstream": "https://github.com/carbon-design-system/carbon",
        "note": "IBM Carbon Design System SVG icons normalized by Iconify.",
        "sources": [iconify_source("@iconify-json/carbon", "1.2.27", "0ebce2313aabc58901cc4324f0ccccd03009cca0cc03fecd18cc570d9ba23139", 2618)],
        "license_sources": [{
            "file": "CARBON-ICONS-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/carbon-design-system/carbon/8472ccac7c2150ef317617063da6b82058812319/LICENSE",
            "sha256": "037b3e9eaff51477b270e9082f54b99175e4dd893548654f00995045b68294b8",
        }],
    },
    "ant-design-icons": {
        "name": "Ant Design Icons", "version": "1.2.9", "group": "UI", "license": "MIT",
        "license_class": "permissive", "license_file": "ANT-DESIGN-ICONS-LICENSE.txt",
        "upstream": "https://github.com/ant-design/ant-design-icons",
        "note": "Outlined, filled, and two-tone Ant Design SVGs normalized by Iconify.",
        "sources": [iconify_source("@iconify-json/ant-design", "1.2.9", "d6351e677f9e51b7a15cf0702a0c151e5c663ec8a053ebf2aa79743ddf0438e2", 848)],
        "style_suffixes": [("-twotone", "two-tone"), ("-outlined", "outlined"), ("-filled", "filled")],
        "license_sources": [{
            "file": "ANT-DESIGN-ICONS-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/ant-design/ant-design-icons/7f2516ac91226d2b41f93b35cb5197c8d94f7189/LICENSE",
            "sha256": "5d367fb0a07340571542eb4ee8eb1add62d37b71bad6786a57c2e9a86bf76c70",
        }],
    },
    "flat-color-icons": {
        "name": "Flat Color Icons", "version": "1.2.3", "group": "Color", "license": "MIT",
        "license_class": "permissive", "license_file": "FLAT-COLOR-ICONS-LICENSE.md",
        "upstream": "https://github.com/icons8/flat-color-icons",
        "note": "Icons8 flat-color SVG artwork normalized by Iconify.",
        "sources": [iconify_source("@iconify-json/flat-color-icons", "1.2.3", "d8878a9b0f02d749bc8671eb7d47882eb711185cbcefbb365cbfb488773c4786", 329, "color")],
        "license_sources": [{
            "file": "FLAT-COLOR-ICONS-LICENSE.md",
            "url": "https://raw.githubusercontent.com/icons8/flat-color-icons/1bf90d5ff118bc6690120ff9fdfe234565b7e414/LICENSE.md",
            "sha256": "0c029819d69e43042904a3e9d12d25934d08398ba739e4364d61519aa1c2711c",
        }],
    },
    "maki": {
        "name": "Maki", "version": "1.2.5", "group": "Maps & Places", "license": "CC0-1.0",
        "license_class": "permissive", "license_file": "MAKI-LICENSE.txt",
        "upstream": "https://github.com/mapbox/maki",
        "note": "Mapbox point-of-interest SVGs in official pixel-aligned sizes, normalized by Iconify.",
        "sources": [iconify_source("@iconify-json/maki", "1.2.5", "cbf41d1b7262fad2eecdc6425ae5afed2de9b3512093c4c778fb456e788d7e12", 215)],
        "style_suffixes": [("-15", "15 px"), ("-11", "11 px")],
        "license_sources": [{
            "file": "MAKI-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/mapbox/maki/28e2a3602e4bde033a1dd388e86e9c117b425e34/LICENSE.txt",
            "sha256": "36ffd9dc085d529a7e60e1276d73ae5a030b020313e6c5408593a6ae2af39673",
        }],
    },
    "clarity-icons": {
        "name": "Clarity Icons", "version": "1.2.4", "group": "Enterprise UI", "license": "MIT",
        "license_class": "permissive", "license_file": "CLARITY-ICONS-LICENSE.txt",
        "upstream": "https://github.com/vmware/clarity-assets",
        "note": "Clarity Design System line and solid SVG icons normalized by Iconify.",
        "sources": [iconify_source("@iconify-json/clarity", "1.2.4", "6ea2d256f5fc8b4a1778d332533fab81daf4197d3809e2ac8df82ab54fd02f26", 1103)],
        "style_suffixes": [
            ("-outline-alerted", "outline alerted"), ("-outline-badged", "outline badged"),
            ("-solid-alerted", "solid alerted"), ("-solid-badged", "solid badged"),
            ("-solid", "solid"), ("-line", "line"),
        ],
        "license_sources": [{
            "file": "CLARITY-ICONS-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/vmware/clarity-assets/a84864f436294097ede3199e9be7c3fe9d95593e/LICENSE",
            "sha256": "144757b53192e700f7fd7d7de1ef2d2e97f968556d4fbd3e7ca9bfce90a4482e",
        }],
    },
    "eva-icons": {
        "name": "Eva Icons", "version": "1.2.3", "group": "UI", "license": "MIT",
        "license_class": "permissive", "license_file": "EVA-ICONS-LICENSE.txt",
        "upstream": "https://github.com/akveo/eva-icons",
        "note": "Eva outline and filled SVG icons normalized by Iconify.",
        "sources": [iconify_source("@iconify-json/eva", "1.2.3", "728a5f3f5ea238be5ce65ef3306042d188b9eda52d652f8108ab205264696a97", 490)],
        "style_suffixes": [("-outline", "outline"), ("-fill", "filled")],
        "license_sources": [{
            "file": "EVA-ICONS-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/akveo/eva-icons/70d2471ff88ab1385d3310b93a406243377b53d5/LICENSE.txt",
            "sha256": "4788c563f8871931bce41ede59379a5277ac1a473e289f9100924149ce8bd311",
        }],
    },
    "css-gg": {
        "name": "css.gg", "version": "1.2.2", "group": "UI", "license": "MIT",
        "license_class": "permissive", "license_file": "CSS-GG-LICENSE.md",
        "upstream": "https://github.com/astrit/css.gg",
        "note": "css.gg SVG icons normalized by Iconify.",
        "sources": [iconify_source("@iconify-json/gg", "1.2.2", "ee7a061fb05fdadcc7fdcf7b11d6d4aec427a8695f92efd909a0af242028eb44", 704)],
        "license_sources": [{
            "file": "CSS-GG-LICENSE.md",
            "url": "https://raw.githubusercontent.com/astrit/css.gg/ad0428df5491082b29a81d64dbdc59b9602cc059/LICENSE.md",
            "sha256": "901673e29904f76a9735f1430f9ee59867aae09692168d7abf1ba6adf01f8195",
        }],
    },
    "solar-icons": {
        "name": "Solar Icons", "version": "1.2.12", "group": "UI", "license": "CC-BY-4.0",
        "license_class": "attribution", "license_file": "SOLAR-ICONS-LICENSE.txt",
        "upstream": "https://www.figma.com/community/file/1166831539721848736",
        "note": "Solar SVG artwork by 480 Design in six styles, normalized by Iconify. Attribution: Solar Icons by 480 Design (CC BY 4.0).",
        "attribution": "Solar Icons by 480 Design, licensed under CC BY 4.0",
        "sources": [iconify_source("@iconify-json/solar", "1.2.12", "9a9eba8111fa3ae53721fe440d01282fbd3e662d582be721000a61ab8be734e0", 8280)],
        "style_suffixes": [
            ("-bold-duotone", "bold duotone"), ("-line-duotone", "line duotone"),
            ("-linear", "linear"), ("-outline", "outline"), ("-broken", "broken"), ("-bold", "bold"),
        ],
        "license_sources": [
            {
                "file": "SOLAR-ICONS-LICENSE.txt",
                "url": "https://creativecommons.org/licenses/by/4.0/legalcode.txt",
                "sha256": "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411",
            },
            {
                "file": "SOLAR-ICONS-NOTICE.txt",
                "url": "https://raw.githubusercontent.com/saoudi-h/solar-icons/09eac32a6aa2facd7499de59e55e6c2b93bc32fc/LICENSE-THIRD-PARTY",
                "sha256": "055cc14f0eca227d9af49d408e3c5d3407fb688158e123b28f67177e1ec5f7d8",
            },
        ],
    },
}


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def member_bytes(archive: tarfile.TarFile, name: str) -> bytes:
    member = archive.extractfile(archive.getmember(name))
    if member is None:
        raise RuntimeError(f"Could not read {name}")
    return member.read()


def words(*values: object) -> list[str]:
    phrases = {str(value).strip() for value in values if value and str(value).strip()}
    tokens = {token for phrase in phrases for token in re.findall(r"[^\W_]+", phrase, re.UNICODE)}
    return sorted(phrases | tokens, key=lambda value: (value.casefold(), value))


def style_for(config: dict[str, object], source: dict[str, object], slug: str) -> tuple[str, str]:
    if source.get("variant"):
        return str(source["variant"]), slug
    for suffix, label in config.get("style_suffixes", []):
        if slug.endswith(suffix):
            return label, slug.removesuffix(suffix)
    return str(config.get("default_variant", "default")), slug


def svg_bytes(icon: dict[str, object], icon_set: dict[str, object]) -> tuple[bytes, str]:
    left = icon.get("left", icon_set.get("left", 0))
    top = icon.get("top", icon_set.get("top", 0))
    width = icon.get("width", icon_set.get("width", 16))
    height = icon.get("height", icon_set.get("height", 16))
    view_box = f"{left} {top} {width} {height}"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{escape(view_box)}" color="#000">'
        f'{icon["body"]}</svg>\n'
    )
    return svg.encode(), view_box


def build(library_id: str) -> None:
    config = LIBRARIES[library_id]
    packages: list[dict[str, object]] = []
    for source in config["sources"]:
        package_bytes = download(str(source["url"]))
        package_hash = digest(package_bytes)
        if package_hash != source["sha256"]:
            raise RuntimeError(f"{source['package']} checksum mismatch: {package_hash}")
        with tarfile.open(fileobj=BytesIO(package_bytes), mode="r:gz") as archive:
            package = json.loads(member_bytes(archive, "package/package.json"))
            icon_set = json.loads(member_bytes(archive, "package/icons.json"))
            info = json.loads(member_bytes(archive, "package/info.json"))
        if package.get("name") != source["package"] or package.get("version") != source["version"]:
            raise RuntimeError(f"Unexpected package identity for {source['package']}")
        if info.get("license", {}).get("spdx") != config["license"]:
            raise RuntimeError(f"Unexpected icon license for {source['package']}")
        visible = {slug: icon for slug, icon in icon_set["icons"].items() if not icon.get("hidden")}
        if len(visible) != source["expected"]:
            raise RuntimeError(f"Unexpected {source['package']} count: {len(visible)}")
        packages.append({"source": source, "hash": package_hash, "icons": visible, "icon_set": icon_set})

    licenses: list[tuple[dict[str, str], bytes]] = []
    for license_source in config["license_sources"]:
        license_bytes = download(str(license_source["url"]))
        license_hash = digest(license_bytes)
        if license_hash != license_source["sha256"]:
            raise RuntimeError(f"{license_source['file']} checksum mismatch: {license_hash}")
        licenses.append((license_source, license_bytes))

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    assets = ROOT / "assets" / library_id
    assets.parent.mkdir(parents=True, exist_ok=True)
    icons: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(dir=assets.parent) as temporary:
        staging = Path(temporary) / library_id
        for package_data in packages:
            source = package_data["source"]
            icon_set = package_data["icon_set"]
            for slug, icon in sorted(package_data["icons"].items()):
                if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
                    raise RuntimeError(f"Unsafe icon name: {slug}")
                variant, base_slug = style_for(config, source, slug)
                variant_id = re.sub(r"[^a-z0-9]+", "-", variant.casefold()).strip("-") or "default"
                relative = Path(variant_id) / f"{slug}.svg"
                output = staging / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                rendered, view_box = svg_bytes(icon, icon_set)
                output.write_bytes(rendered)
                base_name = base_slug.replace("-", " ")
                display_name = base_name if variant == "default" else f"{base_name} ({variant})"
                item: dict[str, object] = {
                    "id": f"{library_id}:{variant_id}/{slug}",
                    "collection": library_id,
                    "kind": "image",
                    "name": display_name,
                    "src": f"./assets/{library_id}/{relative.as_posix()}",
                    "keywords": words(base_name, slug, variant, config["name"], config["group"]),
                    "group": config["group"],
                    "variant": variant,
                    "viewBox": view_box,
                }
                if config.get("attribution"):
                    item["attribution"] = config["attribution"]
                icons.append(item)

        if assets.exists():
            shutil.rmtree(assets)
        staging.replace(assets)

    ids = [str(icon["id"]) for icon in icons]
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"Duplicate {config['name']} IDs")
    expected_total = sum(int(source["expected"]) for source in config["sources"])
    if len(icons) != expected_total:
        raise RuntimeError(f"Unexpected {config['name']} total: {len(icons)}")

    for license_source, license_bytes in licenses:
        (SOURCES / str(license_source["file"])).write_bytes(license_bytes)
    catalog_bytes = (json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    (DATA / f"{library_id}.json").write_bytes(catalog_bytes)
    manifest = {
        "name": config["name"], "version": config["version"],
        "packages": [
            {
                "name": package_data["source"]["package"],
                "version": package_data["source"]["version"],
                "url": package_data["source"]["url"],
                "sha256": package_data["hash"],
                "assetCount": package_data["source"]["expected"],
            }
            for package_data in packages
        ],
        "upstreamUrl": config["upstream"], "assetCount": len(icons),
        "catalog": f"../{library_id}.json", "catalogSha256": digest(catalog_bytes),
        "assets": f"../../assets/{library_id}/**/*.svg", "license": config["license"],
        "licenseFile": config["license_file"],
        "licenseSources": config["license_sources"],
    }
    (SOURCES / f"{library_id}-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Built {len(icons):,} {config['name']} SVGs.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("libraries", nargs="*", choices=sorted(LIBRARIES))
    args = parser.parse_args()
    for library_id in args.libraries or LIBRARIES:
        build(library_id)


if __name__ == "__main__":
    main()
