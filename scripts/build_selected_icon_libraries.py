"""Build six selected icon collections from pinned Iconify JSON packages."""

from __future__ import annotations

import argparse
from html import escape
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import tarfile
import tempfile

from build_recommended_icon_libraries import digest, download, iconify_source, member_bytes, words


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = DATA / "sources"

LIBRARIES = {
    "keyline-icons": {
        "name": "Keyline Icons", "group": "UI", "upstream": "https://github.com/keyline-icons/keyline-icons",
        "sources": [iconify_source("@iconify-json/keyline-icons", "1.2.10", "0090b2a27b696e98b507c14f253cce6735ee65bbfbae8850630900fc17847a5e", 9736)],
        "license": "MIT", "license_file": "KEYLINE-ICONS-LICENSE.txt",
        "license_url": "https://raw.githubusercontent.com/keyline-icons/keyline-icons/73d757b13d2ef78f85cdd8fdcb5c58555cb3940d/LICENSE",
        "license_sha256": "c9eaf07fee7f7eed72daec177408132b0a48eca8db0c831e1f7bf28e3b1ccefc",
        "styles": [("-sharp-two-tone", "sharp two-tone"), ("-sharp-duotone", "sharp duotone"),
                   ("-sharp-fill", "sharp fill"), ("-two-tone", "two-tone"),
                   ("-duotone", "duotone"), ("-sharp", "sharp stroke"), ("-fill", "fill")],
        "default_style": "stroke",
        "note": "Rounded and sharp SVGs in stroke, two-tone, duotone, and fill styles, normalized by Iconify.",
    },
    "tdesign-icons": {
        "name": "TDesign Icons", "group": "UI", "upstream": "https://github.com/Tencent/tdesign-icons",
        "sources": [iconify_source("@iconify-json/tdesign", "1.2.19", "af53c40f637023517d6a65f609c844d74ad33362b221de971e9579e252a3b8cb", 2356)],
        "license": "MIT", "license_file": "TDESIGN-ICONS-LICENSE.txt",
        "license_url": "https://raw.githubusercontent.com/Tencent/tdesign-icons/cdd47ea37dc6a7a06fb59d21d5482852e7beb50b/LICENSE",
        "license_sha256": "b3dbcb89dcf4a11abf1b70d043795a3da0c458af16fefd2ff315d9ff5875312f",
        "styles": [("-filled", "filled")], "default_style": "outline",
        "note": "TDesign outline and filled SVGs normalized by Iconify.",
    },
    "flowbite-icons": {
        "name": "Flowbite Icons", "group": "UI", "upstream": "https://github.com/themesberg/flowbite-icons",
        "sources": [iconify_source("@iconify-json/flowbite", "1.2.7", "dff96194210b9f62a1270a991de8f1c4030887ea9d6df90b25dc0365f0f87c88", 751)],
        "license": "MIT", "license_file": "FLOWBITE-ICONS-LICENSE.txt",
        "license_url": "https://raw.githubusercontent.com/themesberg/flowbite-icons/4f85985690fdd553e029f7415d90d32142bb5452/LICENSE",
        "license_sha256": "b3282d91fbf0ac51c848c7f18fc82b67a1ffbcfaada35af81cfa0fd8966101d3",
        "styles": [("-outline", "outline"), ("-solid", "solid")],
        "note": "Flowbite outline and solid SVGs normalized by Iconify.",
    },
    "coreui-icons-free": {
        "name": "CoreUI Icons Free", "group": "UI", "upstream": "https://github.com/coreui/coreui-icons",
        "sources": [
            {**iconify_source("@iconify-json/cil", "1.2.3", "4b15665dd0b5fc53981b99f54d3cdbb27afe50f54c41e734458b3c49788a34a9", 554, "linear"), "license": "CC-BY-4.0"},
            {**iconify_source("@iconify-json/cib", "1.2.3", "0d6efc2ec141f4b23422134a59a092a2e7e9f1fc7ecb08b81986159a5b868ac4", 830, "brands"), "license": "CC0-1.0"},
            {**iconify_source("@iconify-json/cif", "1.2.7", "804801450b77e3b2c9a2b716fb45b44ee2a97e702e21ac6bca6358d0f7eb13c8", 199, "flags"), "license": "CC0-1.0"},
        ],
        "license": "CC-BY-4.0 / CC0-1.0", "license_file": "COREUI-ICONS-FREE-LICENSE.txt",
        "license_url": "https://raw.githubusercontent.com/coreui/coreui-icons/88d1cfc47fc3cc84114de2a01b04db11a941bdf9/LICENSE",
        "license_sha256": "171b668bd4fa31e5b75141d30290e5ab9eefcc881027ef24d0bd9e91aea8689b",
        "note": "CoreUI linear SVGs are CC BY 4.0; brand and flag SVGs are CC0 1.0 and may involve trademarks.",
    },
    "akar-icons": {
        "name": "Akar Icons", "group": "UI", "upstream": "https://github.com/artcoholic/akar-icons",
        "sources": [iconify_source("@iconify-json/akar-icons", "1.2.7", "21d871932fc182074cd206b88d6b40cbeffa45d17fdf800fc3bc81358e8ff8c0", 454)],
        "license": "MIT", "license_file": "AKAR-ICONS-LICENSE.txt",
        "license_url": "https://raw.githubusercontent.com/artcoholic/akar-icons/a88023a51bfc3cb86c3bbb3db8fce39b1a58729b/LICENSE",
        "license_sha256": "87500dbc60dd758dc91c72927a647ed4fdb162effc6dbc2073a2c9f51ba695c0",
        "note": "Rounded Akar SVG artwork normalized by Iconify.",
    },
    "proicons": {
        "name": "ProIcons", "group": "UI", "upstream": "https://github.com/ProCode-Software/proicons",
        "sources": [iconify_source("@iconify-json/proicons", "1.2.20", "951dc0fd780704fd098deadc4c880d31392619d4f0c2ec49b3758a856f2dab2e", 544)],
        "license": "MIT", "license_file": "PROICONS-LICENSE.txt",
        "license_url": "https://raw.githubusercontent.com/ProCode-Software/proicons/b8718fbc0a8654f6065cff8b3166ee3b99cd89ca/LICENSE",
        "license_sha256": "1668412af87d0d966a578e84560f392a1a3a60a01d47bc08c022b8f074e0efb6",
        "note": "ProIcons SVG artwork normalized by Iconify.",
    },
}


