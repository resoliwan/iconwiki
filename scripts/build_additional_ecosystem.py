"""Build the licensed releases listed in additional-ecosystem-packs.json."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PACKS = json.loads((DATA / "sources/additional-ecosystem-packs.json").read_text())


def svg_files(data, pattern):
    stream = BytesIO(data)
    if zipfile.is_zipfile(stream):
        with zipfile.ZipFile(stream) as archive:
            for name in sorted(archive.namelist()):
                if PurePosixPath(name).match(pattern) and not name.startswith("__MACOSX/"):
                    yield name, archive.read(name)
        return
    with tarfile.open(fileobj=BytesIO(data), mode="r:gz") as archive:
        for entry in sorted(archive.getmembers(), key=lambda e: e.name):
            path = entry.name.partition("/")[2]
            if entry.isfile() and PurePosixPath(path).match(pattern):
                yield path, archive.extractfile(entry).read()


def glyphs(svg):
    font = svg.find(".//{*}font")
    face = font.find("{*}font-face").attrib
    for glyph in font.findall("{*}glyph"):
        name = glyph.get("glyph-name")
        if name and glyph.get("d"):
            width = glyph.get("horiz-adv-x", font.get("horiz-adv-x"))
            attrs = {"xmlns": "http://www.w3.org/2000/svg", "viewBox": f"0 0 {width} {face['units-per-em']}"}
            frame = ET.Element("svg", attrs)
            ET.SubElement(frame, "path", {"d": glyph.get("d"), "transform": f"translate(0 {face['ascent']}) scale(1 -1)"})
            yield name, ET.tostring(frame)


def write_pack(library, pack, data):
    if hashlib.sha256(data).hexdigest() != pack["sha256"]:
        raise ValueError(f"Archive checksum mismatch for {library}")
    directory = ROOT / "assets" / library
    directory.mkdir(exist_ok=True)
    items = {}
    allowed = set(pack.get("include", []))
    for path, content in svg_files(data, pack["pattern"]):
        svg = ET.fromstring(content)
        files = glyphs(svg) if svg.find(".//{*}font") is not None else [(Path(path).stem, content)]
        for name, body in files:
            if allowed and name not in allowed:
                continue
            slug = re.sub("[^a-z0-9]+", "-", name.lower()).strip("-")
            if library == "oci-icons":
                slug = slug.removeprefix("oci-icon-")
            if slug in items:
                raise ValueError(f"Duplicate ID in {library}: {slug}")
            title = slug.replace("-", " ")
            category = Path(path).parts[0].strip("_").replace("_", " ").title() if library == "linea" else pack["name"]
            items[slug] = {"id": f"{library}:{slug}", "collection": library, "kind": "image",
                           "src": f"./assets/{library}/{slug}.svg", "name": title, "group": category,
                           "keywords": [title, category, pack["name"], pack["author"]]}
            (directory / f"{slug}.svg").write_bytes(body)
    if not items:
        raise ValueError(f"No icons in {library}")
    rows = [items[key] for key in sorted(items)]
    (DATA / f"{library}.json").write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{library}: {len(rows)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, help="Use pinned archives from this directory")
    args = parser.parse_args()
    for library, pack in PACKS.items():
        archive = args.cache / library if args.cache else None
        data = archive.read_bytes() if archive and archive.exists() else urllib.request.urlopen(pack["archive"], timeout=120).read()
        write_pack(library, pack, data)
