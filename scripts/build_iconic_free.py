"""Build the pinned Iconic Free pack, optionally rechecking the creator's directory."""

import argparse
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from build_ecosystem_icons import SOURCES, build


def verify_directory(config):
    # The public Free page uses this form to load its category results.
    form = {"action": "load-contents", "setup[trigger]": "auto", "setup[object_type]": "icon",
            "setup[template_part_id]": "icon-grid-icon", "setup[more_part_id]": "icon-grid-load-more",
            "setup[source]": "category", "setup[query]": "free", "setup[count]": "500"}
    request = Request(config["upstream"], data=urlencode(form).encode(), headers={"User-Agent": "iconwiki/1.0"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode()
    slugs = re.findall(r'data-load-page-state-url\s*=\s*"https://iconic\.app/([a-z0-9-]+)/"', html)
    if sorted(slugs) != config["free_slugs"]:
        raise ValueError("The creator's Free category differs from the pinned list.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-directory", action="store_true")
    args = parser.parse_args()
    pack = json.loads((SOURCES / "iconic-free-pack.json").read_text(encoding="utf-8"))["iconic-free"]
    if args.verify_directory:
        verify_directory(pack)
    build("iconic-free", pack)
