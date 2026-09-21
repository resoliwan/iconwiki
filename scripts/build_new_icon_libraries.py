"""Build six pinned icon libraries added in the 2026 catalog expansion."""

from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
import tempfile
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = DATA / "sources"
USER_AGENT = "iconwiki/1.0"

LIBRARIES = {
    "health-icons": {
        "name": "Health Icons", "version": "2.0.0", "package": "healthicons",
        "url": "https://registry.npmjs.org/healthicons/-/healthicons-2.0.0.tgz",
        "sha256": "7d29cfc4ffb495319c27b34c9ac96ddc9781c7b3dc3b96eef3d34fe4d3ef9f03",
        "prefix": "package/public/icons/svg/", "expected": 1514,
        "license": "MIT", "license_file": "HEALTH-ICONS-LICENSE.txt",
        "upstream": "https://github.com/resolvetosavelives/healthicons",
    },
    "devicon": {
        "name": "Devicon", "version": "2.17.0", "package": "devicon",
        "url": "https://registry.npmjs.org/devicon/-/devicon-2.17.0.tgz",
        "sha256": "e611f56ef1eeb17c00940f970d44d8ca086439ae7892b496a46b81a7f9a38d5a",
        "prefix": "package/icons/", "expected": 1877,
        "license": "MIT", "license_file": "DEVICON-LICENSE.txt",
        "upstream": "https://github.com/devicons/devicon",
    },
    "flag-icons": {
        "name": "flag-icons", "version": "7.5.0", "package": "flag-icons",
        "url": "https://registry.npmjs.org/flag-icons/-/flag-icons-7.5.0.tgz",
        "sha256": "c0b80bf0e08006a60f56621d6bc49f8c7131f4d1fef6737a165a673431f4b518",
        "prefix": "package/flags/", "expected": 542,
        "license": "MIT", "license_file": "FLAG-ICONS-LICENSE.txt",
        "upstream": "https://github.com/lipis/flag-icons",
    },
    "octicons": {
        "name": "Octicons", "version": "19.38.0", "package": "@primer/octicons",
        "url": "https://registry.npmjs.org/@primer/octicons/-/octicons-19.38.0.tgz",
        "sha256": "296ea6c40b599d955d3bb3821215c67a46e33475913c8affa4ef426f2187436e",
        "prefix": "package/build/svg/", "expected": 769,
        "license": "MIT", "license_file": "OCTICONS-LICENSE.txt",
        "upstream": "https://github.com/primer/octicons",
    },
    "radix-icons": {
        "name": "Radix Icons", "version": "1.3.2", "package": "@radix-ui/react-icons",
        "url": "https://registry.npmjs.org/@radix-ui/react-icons/-/react-icons-1.3.2.tgz",
        "sha256": "140482246ef0e254ad1d2324f746688b70ee352cedfc9ed0e2ad45d3f1542d1f",
        "source_url": "https://codeload.github.com/radix-ui/icons/tar.gz/bde33b13aa5848555f5512ac12155930fb4beb7d",
        "source_prefix": "icons-bde33b13aa5848555f5512ac12155930fb4beb7d/packages/radix-icons/icons/",
        "expected": 318, "license": "MIT", "license_file": "RADIX-ICONS-LICENSE.txt",
        "upstream": "https://github.com/radix-ui/icons",
    },
    "codicons": {
        "name": "Codicons", "version": "0.0.46-24", "package": "@vscode/codicons",
        "url": "https://registry.npmjs.org/@vscode/codicons/-/codicons-0.0.46-24.tgz",
        "sha256": "d77bf2ed152e82c4b81288c5271a3481c61559d1a5416593756e3b0fe8a02bf1",
        "prefix": "package/src/icons/", "expected": 639,
        "license": "CC-BY-4.0", "license_file": "CODICONS-LICENSE.txt",
        "upstream": "https://github.com/microsoft/vscode-codicons",
    },
}


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def member_bytes(archive: tarfile.TarFile, name: str) -> bytes:
    source = archive.extractfile(archive.getmember(name))
    if source is None:
        raise RuntimeError(f"Could not read {name}")
    return source.read()


def svg_view_box(svg: bytes, member_name: str) -> str:
    match = re.search(rb'viewBox=["\']([^"\']+)["\']', svg[:4096])
    if not match:
        raise RuntimeError(f"SVG has no viewBox: {member_name}")
    return match.group(1).decode("utf-8")


def words(*values: object) -> list[str]:
    phrases = {str(value).strip() for value in values if value and str(value).strip()}
    tokens = {token for phrase in phrases for token in re.findall(r"[^\W_]+", phrase, re.UNICODE)}
    return sorted(phrases | tokens, key=lambda value: (value.casefold(), value))


def safe_relative(member_name: str, prefix: str) -> PurePosixPath:
    relative = PurePosixPath(member_name.removeprefix(prefix))
    if member_name == str(relative) or relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError(f"Unsafe archive path: {member_name}")
    return relative


