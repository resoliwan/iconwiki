"""Build a local Game Icons SVG catalog from a pinned official revision."""

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
ASSETS = ROOT / "assets" / "game-icons"

REVISION = "82d948812bfe3f269ef8f731dcdb07b08160edc4"
REVISION_DATE = "2026-04-23"
ARCHIVE_ROOT = f"icons-{REVISION}"
ARCHIVE_URL = f"https://codeload.github.com/game-icons/icons/tar.gz/{REVISION}"
ARCHIVE_SHA256 = "6ede4bfaed3bbe3cbe4b188b46ab2d62a28bcf737cbfcd1f0edcfdf12c124cff"
UPSTREAM_URL = "https://github.com/game-icons/icons"
EXPECTED_COUNT = 4_239
USER_AGENT = "iconwiki/1.0"

# Folder names are the upstream attribution boundary. The display names below
# follow the authors listed in the repository's license file.
AUTHORS = {
    "andymeneely": "Andy Meneely",
    "aussiesim": "Aussiesim",
    "badges": "Game-icons.net Badges",
    "carl-olsen": "Carl Olsen",
    "caro-asercion": "Caro Asercion",
    "cathelineau": "Cathelineau",
    "catsu": "Catsu",
    "darkzaitzev": "DarkZaitzev",
    "delapouite": "Delapouite",
    "faithtoken": "Faithtoken",
    "felbrigg": "Felbrigg",
    "generalace135": "GeneralAce135",
    "guard13007": "Guard13007",
    "heavenly-dog": "HeavenlyDog",
    "irongamer": "Irongamer",
    "john-colburn": "John Colburn",
    "john-redman": "John Redman",
    "kier-heyl": "Kier Heyl",
    "lorc": "Lorc",
    "lord-berandas": "Lord Berandas",
    "lucasms": "Lucas",
    "pepijn-poolman": "Pepijn Poolman",
    "pierre-leducq": "Pierre Leducq",
    "priorblue": "PriorBlue",
    "quoting": "Quoting",
    "rihlsul": "Rihlsul",
    "sbed": "Sbed",
    "seregacthtuf": "SeregaCthtuf",
    "skoll": "Skoll",
    "sparker": "Sparker",
    "spencerdub": "SpencerDub",
    "starseeker": "Starseeker",
    "various-artists": "Various Artists",
    "viscious-speed": "Viscious Speed",
    "willdabeast": "Willdabeast",
    "zajkonur": "Zajkonur",
    "zeromancer": "Zeromancer",
}
CC0_AUTHORS = {"viscious-speed", "zeromancer"}
VIEWBOX_PATTERN = re.compile(r'\bviewBox="(0 0 (?:256|512) (?:256|512))"')


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def member_bytes(archive: tarfile.TarFile, member: tarfile.TarInfo) -> bytes:
    source = archive.extractfile(member)
    if source is None:
        raise RuntimeError(f"Could not read archive member: {member.name}")
    return source.read()


