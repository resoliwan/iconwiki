"""Build the local Weather Icons SVG catalog from a pinned upstream snapshot."""

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
ASSETS = ROOT / "assets" / "weather-icons"

VERSION = "2.0.12"
COMMIT = "bb80982bf1f43f2d57f9dd753e7413bf88beb9ed"
ARCHIVE_URL = f"https://github.com/erikflowers/weather-icons/archive/{COMMIT}.tar.gz"
ARCHIVE_SHA256 = "8029aa2d5c1662dec1df8631c2b134be0fc230a0015096b0a6fc31e977bfb31f"
UPSTREAM_URL = "https://github.com/erikflowers/weather-icons"
PREFIX = f"weather-icons-{COMMIT}/"
USER_AGENT = "iconwiki/1.0"
EXPECTED_COUNT = 219


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


def category(slug: str) -> str:
    for prefix, label in (
        ("day-", "Day"), ("night-", "Night"), ("moon-", "Moon"),
        ("wind-beaufort-", "Beaufort"), ("direction-", "Direction"),
        ("time-", "Time"), ("thermometer-", "Temperature"),
    ):
        if slug.startswith(prefix):
            return label
    return "Weather"


def main() -> None:
    archive_bytes = download(ARCHIVE_URL)
    actual_sha256 = sha256(archive_bytes)
    if actual_sha256 != ARCHIVE_SHA256:
        raise RuntimeError(f"Weather Icons checksum mismatch: {actual_sha256}")

    icons: list[dict[str, object]] = []
    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(fileobj=BytesIO(archive_bytes), mode="r:gz") as archive:
        package = json.loads(member_bytes(archive, PREFIX + "package.json"))
        if package.get("version") != VERSION:
            raise RuntimeError("Unexpected Weather Icons version.")
        members = sorted(
            (m for m in archive.getmembers() if m.isfile() and m.name.startswith(PREFIX + "svg/") and m.name.endswith(".svg")),
            key=lambda m: m.name,
        )
        if len(members) != EXPECTED_COUNT:
            raise RuntimeError(f"Unexpected Weather Icons count: {len(members)}")

        with tempfile.TemporaryDirectory(dir=ASSETS.parent) as temporary:
            staging = Path(temporary) / "weather-icons"
            staging.mkdir()
            for member in members:
                filename = Path(member.name).name
                slug = filename.removesuffix(".svg").removeprefix("wi-")
                svg_bytes = member_bytes(archive, member.name)
                svg_text = svg_bytes.decode("utf-8")
                match = re.search(r'viewBox="([^"]+)"', svg_text)
                if not match:
                    raise RuntimeError(f"Missing viewBox: {filename}")
                (staging / filename).write_bytes(svg_bytes)
                display_name = slug.replace("-", " ")
                icons.append({
                    "id": f"weather-icons:{slug}", "collection": "weather-icons",
                    "kind": "image", "name": display_name,
                    "keywords": sorted({display_name, *slug.split("-"), "weather", "meteorology"}, key=str.casefold),
                    "group": category(slug), "viewBox": match.group(1),
                    "src": f"./assets/weather-icons/{filename}",
                })
            if ASSETS.exists():
                shutil.rmtree(ASSETS)
            staging.replace(ASSETS)

    ids = [str(icon["id"]) for icon in icons]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate Weather Icons IDs were generated.")
    catalog_bytes = (json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    (DATA / "weather-icons.json").write_bytes(catalog_bytes)
    license_text = (
        "Weather Icons visual designs are licensed under the SIL Open Font License 1.1.\n"
        "Project code is licensed under the MIT License. Documentation is licensed under CC BY 3.0.\n\n"
        "Upstream license information: https://github.com/erikflowers/weather-icons#licensing\n"
        "SIL OFL 1.1: https://openfontlicense.org/open-font-license-official-text/\n"
    )
    (SOURCES / "WEATHER-ICONS-LICENSE.txt").write_text(license_text, encoding="utf-8")
    (SOURCES / "weather-icons-manifest.json").write_text(json.dumps({
        "name": "Weather Icons", "version": VERSION, "gitCommit": COMMIT,
        "archiveUrl": ARCHIVE_URL, "archiveSha256": actual_sha256,
        "upstreamUrl": UPSTREAM_URL, "assetCount": len(icons),
        "catalog": "../weather-icons.json", "catalogSha256": sha256(catalog_bytes),
        "assets": "../../assets/weather-icons/*.svg", "license": "OFL-1.1",
        "licenseFile": "WEATHER-ICONS-LICENSE.txt",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(icons):,} Weather Icons v{VERSION} SVGs.")


if __name__ == "__main__":
    main()
