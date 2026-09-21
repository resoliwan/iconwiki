"""Build a local Blobmoji SVG catalog from the archived upstream project."""

from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = DATA / "sources"
ASSETS = ROOT / "assets" / "blobmoji"

VERSION = "15.0"
COMMIT = "7dd14d2b0141693485fd26bc35817bd290352a79"
REPOSITORY = "https://github.com/C1710/blobmoji.git"
UPSTREAM_URL = "https://github.com/C1710/blobmoji"


def run(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def normalized_sequence(codes: list[str]) -> tuple[str, ...]:
    return tuple(f"{int(code, 16):x}" for code in codes if int(code, 16) != 0xFE0F)


def normalized_name(value: str) -> str:
    value = re.sub(r"[-_. ]", " ", value)
    value = re.sub(r'''[,*\\/:'"()]''', "", value)
    return " ".join(value.lower().split())


def flag_asset(row: dict[str, object], checkout: Path) -> Path | None:
    codes = row["codepoints"]
    flag_code = ""
    if len(codes) == 2 and all(0x1F1E6 <= int(code, 16) <= 0x1F1FF for code in codes):
        flag_code = "".join(chr(ord("A") + int(code, 16) - 0x1F1E6) for code in codes)
    elif len(codes) > 2 and codes[0] == "1F3F4" and codes[-1] == "E007F":
        tag = "".join(chr(int(code, 16) - 0xE0000) for code in codes[1:-1])
        flag_code = {"gbeng": "GB-ENG", "gbsct": "GB-SCT", "gbwls": "GB-WLS"}.get(tag, "")
    if not flag_code:
        return None
    source = checkout / "third_party" / "region-flags" / "svg" / f"{flag_code}.svg"
    return source if source.is_file() else None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    unicode_rows = json.loads((DATA / "unicode.json").read_text(encoding="utf-8"))
    by_sequence = {normalized_sequence(row["codepoints"]): row for row in unicode_rows}
    order_by_id = {row["id"]: order for order, row in enumerate(unicode_rows)}
    by_name: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    for row in unicode_rows:
        by_name[normalized_name(row["name"])].append(row)

    with tempfile.TemporaryDirectory(prefix="blobmoji-build-") as temp_name:
        checkout = Path(temp_name) / "checkout"
        run("git", "clone", "--filter=blob:none", "--no-checkout", REPOSITORY, str(checkout))
        run("git", "sparse-checkout", "init", "--cone", cwd=checkout)
        run("git", "sparse-checkout", "set", "svg", "svg15", "third_party/region-flags", cwd=checkout)
        run("git", "fetch", "--depth=1", "origin", COMMIT, cwd=checkout)
        run("git", "checkout", "--detach", "FETCH_HEAD", cwd=checkout)

        matched: dict[str, tuple[dict[str, object], Path]] = {}
        skipped: list[str] = []
        for directory in (checkout / "svg", checkout / "svg15"):
            for source in sorted(directory.glob("*.svg")):
                if source.stem.startswith("emoji_u"):
                    row = by_sequence.get(normalized_sequence(source.stem.removeprefix("emoji_u").split("_")))
                else:
                    candidates = by_name[normalized_name(source.stem)]
                    row = candidates[0] if len(candidates) == 1 else None
                if row is None:
                    skipped.append(str(source.relative_to(checkout)))
                else:
                    matched[row["id"]] = (row, source)

        for row in unicode_rows:
            source = flag_asset(row, checkout)
            if source is not None:
                matched[row["id"]] = (row, source)

        staged = Path(temp_name) / "assets"
        staged.mkdir()
        icons: list[dict[str, object]] = []
        for row, source in sorted(matched.values(), key=lambda pair: order_by_id[pair[0]["id"]]):
            codepoints = row["codepoints"]
            filename = f"{'-'.join(codepoints)}.svg"
            shutil.copyfile(source, staged / filename)
            icons.append({
                **row,
                "id": f"blobmoji:{'-'.join(codepoints)}",
                "collection": "blobmoji",
                "kind": "image",
                "src": f"./assets/blobmoji/{filename}",
            })

        if len(icons) != 3_678:
            raise RuntimeError(f"Unexpected Blobmoji match count: {len(icons)}")
        if len({item["id"] for item in icons}) != len(icons):
            raise RuntimeError("Duplicate Blobmoji IDs were generated.")

        catalog_path = DATA / "blobmoji.json"
        catalog_path.write_text(
            json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        if ASSETS.exists():
            shutil.rmtree(ASSETS)
        staged.replace(ASSETS)
        SOURCES.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(checkout / "LICENSE", SOURCES / "BLOBMOJI-LICENSE.txt")
        shutil.copyfile(
            checkout / "third_party" / "region-flags" / "LICENSE",
            SOURCES / "BLOBMOJI-FLAGS-LICENSE.txt",
        )

    manifest = {
        "name": "Blobmoji",
        "version": VERSION,
        "commit": COMMIT,
        "upstreamUrl": UPSTREAM_URL,
        "style": "color SVG",
        "assetCount": len(icons),
        "skippedNonRgiOrUnmatchedAssets": len(skipped),
        "catalog": "../blobmoji.json",
        "catalogSha256": sha256(DATA / "blobmoji.json"),
        "license": "Apache-2.0",
        "licenseFile": "BLOBMOJI-LICENSE.txt",
        "flagLicenseFile": "BLOBMOJI-FLAGS-LICENSE.txt",
    }
    (SOURCES / "blobmoji-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built {len(icons):,} Blobmoji SVGs from the archived Unicode {VERSION} set.")


if __name__ == "__main__":
    main()