def style_for(config: dict, source: dict, slug: str) -> tuple[str, str]:
    if source.get("variant"):
        return source["variant"], slug
    for suffix, style in config.get("styles", []):
        if slug.endswith(suffix):
            return style, slug.removesuffix(suffix)
    return config.get("default_style", "default"), slug


def build(library_id: str) -> None:
    config = LIBRARIES[library_id]
    flag_lookup = {}
    if library_id == "coreui-icons-free":
        for flag in json.loads((DATA / "flag-icons.json").read_text()):
            if flag["variant"] == "1x1":
                flag_lookup[flag["id"].rsplit("/", 1)[-1]] = flag
    packages = []
    for source in config["sources"]:
        archive_bytes = download(source["url"])
        if digest(archive_bytes) != source["sha256"]:
            raise RuntimeError(f"Package checksum mismatch: {source['package']}")
        with tarfile.open(fileobj=BytesIO(archive_bytes), mode="r:gz") as archive:
            package = json.loads(member_bytes(archive, "package/package.json"))
            icon_set = json.loads(member_bytes(archive, "package/icons.json"))
            info = json.loads(member_bytes(archive, "package/info.json"))
        if (package.get("name"), package.get("version")) != (source["package"], source["version"]):
            raise RuntimeError(f"Package identity mismatch: {source['package']}")
        expected_license = source.get("license", config["license"])
        if info.get("license", {}).get("spdx") != expected_license:
            raise RuntimeError(f"License mismatch: {source['package']}")
        icons = {slug: icon for slug, icon in icon_set["icons"].items() if not icon.get("hidden")}
        if len(icons) != source["expected"]:
            raise RuntimeError(f"Icon count mismatch: {source['package']}: {len(icons)}")
        packages.append((source, icon_set, icons))

    license_bytes = download(config["license_url"])
    if digest(license_bytes) != config["license_sha256"]:
        raise RuntimeError(f"License checksum mismatch: {library_id}")

    catalog = []
    assets = ROOT / "assets" / library_id
    with tempfile.TemporaryDirectory(dir=assets.parent) as temporary:
        staging = Path(temporary) / library_id
        for source, icon_set, icons in packages:
            for slug, icon in sorted(icons.items()):
                if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
                    raise RuntimeError(f"Unsafe icon name: {slug}")
                style, base_slug = style_for(config, source, slug)
                style_id = re.sub(r"[^a-z0-9]+", "-", style.casefold()).strip("-")
                relative = Path(style_id) / f"{slug}.svg"
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                left = icon.get("left", icon_set.get("left", 0))
                top = icon.get("top", icon_set.get("top", 0))
                width = icon.get("width", icon_set.get("width", 16))
                height = icon.get("height", icon_set.get("height", 16))
                view_box = f"{left} {top} {width} {height}"
                target.write_text(
                    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{escape(view_box)}" color="#000">{icon["body"]}</svg>\n'
                )
                base_name = base_slug.replace("-", " ")
                license_name = source.get("license", config["license"])
                group = "Flags" if library_id == "coreui-icons-free" and style == "flags" else (
                    "Brands" if library_id == "coreui-icons-free" and style == "brands" else config["group"]
                )
                flag = flag_lookup.get(slug) if style == "flags" else None
                if flag:
                    base_name = flag["name"].split(" flag (", 1)[0] + " flag"
                display_name = f"{base_name} (CoreUI)" if flag else (
                    base_name if style == "default" else f"{base_name} ({style})"
                )
                item = {
                    "id": f"{library_id}:{style_id}/{slug}", "collection": library_id,
                    "kind": "image", "name": display_name,
                    "src": f"./assets/{library_id}/{relative.as_posix()}",
                    "keywords": words(base_name, slug, style, config["name"], group, *(flag["keywords"] if flag else [])),
                    "group": group, "variant": style, "viewBox": view_box,
                }
                if re.search(r'(?:fill|stroke)="#[0-9a-fA-F]{3,8}', str(icon["body"])):
                    item["colored"] = True
                if library_id == "coreui-icons-free":
                    item["license"] = license_name
                    item["licenseClass"] = "restricted" if style in ("brands", "flags") else "attribution"
                    if style == "linear":
                        item["attribution"] = "CoreUI Icons Free, licensed under CC BY 4.0"
                catalog.append(item)
        if assets.exists():
            shutil.rmtree(assets)
        staging.replace(assets)

    expected_total = sum(source["expected"] for source in config["sources"])
    if len(catalog) != expected_total or len({item["id"] for item in catalog}) != expected_total:
        raise RuntimeError(f"Catalog count or ID mismatch: {library_id}")
    SOURCES.mkdir(parents=True, exist_ok=True)
    (SOURCES / config["license_file"]).write_bytes(license_bytes)
    catalog_bytes = (json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    (DATA / f"{library_id}.json").write_bytes(catalog_bytes)
    manifest = {
        "name": config["name"], "version": config["sources"][0]["version"],
        "packages": [{"name": source["package"], "version": source["version"], "url": source["url"],
                      "sha256": source["sha256"], "assetCount": source["expected"],
                      "license": source.get("license", config["license"])} for source in config["sources"]],
        "upstreamUrl": config["upstream"], "assetCount": len(catalog),
        "catalog": f"../{library_id}.json", "catalogSha256": digest(catalog_bytes),
        "assets": f"../../assets/{library_id}/**/*.svg", "license": config["license"],
        "licenseFile": config["license_file"], "licenseUrl": config["license_url"],
        "licenseSha256": config["license_sha256"],
    }
    (SOURCES / f"{library_id}-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Built {len(catalog):,} {config['name']} SVGs")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("libraries", nargs="*", choices=sorted(LIBRARIES))
    args = parser.parse_args()
    for library_id in args.libraries or LIBRARIES:
        build(library_id)


if __name__ == "__main__":
    main()
