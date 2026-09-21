"""Build a local Noto Emoji SVG catalog from a pinned official release."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = DATA / "sources"
ASSETS = ROOT / "assets" / "noto-emoji"

VERSION = "2.051"
COMMIT = "8998f5dd683424a73e2314a8c1f1e359c19e8742"
REPOSITORY = "https://github.com/googlefonts/noto-emoji.git"
UPSTREAM_URL = "https://github.com/googlefonts/noto-emoji"


def run(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def normalized(codes: list[str]) -> tuple[str, ...]:
    return tuple(f"{int(code, 16):x}" for code in codes if int(code, 16) != 0xFE0F)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    unicode_rows = json.loads((DATA / "unicode.json").read_text(encoding="utf-8"))
    unicode_by_sequence = {normalized(row["codepoints"]): row for row in unicode_rows}
    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="noto-emoji-build-") as temp_name:
        checkout = Path(temp_name) / "checkout"
        run("git", "clone", "--filter=blob:none", "--no-checkout", REPOSITORY, str(checkout))
        run("git", "sparse-checkout", "init", "--cone", cwd=checkout)
        run("git", "sparse-checkout", "set", "svg", cwd=checkout)
        run("git", "fetch", "--depth=1", "origin", COMMIT, cwd=checkout)
        run("git", "checkout", "--detach", "FETCH_HEAD", cwd=checkout)

        staged = Path(temp_name) / "assets"
        staged.mkdir()
        icons: list[dict[str, object]] = []
        skipped: list[str] = []
        for source in sorted((checkout / "svg").glob("emoji_u*.svg")):
            raw_codes = source.stem.removeprefix("emoji_u").split("_")
            row = unicode_by_sequence.get(normalized(raw_codes))
            if row is None:
                skipped.append(source.name)
                continue
            codepoints = row["codepoints"]
            slug = "-".join(codepoints)
            filename = f"{slug}.svg"
            shutil.copyfile(source, staged / filename)
            icons.append(
                {
                    "id": f"noto-emoji:{slug}",
                    "collection": "noto-emoji",
                    "kind": "image",
                    "name": row["name"],
                    "src": f"./assets/noto-emoji/{filename}",
                    "emoji": row["emoji"],
                    "keywords": row.get("keywords", []),
                    "group": row.get("group", "Other"),
                    "subgroup": row.get("subgroup", ""),
                    "codepoints": codepoints,
                    "version": row.get("version", ""),
                    "skinTone": row.get("skinTone", False),
                }
            )

        if len(icons) < 3_600:
            raise RuntimeError(f"Unexpected Noto Emoji match count: {len(icons)}")
        if len({item["id"] for item in icons}) != len(icons):
            raise RuntimeError("Duplicate Noto Emoji IDs were generated.")

        catalog_path = DATA / "noto-emoji.json"
        catalog_path.write_text(
            json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        if ASSETS.exists():
            shutil.rmtree(ASSETS)
        staged.replace(ASSETS)
        shutil.copyfile(checkout / "svg" / "LICENSE", SOURCES / "NOTO-EMOJI-SVG-LICENSE.txt")

    manifest = {
        "name": "Noto Color Emoji",
        "version": VERSION,
        "commit": COMMIT,
        "upstreamUrl": UPSTREAM_URL,
        "style": "color SVG",
        "assetCount": len(icons),
        "skippedUnqualifiedOrComponentAssets": len(skipped),
        "catalog": "../noto-emoji.json",
        "catalogSha256": sha256(DATA / "noto-emoji.json"),
        "license": "Apache-2.0",
        "licenseFile": "NOTO-EMOJI-SVG-LICENSE.txt",
    }
    (SOURCES / "noto-emoji-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built {len(icons):,} Noto Color Emoji SVGs from v{VERSION}.")


if __name__ == "__main__":
    main()
