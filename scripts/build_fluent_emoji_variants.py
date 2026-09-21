"""Build local Fluent Emoji Flat and High Contrast SVG catalogs.

High Contrast is intentionally skin-tone agnostic upstream. To keep its catalog
coverage aligned with Color and Flat, toned Unicode entries receive a copy of
the corresponding default High Contrast artwork.
"""

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

COMMIT = "1ffb34c752ecf5d402f04cfb4b392c77f57c54bc"
REPOSITORY = "https://github.com/microsoft/fluentui-emoji.git"
UPSTREAM_URL = "https://github.com/microsoft/fluentui-emoji"
EXPECTED_COUNT = 3_145
TONES = {
    "Light": "1f3fb",
    "Medium-Light": "1f3fc",
    "Medium": "1f3fd",
    "Medium-Dark": "1f3fe",
    "Dark": "1f3ff",
}
STYLES = {
    "flat": {
        "upstream": "Flat",
        "collection": "fluent-emoji-flat",
        "title": "Fluent Emoji Flat",
        "style": "Flat SVG",
    },
    "high-contrast": {
        "upstream": "High Contrast",
        "collection": "fluent-emoji-high-contrast",
        "title": "Fluent Emoji High Contrast",
        "style": "High Contrast SVG",
    },
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


def variant_rows(
    metadata_path: Path,
    metadata: dict,
    base_rows: dict,
    toned_rows: dict,
) -> list[tuple[str | None, dict]]:
    base_key = normalized(metadata["unicode"].split())
    if not (metadata_path.parent / "Default").is_dir():
        return [(None, base_rows[base_key])]

    rows: list[tuple[str | None, dict]] = [("Default", base_rows[base_key])]
    for tone_name, modifier in TONES.items():
        tone_row = toned_rows.get((base_key, modifier))
        if tone_row is not None:
            rows.append((tone_name, tone_row))
    return rows


def source_for(metadata_path: Path, tone_name: str | None, upstream_style: str) -> Path:
    parent = metadata_path.parent
    if tone_name is None:
        candidates = sorted((parent / upstream_style).glob("*.svg"))
    else:
        candidates = sorted((parent / tone_name / upstream_style).glob("*.svg"))
        if not candidates and upstream_style == "High Contrast":
            candidates = sorted((parent / "Default" / upstream_style).glob("*.svg"))
    if not candidates:
        raise RuntimeError(
            f"Missing {upstream_style} SVG for {parent.name} ({tone_name or 'direct'})"
        )
    return candidates[0]


def build_style(
    checkout: Path,
    temp_root: Path,
    config: dict[str, str],
    base_rows: dict,
    toned_rows: dict,
) -> tuple[list[dict[str, object]], Path]:
    collection = config["collection"]
    upstream_style = config["upstream"]
    staged = temp_root / collection
    staged.mkdir()
    icons: list[dict[str, object]] = []

    for metadata_path in sorted((checkout / "assets").glob("*/metadata.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        for tone_name, row in variant_rows(metadata_path, metadata, base_rows, toned_rows):
            source = source_for(metadata_path, tone_name, upstream_style)
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
                    "id": f"{collection}:{slug}",
                    "collection": collection,
                    "kind": "image",
                    "name": row["name"],
                    "src": f"./assets/{collection}/{filename}",
                    "emoji": row["emoji"],
                    "keywords": keywords,
                    "group": metadata.get("group", row.get("group", "Other")),
                    "subgroup": row.get("subgroup", ""),
                    "codepoints": codepoints,
                    "version": metadata.get("fromVersion", row.get("version", "")),
                    "skinTone": row.get("skinTone", False),
                }
            )

    if len(icons) != EXPECTED_COUNT:
        raise RuntimeError(f"Unexpected {config['title']} count: {len(icons)}")
    if len({item["id"] for item in icons}) != len(icons):
        raise RuntimeError(f"Duplicate {config['title']} IDs were generated.")
    if len(list(staged.glob("*.svg"))) != len(icons):
        raise RuntimeError(f"{config['title']} asset filenames are not unique.")

    catalog_path = DATA / f"{collection}.json"
    catalog_path.write_text(
        json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    destination = ROOT / "assets" / collection
    if destination.exists():
        shutil.rmtree(destination)
    staged.replace(destination)

    manifest = {
        "name": config["title"],
        "commit": COMMIT,
        "upstreamUrl": UPSTREAM_URL,
        "style": config["style"],
        "assetCount": len(icons),
        "catalog": f"../{collection}.json",
        "catalogSha256": sha256(catalog_path),
        "license": "MIT",
        "licenseFile": "FLUENT-EMOJI-LICENSE.txt",
    }
    (SOURCES / f"{collection}-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return icons, destination


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

    with tempfile.TemporaryDirectory(prefix="fluent-emoji-variants-build-") as temp_name:
        temp_root = Path(temp_name)
        checkout = temp_root / "checkout"
        run("git", "clone", "--filter=blob:none", "--no-checkout", REPOSITORY, str(checkout))
        run("git", "sparse-checkout", "init", "--no-cone", cwd=checkout)
        run(
            "git",
            "sparse-checkout",
            "set",
            "/assets/*/metadata.json",
            "/assets/*/Flat/*.svg",
            "/assets/*/High Contrast/*.svg",
            "/assets/*/*/Flat/*.svg",
            "/assets/*/*/High Contrast/*.svg",
            "/LICENSE",
            cwd=checkout,
        )
        run("git", "fetch", "--depth=1", "origin", COMMIT, cwd=checkout)
        run("git", "checkout", "--detach", "FETCH_HEAD", cwd=checkout)

        for config in STYLES.values():
            icons, _ = build_style(
                checkout, temp_root, config, base_rows, toned_rows
            )
            print(f"Built {len(icons):,} {config['title']} SVGs.")

        license_path = SOURCES / "FLUENT-EMOJI-LICENSE.txt"
        if not license_path.exists():
            shutil.copyfile(checkout / "LICENSE", license_path)


if __name__ == "__main__":
    main()
