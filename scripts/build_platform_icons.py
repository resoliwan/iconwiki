"""Build platform icon catalogs from pinned symbol mappings and Microsoft documentation."""
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.request import urlopen

DATA = Path(__file__).resolve().parents[1] / "data"
SF_MAP = "https://registry.npmjs.org/@rmccue/sfsymbols/-/sfsymbols-0.0.2.tgz"
SF_SEARCH_ALIASES = ["Apple SF Symbols", "San Francisco", "Apple San Francisco", "샌프란시스코", "애플 샌프란시스코"]
MS_DOCS = ("https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/"
           "a3812316d9d6678be4e526ffb4b1c4f3958d956d/hub/apps/design/iconography/")


def write_catalog(collection, entries):
    if not entries or len({item["id"] for item in entries}) != len(entries):
        raise ValueError(f"Invalid entries in {collection}")
    path = DATA / f"{collection}.json"
    path.write_text(json.dumps(entries, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{collection}: {len(entries)}")


def build_sf_symbols():
    archive = urlopen(SF_MAP, timeout=60).read()
    if hashlib.sha1(archive).hexdigest() != "fb276aa57f3ba99f60010524574574145d425351":
        raise ValueError("SF Symbols mapping checksum changed")
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        mapping = source.extractfile("package/index.js").read().decode()
    entries = []
    for name, glyph in re.findall(r'^\s*"([^"]+)": "(.)"', mapping, re.MULTILINE):
        entries.append({
            "id": f"sf-symbols:{name}", "collection": "sf-symbols", "kind": "font",
            "name": name, "glyph": glyph, "group": "System icons",
            "keywords": [name.replace(".", " "), "SF Symbols", "Apple", "macOS", "Mac", "맥", "애플", *SF_SEARCH_ALIASES],
        })
    write_catalog("sf-symbols", entries)


def build_segoe_fluent_icons():
    doc = urlopen(MS_DOCS + "segoe-fluent-icons-font.md", timeout=60).read().decode()
    rows = re.findall(r'source="(images/segoe-fluent-icons/[^"]+\.png)".*?\|\s*'
                      r'([0-9a-fA-F]{4})\s*\|\s*:::no-loc text="([^"]+)"', doc)
    entries = []
    for image, code, name in rows:
        words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)
        entries.append({
            "id": f"segoe-fluent-icons:{name}", "collection": "segoe-fluent-icons", "kind": "image",
            "name": name, "src": MS_DOCS + image, "codepoints": [code.upper()], "group": "System icons",
            "keywords": [words, "Segoe Fluent Icons", "Microsoft", "Windows", "Windows 11", "윈도우"],
        })
    write_catalog("segoe-fluent-icons", entries)


if __name__ == "__main__":
    build_sf_symbols()
    build_segoe_fluent_icons()
