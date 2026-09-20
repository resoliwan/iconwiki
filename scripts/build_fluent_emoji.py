"""Build the local Fluent Emoji Color SVG catalog from a pinned commit."""

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
ASSETS = ROOT / "assets" / "fluent-emoji"

COMMIT = "1ffb34c752ecf5d402f04cfb4b392c77f57c54bc"
REPOSITORY = "https://github.com/microsoft/fluentui-emoji.git"
UPSTREAM_URL = "https://github.com/microsoft/fluentui-emoji"
TONES = {
    "Light": "1f3fb",
    "Medium-Light": "1f3fc",
    "Medium": "1f3fd",
    "Medium-Dark": "1f3fe",
    "Dark": "1f3ff",
}


def run(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def normalized(codes: list[str]) -> tuple[str, ...]:
    return tuple(f"{int(code, 16):x}" for code in codes if int(code, 16) != 0xFE0F)


def without_tones(codes: list[str]) -> tuple[str, ...]:
    return tuple(code for code in normalized(codes) if not 0x1F3FB <= int(code, 16) <= 0x1F3FF)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    unicode_rows = json.loads((DATA / "unicode.json").read_text(encoding="utf-8"))
    base_rows = {normalized(row["codepoints"]): row for row in unicode_rows}
    toned_rows: dict[tuple[tuple[str, ...], str], dict] = {}
    for row in unicode_rows:
        modifiers = [
            code.lower()
            for code in row["codepoints"]
            if 0x1F3FB <= int(code, 16) <= 0x1F3FF
        ]
        if len(modifiers) == 1:
            toned_rows[(without_tones(row["codepoints"]), modifiers[0])] = row

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="fluent-emoji-build-") as temp_name:
        checkout = Path(temp_name) / "checkout"
        run("git", "clone", "--filter=blob:none", "--no-checkout", REPOSITORY, str(checkout))
        run("git", "sparse-checkout", "init", "--no-cone", cwd=checkout)
        run(
            "git",
            "sparse-checkout",
            "set",
            "/assets/*/metadata.json",
            "/assets/*/Color/*.svg",
            "/assets/*/*/Color/*.svg",
            "/LICENSE",
            cwd=checkout,
        )
        run("git", "fetch", "--depth=1", "origin", COMMIT, cwd=checkout)
        run("git", "checkout", "--detach", "FETCH_HEAD", cwd=checkout)

        staged = Path(temp_name) / "assets"
        staged.mkdir()
        icons: list[dict[str, object]] = []
        upstream_assets = checkout / "assets"
        for metadata_path in sorted(upstream_assets.glob("*/metadata.json")):
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            base_key = normalized(metadata["unicode"].split())
            variants: list[tuple[Path, dict]] = []
            direct = sorted((metadata_path.parent / "Color").glob("*.svg"))
            if direct:
                variants.append((direct[0], base_rows[base_key]))
            else:
                default = sorted((metadata_path.parent / "Default" / "Color").glob("*.svg"))
                if default:
                    variants.append((default[0], base_rows[base_key]))
                for tone_name, modifier in TONES.items():
                    paths = sorted((metadata_path.parent / tone_name / "Color").glob("*.svg"))
                    if paths:
                        variants.append((paths[0], toned_rows[(base_key, modifier)]))

            for source, row in variants:
                codepoints = row["codepoints"]
                slug = "-".join(codepoints)
                filename = f"{slug}.svg"
                shutil.copyfile(source, staged / filename)
                keywords = sorted(
                    {
                        row["name"],
                        metadata.get("cldr", ""),
                        metadata.get("tts", ""),
                        *metadata.get("keywords", []),
                        *row.get("keywords", []),
                    }
                    - {""},
                    key=str.casefold,
                )
                icons.append(
                    {
                        "id": f"fluent-emoji:{slug}",
                        "collection": "fluent-emoji",
                        "kind": "image",
                        "name": row["name"],
                        "src": f"./assets/fluent-emoji/{filename}",
                        "emoji": row["emoji"],
                        "keywords": keywords,
                        "group": metadata.get("group", row.get("group", "Other")),
                        "subgroup": row.get("subgroup", ""),
                        "codepoints": codepoints,
                        "version": metadata.get("fromVersion", row.get("version", "")),
                        "skinTone": row.get("skinTone", False),
                    }
                )

        if len(icons) != 3_145:
            raise RuntimeError(f"Unexpected Fluent Emoji Color SVG count: {len(icons)}")
        if len({item["id"] for item in icons}) != len(icons):
            raise RuntimeError("Duplicate Fluent Emoji IDs were generated.")
        if len(list(staged.glob("*.svg"))) != len(icons):
            raise RuntimeError("Fluent Emoji asset filenames are not unique.")

        catalog_path = DATA / "fluent-emoji.json"
        catalog_path.write_text(
            json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        if ASSETS.exists():
            shutil.rmtree(ASSETS)
        staged.replace(ASSETS)
        shutil.copyfile(checkout / "LICENSE", SOURCES / "FLUENT-EMOJI-LICENSE.txt")

    manifest = {
        "name": "Fluent Emoji",
        "commit": COMMIT,
        "upstreamUrl": UPSTREAM_URL,
        "style": "Color SVG",
        "assetCount": len(icons),
        "catalog": "../fluent-emoji.json",
        "catalogSha256": sha256(DATA / "fluent-emoji.json"),
        "license": "MIT",
        "licenseFile": "FLUENT-EMOJI-LICENSE.txt",
    }
    (SOURCES / "fluent-emoji-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built {len(icons):,} Fluent Emoji Color SVGs.")


if __name__ == "__main__":
    main()