def build(library_id: str) -> None:
    config = LIBRARIES[library_id]
    package_bytes = download(str(config["url"]))
    package_hash = sha256(package_bytes)
    if package_hash != config["sha256"]:
        raise RuntimeError(f"{config['name']} checksum mismatch: {package_hash}")

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    assets = ROOT / "assets" / library_id
    assets.parent.mkdir(parents=True, exist_ok=True)
    icons: list[dict[str, object]] = []

    with tarfile.open(fileobj=BytesIO(package_bytes), mode="r:gz") as archive:
        package = json.loads(member_bytes(archive, "package/package.json"))
        if package.get("version") != config["version"]:
            raise RuntimeError(f"Unexpected {config['name']} package version")
        if package.get("license") != config["license"]:
            raise RuntimeError(f"Unexpected {config['name']} package license")

        metadata: object = {}
        if library_id == "health-icons":
            metadata = json.loads(member_bytes(archive, "package/public/icons/meta-data.json"))
        elif library_id == "devicon":
            metadata = json.loads(member_bytes(archive, "package/devicon.json"))
        elif library_id == "flag-icons":
            metadata = json.loads(member_bytes(archive, "package/country.json"))
        elif library_id == "octicons":
            metadata = json.loads(member_bytes(archive, "package/build/data.json"))
        elif library_id == "radix-icons":
            metadata = json.loads(member_bytes(archive, "package/manifest.json"))
        elif library_id == "codicons":
            metadata = json.loads(member_bytes(archive, "package/dist/metadata.json"))

        if library_id == "radix-icons":
            source_bytes = download(str(config["source_url"]))
            source_archive = tarfile.open(fileobj=BytesIO(source_bytes), mode="r:gz")
            expected_slugs = set(metadata["icons"][":15"])
            members = [
                member for member in source_archive.getmembers()
                if member.isfile() and member.name.startswith(str(config["source_prefix"]))
                and member.name.endswith(".svg")
                and "/" not in member.name[len(str(config["source_prefix"])):]
                and Path(member.name).stem in expected_slugs
            ]
            icon_archive = source_archive
            prefix = str(config["source_prefix"])
        else:
            prefix = str(config["prefix"])
            members = [
                member for member in archive.getmembers()
                if member.isfile() and member.name.startswith(prefix) and member.name.endswith(".svg")
            ]
            icon_archive = archive

        if len(members) != config["expected"]:
            raise RuntimeError(f"Unexpected {config['name']} count: {len(members)}")

        health_meta = {item["id"]: item for item in metadata} if library_id == "health-icons" else {}
        devicon_meta = {item["name"]: item for item in metadata} if library_id == "devicon" else {}
        flag_meta = {item["code"]: item for item in metadata} if library_id == "flag-icons" else {}

        with tempfile.TemporaryDirectory(dir=assets.parent) as temporary:
            staging = Path(temporary) / library_id
            for member in sorted(members, key=lambda item: item.name):
                relative = safe_relative(member.name, prefix)
                slug = relative.stem
                svg = member_bytes(icon_archive, member.name)
                view_box = svg_view_box(svg, member.name)
                output = staging.joinpath(*relative.parts)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(svg)

                variant = "default"
                group = "Icons"
                name = slug.replace("-", "_").replace("_", " ")
                keyword_values: list[object] = [name, slug, config["name"]]
                icon: dict[str, object]

                if library_id == "health-icons":
                    variant, group = relative.parts[0], relative.parts[1].replace("-", " ").title()
                    details = health_meta.get(slug, {})
                    name = str(details.get("title") or name)
                    keyword_values += details.get("tags", [])
                elif library_id == "devicon":
                    technology = relative.parts[0]
                    variant = slug.removeprefix(f"{technology}-")
                    group = "Development"
                    details = devicon_meta.get(technology, {})
                    name = f"{technology.replace('-', ' ')} ({variant.replace('-', ' ')})"
                    keyword_values += [technology, *details.get("altnames", []), *details.get("tags", [])]
                elif library_id == "flag-icons":
                    variant = relative.parts[0]
                    code = slug.upper()
                    details = flag_meta.get(slug, {})
                    country_name = details.get("name", slug)
                    name = f"{country_name} flag ({variant})"
                    group = "Flags"
                    keyword_values += [country_name, code, details.get("capital"), details.get("continent"), "country", "flag"]
                elif library_id == "octicons":
                    match = re.fullmatch(r"(.+)-(\d+)", slug)
                    if not match:
                        raise RuntimeError(f"Unexpected Octicons filename: {slug}")
                    base, variant = match.groups()
                    details = metadata.get(base, {})
                    name = f"{base.replace('-', ' ')} ({variant} px)"
                    group = "GitHub UI"
                    keyword_values += [base, *details.get("keywords", []), "github", "primer"]
                elif library_id == "radix-icons":
                    variant, group = "15 px", "UI"
                    keyword_values += ["radix", "interface", "ui"]
                elif library_id == "codicons":
                    details = metadata.get(slug, {})
                    group = str(details.get("category") or "Editor").replace("-", " ").title()
                    keyword_values += [*details.get("tags", []), details.get("description"), "vscode", "editor"]

                icon = {
                    "id": f"{library_id}:{'/'.join(relative.with_suffix('').parts)}",
                    "collection": library_id,
                    "kind": "image",
                    "name": name,
                    "src": f"./assets/{library_id}/{relative.as_posix()}",
                    "keywords": words(*keyword_values),
                    "group": group,
                    "variant": variant,
                    "viewBox": view_box,
                }
                if library_id == "devicon" and devicon_meta.get(relative.parts[0], {}).get("color"):
                    icon["brandColor"] = devicon_meta[relative.parts[0]]["color"]
                icons.append(icon)

            if assets.exists():
                shutil.rmtree(assets)
            staging.replace(assets)

        (SOURCES / str(config["license_file"])).write_bytes(member_bytes(archive, "package/LICENSE"))

    ids = [str(icon["id"]) for icon in icons]
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"Duplicate {config['name']} IDs")
    catalog_bytes = (json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    (DATA / f"{library_id}.json").write_bytes(catalog_bytes)
    manifest = {
        "name": config["name"], "version": config["version"], "package": config["package"],
        "packageUrl": config["url"], "packageSha256": package_hash,
        "upstreamUrl": config["upstream"], "assetCount": len(icons),
        "catalog": f"../{library_id}.json", "catalogSha256": sha256(catalog_bytes),
        "assets": f"../../assets/{library_id}/**/*.svg", "license": config["license"],
        "licenseFile": config["license_file"],
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