def main() -> None:
    archive_bytes = download(ARCHIVE_URL)
    archive_sha256 = sha256(archive_bytes)
    if archive_sha256 != ARCHIVE_SHA256:
        raise RuntimeError(
            "Game Icons archive checksum mismatch: "
            f"expected {ARCHIVE_SHA256}, got {archive_sha256}"
        )

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    icons: list[dict[str, object]] = []
    author_counts = {author: 0 for author in AUTHORS}
    viewbox_counts: dict[str, int] = {}

    with tarfile.open(fileobj=BytesIO(archive_bytes), mode="r:gz") as archive:
        license_member = archive.getmember(f"{ARCHIVE_ROOT}/license.txt")
        license_bytes = member_bytes(archive, license_member)
        if not license_bytes.strip():
            raise RuntimeError("The Game Icons license file was empty.")

        prefix = f"{ARCHIVE_ROOT}/"
        members = sorted(
            (
                member
                for member in archive.getmembers()
                if member.isfile()
                and member.name.startswith(prefix)
                and member.name.endswith(".svg")
                and len(Path(member.name).parts) == 3
            ),
            key=lambda member: member.name,
        )

        with tempfile.TemporaryDirectory(dir=ASSETS.parent) as temporary:
            staging = Path(temporary) / "game-icons"
            staging.mkdir()

            for member in members:
                _, author_slug, filename = Path(member.name).parts
                if author_slug not in AUTHORS:
                    raise RuntimeError(f"Unknown Game Icons author folder: {author_slug}")

                slug = filename.removesuffix(".svg")
                svg_bytes = member_bytes(archive, member)
                try:
                    svg_text = svg_bytes.decode("utf-8")
                except UnicodeDecodeError as error:
                    raise RuntimeError(f"Non-UTF-8 Game Icons SVG: {member.name}") from error
                viewbox_match = VIEWBOX_PATTERN.search(svg_text)
                if viewbox_match is None:
                    raise RuntimeError(f"Unexpected Game Icons viewBox: {member.name}")
                viewbox = viewbox_match.group(1)
                viewbox_counts[viewbox] = viewbox_counts.get(viewbox, 0) + 1

                author = AUTHORS[author_slug]
                license_id = "CC0-1.0" if author_slug in CC0_AUTHORS else "CC-BY-3.0"
                license_class = "permissive" if author_slug in CC0_AUTHORS else "attribution"
                display_name = slug.replace("-", " ")
                output_dir = staging / author_slug
                output_dir.mkdir(exist_ok=True)
                (output_dir / filename).write_bytes(svg_bytes)

                icons.append(
                    {
                        "id": f"game-icons:{author_slug}:{slug}",
                        "collection": "game-icons",
                        "kind": "image",
                        "name": display_name,
                        "src": f"./assets/game-icons/{author_slug}/{filename}",
                        "keywords": sorted(
                            {display_name, *slug.split("-"), "game", "game icons", author},
                            key=str.casefold,
                        ),
                        "group": author,
                        "author": author,
                        "attribution": f"Icons made by {author}",
                        "license": license_id,
                        "licenseClass": license_class,
                        "size": int(viewbox.split()[2]),
                        "viewBox": viewbox,
                    }
                )
                author_counts[author_slug] += 1

            if ASSETS.exists():
                shutil.rmtree(ASSETS)
            staging.replace(ASSETS)

    if len(icons) != EXPECTED_COUNT:
        raise RuntimeError(
            f"Unexpected Game Icons asset count: expected {EXPECTED_COUNT}, got {len(icons)}"
        )
    if any(count == 0 for count in author_counts.values()):
        raise RuntimeError(f"An expected Game Icons author folder was empty: {author_counts}")
    ids = [str(icon["id"]) for icon in icons]
    sources = [str(icon["src"]) for icon in icons]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate Game Icons IDs were generated.")
    if len(sources) != len(set(sources)):
        raise RuntimeError("Duplicate Game Icons asset paths were generated.")
    if any(not (ROOT / source.removeprefix("./")).is_file() for source in sources):
        raise RuntimeError("A Game Icons catalog asset is missing.")

    catalog_bytes = (
        json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    (DATA / "game-icons.json").write_bytes(catalog_bytes)
    (SOURCES / "GAME-ICONS-LICENSE.txt").write_bytes(license_bytes)
    (SOURCES / "game-icons-manifest.json").write_text(
        json.dumps(
            {
                "name": "Game Icons",
                "revision": REVISION,
                "revisionDate": REVISION_DATE,
                "archiveUrl": ARCHIVE_URL,
                "archiveSha256": archive_sha256,
                "upstreamUrl": UPSTREAM_URL,
                "authorCount": len(author_counts),
                "authorCounts": author_counts,
                "cc0Authors": sorted(CC0_AUTHORS),
                "viewBoxCounts": viewbox_counts,
                "assetCount": len(icons),
                "catalog": "../game-icons.json",
                "catalogSha256": sha256(catalog_bytes),
                "assets": "../../assets/game-icons/*/*.svg",
                "license": "CC-BY-3.0 (CC0-1.0 for named contributors)",
                "licenseFile": "GAME-ICONS-LICENSE.txt",
                "attribution": "Icons made by {author}",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Built {len(icons):,} Game Icons SVGs from revision {REVISION[:12]} "
        f"across {len(author_counts)} author folders."
    )


if __name__ == "__main__":
    main()
