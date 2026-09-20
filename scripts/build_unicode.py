"""Build a local Unicode catalog. Network is only used by this maintenance script."""
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE = DATA / "sources"
SOURCE.mkdir(parents=True, exist_ok=True)


def download(url, filename):
    path = SOURCE / filename
    if not path.exists():
        request = urllib.request.Request(url, headers={"User-Agent": "LocalIconLibrary/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
        path.write_bytes(payload)
    return path.read_text(encoding="utf-8")


emoji_url = "https://www.unicode.org/Public/17.0.0/emoji/emoji-test.txt"
emoji_text = download(emoji_url, "emoji-test-17.0.txt")
annotations = {}
provenance = [{"url": emoji_url, "file": "emoji-test-17.0.txt"}]
for language in ("en",):
    for folder in ("annotations", "annotationsDerived"):
        filename = f"cldr-48-{folder}-{language}.xml"
        url = f"https://raw.githubusercontent.com/unicode-org/cldr/release-48/common/{folder}/{language}.xml"
        xml = download(url, filename)
        provenance.append({"url": url, "file": filename})
        for node in ET.fromstring(xml).iter("annotation"):
            key = node.attrib["cp"].replace("\ufe0f", "")
            row = annotations.setdefault(key, {"keywords": []})
            value = "".join(node.itertext()).strip()
            if not value or value == "↑↑↑":
                continue
            if node.attrib.get("type") == "tts":
                row[language] = value
            row["keywords"].extend(part.strip() for part in value.split("|"))

group = subgroup = ""
items = []
for line in emoji_text.splitlines():
    if line.startswith("# group: "):
        group = line.removeprefix("# group: ")
    elif line.startswith("# subgroup: "):
        subgroup = line.removeprefix("# subgroup: ")
    elif match := re.match(r"^([A-F0-9 ]+)\s*;\s*(fully-qualified|component)\s*#\s*(\S+)\s+E([\d.]+)\s+(.+)$", line):
        codes, status, emoji, version, name = match.groups()
        codepoints = codes.split()
        meta = annotations.get(emoji.replace("\ufe0f", ""), {})
        items.append({
            "id": "unicode:" + "-".join(codepoints),
            "collection": "unicode",
            "kind": "emoji",
            "emoji": emoji,
            "name": name,
            "keywords": sorted(set(meta.get("keywords", []) + [name, meta.get("en", name)])),
            "group": group,
            "subgroup": subgroup,
            "codepoints": codepoints,
            "version": version,
            "skinTone": any(0x1F3FB <= int(code, 16) <= 0x1F3FF for code in codepoints),
            "status": status,
        })

assert len(items) > 3900, f"Unexpected catalog size: {len(items)}"
assert len({item['id'] for item in items}) == len(items)
license_url = "https://www.unicode.org/license.txt"
download(license_url, "UNICODE-LICENSE.txt")
provenance.append({"url": license_url, "file": "UNICODE-LICENSE.txt"})
for source in provenance:
    source["sha256"] = hashlib.sha256((SOURCE / source["file"]).read_bytes()).hexdigest()

(DATA / "unicode.json").write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
(DATA / "collections.json").write_text(json.dumps([{
    "id": "unicode", "name": "Unicode Emoji", "version": "17.0",
    "catalog": "./data/unicode.json", "sourceUrl": "https://www.unicode.org/emoji/",
    "license": "Unicode-3.0", "licenseUrl": "./data/sources/UNICODE-LICENSE.txt",
    "note": "Character, name, and search metadata come from Unicode and CLDR. Artwork is rendered by the device emoji font.",
}], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(SOURCE / "manifest.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
print(f"Built {len(items):,} Unicode emoji with English metadata.")
