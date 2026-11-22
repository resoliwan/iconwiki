"""Build six original icon libraries from the archive pins in ecosystem-packs.json."""

from collections import defaultdict
from io import BytesIO
import json
from pathlib import Path
import re
import tarfile
import tempfile
from xml.etree import ElementTree as ET
import zipfile

from build_recommended_icon_libraries import DATA, ROOT, SOURCES, digest, download, member_bytes, words

LIBRARIES = json.loads((SOURCES / "ecosystem-packs.json").read_text(encoding="utf-8"))
SVG = "{http://www.w3.org/2000/svg}"


def font_outlines(font_bytes, css_names=None, variant=""):
    font = ET.fromstring(font_bytes).find(f".//{SVG}font")
    face = font.find(f"{SVG}font-face")
    height = face.attrib["units-per-em"]
    ascent = face.attrib["ascent"]
    for glyph in font.findall(f"{SVG}glyph"):
        if not glyph.get("unicode") or not glyph.get("d"):
            continue
        names = css_names[ord(glyph.attrib["unicode"])] if css_names is not None else [glyph.attrib["glyph-name"]]
        slug = names[0].lower().replace("_", "-")
        width = glyph.get("horiz-adv-x", font.attrib["horiz-adv-x"])
        image = ET.Element("svg", xmlns=SVG[1:-1], viewBox=f"0 0 {width} {height}")
        # Font glyph coordinates measure upward from the baseline.
        ET.SubElement(image, "path", d=glyph.attrib["d"], transform=f"translate(0 {ascent}) scale(1 -1)")
        yield Path(variant) / f"{slug}.svg", ET.tostring(image, encoding="utf-8"), names


def artwork(library, config, payload):
    if library == "captain-icon":
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            for name in sorted(archive.namelist()):
                if re.fullmatch(r"capicon/svg/[0-9]+\.svg", name):
                    yield Path(name).name, archive.read(name), []
        return
    if library == "amazing-neo":
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            for variant, stem in [("regular", "amazing-neo"), ("brands", "amazing-neo-brands")]:
                path = f"amazing-neo-v{config['version']}/fonts/{stem}.svg"
                yield from font_outlines(archive.read(path), variant=variant)
        return
    with tarfile.open(fileobj=BytesIO(payload), mode="r:gz") as archive:
        prefix = config["prefix"]
        if library == "themify-icons":
            names = defaultdict(list)
            css = member_bytes(archive, prefix + "css/themify-icons.css").decode()
            for name, code in re.findall(r'\.ti-([\w-]+):before\s*\{\s*content:\s*"\\([a-f0-9]+)"', css):
                names[int(code, 16)].append(name)
            yield from font_outlines(member_bytes(archive, prefix + "fonts/themify.svg"), names)
            return
        for member in sorted(archive.getmembers(), key=lambda m: m.name):
            if member.isfile() and re.fullmatch(re.escape(prefix) + r"[\w-]+\.svg", member.name):
                slug = Path(member.name).stem.lower().replace("_", "-")
                content = member_bytes(archive, member.name)
                if library == "ikonate":
                    # The author's unstyled SVGs inherit the stroke from the host page.
                    root = ET.fromstring(content)
                    defaults = {"fill": "none", "stroke": "currentColor", "stroke-width": "2",
                                "stroke-linecap": "round", "stroke-linejoin": "round"}
                    attributes = " ".join(f'{k}="{v}"' for k, v in defaults.items() if k not in root.attrib)
                    content = content.replace(b"<svg ", f"<svg {attributes} ".encode(), 1)
                yield f"{slug}.svg", content, []


def build(library, config):
    payload = download(config["archive"])
    if digest(payload) != config["sha256"]:
        raise ValueError(f"Unexpected archive checksum for {library}")
    records = {}
    artwork_hashes = {}
    assets = ROOT / "assets" / library
    with tempfile.TemporaryDirectory(dir=assets.parent) as temp:
        stage = Path(temp)
        for relative, content, aliases in artwork(library, config, payload):
            path = Path(relative)
            key = path.with_suffix("").as_posix()
            if not re.fullmatch(r"(?:[a-z0-9-]+/)?[a-z0-9-]+", key) or key in records:
                raise ValueError(f"Invalid or duplicate icon ID: {library}:{key}")
            svg = ET.fromstring(content)
            if svg.tag != f"{SVG}svg":
                raise ValueError(f"Expected SVG artwork for {library}:{key}")
            variant = path.parent.name
            title = svg.findtext(f"{SVG}title")
            label = path.stem.replace("-", " ")
            if library == "captain-icon":
                label = f"Captain Icon {label}"
            keywords = words(label, path.stem, title, config["name"], variant, *aliases)
            if library == "microns":
                hash_value = digest(content)
                if hash_value in artwork_hashes:
                    original = records[artwork_hashes[hash_value]]
                    original["keywords"] = words(*original["keywords"], *keywords)
                    continue
                artwork_hashes[hash_value] = key
            record = {
                "id": f"{library}:{key}", "collection": library, "kind": "image",
                "name": title or label, "src": f"./assets/{library}/{path.as_posix()}",
                "keywords": keywords, "group": config["group"], "viewBox": svg.attrib["viewBox"],
            }
            if variant:
                record["variant"] = variant
            if variant == "brands":
                record.update(group="Brands", licenseClass="restricted")
            records[key] = record
            output = stage / path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(content)

        if "free_slugs" in config and sorted(records) != config["free_slugs"]:
            raise ValueError(f"{library} artwork differs from the pinned Free directory")
        if len(records) != config["count"]:
            raise ValueError(f"Unexpected {library} count: {len(records)}")
        for path in stage.rglob("*.svg"):
            output = assets / path.relative_to(stage)
            output.parent.mkdir(parents=True, exist_ok=True)
            path.replace(output)
    catalog = [records[key] for key in sorted(records)]
    with tempfile.NamedTemporaryFile(dir=DATA, mode="w", encoding="utf-8", delete=False) as output:
        json.dump(catalog, output, ensure_ascii=False, separators=(",", ":"))
        output.write("\n")
    Path(output.name).replace(DATA / f"{library}.json")
    print(f"Built {len(catalog):,} {config['name']} SVGs.")


if __name__ == "__main__":
    for library_id, config in LIBRARIES.items():
        build(library_id, config)
