# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools==4.60.1", "json5==0.12.1", "pillow==11.3.0", "playwright==1.55.0", "pycountry==24.6.1"]
# ///
"""Build the non-Iconify feeds from immutable GitHub snapshots."""
import argparse
from collections import defaultdict
from functools import cache
import hashlib
import html
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

import json5
import pycountry
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image
from playwright.sync_api import sync_playwright

from build_additional_ecosystem import glyphs

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
PACKS = json.loads((DATA / 'sources/feed-packs.json').read_text())


def fetch(url):
    return urlopen(Request(url, headers={'User-Agent': 'iconwiki-catalog'}), timeout=90).read()


class Snapshot:
    def __init__(self, repo, ref, cache_dir):
        self.repo, self.ref = repo, ref
        endpoint = f'repos/{repo}/git/trees/{ref}?recursive=1'
        treefile = cache_dir / repo.split('/')[1] / 'tree' if cache_dir else None
        if treefile and treefile.exists():
            tree = json.loads(treefile.read_bytes())
        else:
            try:
                tree = json.loads(fetch('https://api.github.com/' + endpoint))
            except HTTPError as error:
                if error.code != 403 or not shutil.which('gh'):
                    raise
                tree = json.loads(subprocess.check_output(['gh', 'api', endpoint]))
        if tree['truncated'] or tree['sha'] != ref:
            raise ValueError(f'Incomplete snapshot for {repo}')
        self.files = {e['path']: e['sha'] for e in tree['tree'] if e['type'] == 'blob'}

    def url(self, path):
        if path not in self.files:
            raise ValueError(f'Missing {self.repo}/{path}')
        return f'https://raw.githubusercontent.com/{self.repo}/{self.ref}/' + quote(path)

    @cache
    def read(self, path):
        body = fetch(self.url(path))
        if blob_id(body) != self.files[path]:
            raise ValueError(f'Unexpected Git blob for {path}')
        return body


def blob_id(body):
    return hashlib.sha1(f'blob {len(body)}\0'.encode() + body).hexdigest()


def words(s):
    s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', ' ', s)
    return re.sub(r'[_-]+', ' ', re.sub(r'\b([23]) D\b', r'\1D', s)).strip()


def region(code):
    found = pycountry.countries.get(alpha_2=code.upper())
    return found.name if found else code


def remote(snap, path, name=None, **metadata):
    return dict(src=snap.url(path), digest=snap.files[path], key=path, name=name or words(Path(path).stem), **metadata)


def font_rows(snapshot, selector):
    if selector == 'payment':
        font, style, prefix = 'fonts/payment-webfont.svg', 'style.css', 'pw'
    else:
        font, style, prefix = 'css/font/mfglabsiconset-webfont.svg', 'css/mfglabs_iconset.css', 'icon'
    root = ET.fromstring(snapshot.read(font))
    css = snapshot.read(style).decode()
    pattern = rf'\.{prefix}-([\w-]+):before\s*\{{\s*content:\s*"\\([0-9a-fA-F]+)"'
    names = {chr(int(code, 16)): name for name, code in re.findall(pattern, css)}
    for glyph in root.findall('.//{*}glyph'):
        glyph.set('glyph-name', names.get(glyph.get('unicode'), ''))
    for name, body in glyphs(root):
        yield dict(key=name, name=words(name), body=body, ext='svg')


@cache
def nerd_font(snapshot):
    ttf = TTFont(BytesIO(snapshot.read('patched-fonts/NerdFontsSymbolsOnly/SymbolsNerdFontMono-Regular.ttf')))
    return ttf.getGlyphSet(), ttf.getBestCmap(), json.loads(snapshot.read('glyphnames.json'))


def nerd_rows(snapshot, prefix):
    outlines, cmap, glyphnames = nerd_font(snapshot)
    names = defaultdict(list)
    for key, value in glyphnames.items():
        if key.startswith(prefix + '-'):
            names[int(value['code'], 16)].append(key.split('-', 1)[1])
    for code, aliases in sorted(names.items()):
        glyph = outlines[cmap[code]]
        bounds, pen = BoundsPen(outlines), SVGPathPen(outlines)
        glyph.draw(bounds)
        glyph.draw(pen)
        if not bounds.bounds:
            continue
        left, bottom, right, top = bounds.bounds
        box = ' '.join(f'{n:g}' for n in [left, -top, right - left, top - bottom])
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}"><path transform="scale(1 -1)" d="{pen.getCommands()}"/></svg>'
        yield dict(key=aliases[0], name=words(aliases[0]), keywords=aliases, ext='svg', body=svg.encode())


def css_rows(snapshot, library):
    if library == 'css-icon':
        # The combined stylesheet predates some glyphs in the manifest.
        css = snapshot.read('css/icons.css').decode().split('.search.icon', 1)[0]
        archive = fetch(f'https://codeload.github.com/{snapshot.repo}/tar.gz/{snapshot.ref}')
        rules = {}
        with tarfile.open(fileobj=BytesIO(archive), mode='r:gz') as tar:
            for member in tar:
                path = member.name.partition('/')[2]
                if member.isfile() and re.fullmatch(r'css/icons/[^/]+/[^/]+\.css', path):
                    content = tar.extractfile(member).read()
                    if blob_id(content) != snapshot.files[path]:
                        raise ValueError(f'Unexpected CSS blob: {path}')
                    rules[path] = content.decode()
        css += '\n'.join(rules[key] for key in sorted(rules))
        rows = [(r['name'], 'icon ' + r['classNames'], r['htmlChildMarkup']) for r in json.loads(snapshot.read('js/cssicon.json'))]
    else:
        css = snapshot.read('dist/icono.min.css').decode()
        classes = sorted(set(re.findall(r'class="(icono-[\w-]+)"', snapshot.read('index.html').decode())))
        rows = [(words(c[6:]), c, False) for c in classes]
    cells = []
    for _, classes, child in rows:
        inner = '<i></i>' if child else ''
        cells.append(f'<section><span><b class="{html.escape(classes, quote=True)}">{inner}</b></span></section>')
    style = """
    html,body{margin:0;background:transparent}
    main{display:grid;grid-template-columns:repeat(10,64px)}
    section{width:64px;height:64px;display:grid;place-items:center;position:relative}
    section span{display:block;position:relative}
    """
    if library == 'css-icon':
        style += 'section span{width:21px;height:21px}'
    else:
        style += 'section span{display:flex;color:black}'
    chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    executable = chrome if Path(chrome).is_file() else shutil.which('google-chrome') or shutil.which('chromium')
    height = 64 * ((len(rows) + 9) // 10)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=executable)
        page = browser.new_page(viewport={'width': 640, 'height': height}, device_scale_factor=3)
        page.route('**/*', lambda route: route.abort())
        page.set_content(f'<style>{css}\n{style}</style><main>{"".join(cells)}</main>')
        sheet = Image.open(BytesIO(page.screenshot(omit_background=True))).convert('RGBA')
        browser.close()
    for i, (name, classes, _) in enumerate(rows):
        x, y = i % 10 * 192, i // 10 * 192
        tile = sheet.crop((x, y, x + 192, y + 192))
        box = tile.getchannel('A').getbbox()
        if not box:
            raise ValueError(f'Empty CSS artwork: {classes}')
        buf = BytesIO()
        tile.crop(box).save(buf, format='PNG')
        yield dict(key=classes, name=name, body=buf.getvalue(), ext='png')


def feed_rows(snap, library, selector):
    if selector in ('payment', 'mfg'):
        yield from font_rows(snap, selector)
    elif selector.startswith('nerd:'):
        yield from nerd_rows(snap, selector[5:])
    elif selector == 'css':
        yield from css_rows(snap, library)
    elif selector == 'bioicons':
        for path in sorted(snap.files):
            match = re.fullmatch(r'static/icons/([^/]+)/([^/]+)/([^/]+)/([^/]+)\.svg', path)
            if not match:
                continue
            license, category, artist, name = match.groups()
            label = 'CC0-1.0' if license == 'cc-0' else license.upper()
            yield remote(snap, path, name.replace('_', ' '), group=category.replace('_', ' '),
                         attribution=artist.replace('_', ' '), license=label,
                         licenseClass='attribution' if license.startswith('cc-by') else 'permissive',
                         licenseUrl=snap.url(f'static/icons/{license}/LICENSE'),
                         sourceUrl=f'https://github.com/{snap.repo}/blob/{snap.ref}/' + quote(path))
    elif selector == 'svgl':
        text = snap.read('src/data/svgs.ts').decode().split('export const svgs: iSVG[] = ', 1)[1]
        for entry in json5.loads(text.strip().removesuffix(';')):
            route = entry['route']
            path = route if isinstance(route, str) else route['dark']
            categories = entry['category']
            categories = [categories] if isinstance(categories, str) else categories
            title = ' '.join(filter(None, (entry['title'], entry.get('subTitle'))))
            yield remote(snap, 'static' + path, title, group=categories[0], keywords=categories, sourceUrl=entry['url'])
    elif selector in ('logos', 'browsers'):
        candidates = defaultdict(list)
        for path in sorted(snap.files):
            if selector == 'logos':
                m = re.fullmatch(r'src/content/logos/([^/]+)/\1-(icon|tile|ar21|official)\.svg', path)
                if m:
                    candidates[m[1]].append((['icon', 'tile', 'ar21', 'official'].index(m[2]), path))
            else:
                m = re.fullmatch(r'src/(?:archive/)?([^/]+)/\1(\.svg|_128x128\.png|\.png)', path)
                if m:
                    candidates[m[1]].append((['.svg', '_128x128.png', '.png'].index(m[2]), path))
        for key, options in sorted(candidates.items()):
            yield remote(snap, min(options)[1], words(key))
    else:
        pattern = re.escape(selector).replace(r'\*', '[^/]+')
        for path in sorted(snap.files):
            if not re.fullmatch(pattern, path):
                continue
            name = Path(path).stem
            if library == 'adobe-spectrum-workflow':
                name = re.sub(r'^S2_Icon_|_\d+_N$', '', name)
            if library == 'mapsicon':
                name = path.split('/')[1]
            if library in ('flagkit', 'mapsicon'):
                yield remote(snap, path, region(name), keywords=[name])
            else:
                yield remote(snap, path, words(name))


def build(cache_dir):
    snapshots = {}
    # Each pack retains its own artists and license metadata. Collapse exact
    # copies inside a pack, including identical artwork used for multiple names.
    for library, pack in PACKS.items():
        key = (pack['repo'], pack['commit'])
        if key not in snapshots:
            snapshots[key] = Snapshot(*key, cache_dir)
        items, copies = {}, {}
        for row in feed_rows(snapshots[key], library, pack['selector']):
            body = row.pop('body', None)
            digest = blob_id(body) if body is not None else row.pop('digest')
            existing_art = pack.get('existing_artwork', {}).get(digest)
            if existing_art and blob_id((ROOT / existing_art).read_bytes()) == digest:
                continue
            identity = (digest, row.get('attribution'), row.get('license'))
            source = row.pop('key')
            title = row['name']
            if identity in copies:
                existing = copies[identity]['keywords']
                existing.extend(k for k in [title, *row.get('keywords', [])] if k not in existing)
                continue
            suffix = hashlib.sha256(source.encode()).hexdigest()[:10]
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') or suffix
            if slug in items:
                slug += '-' + suffix
            if slug in items:
                raise ValueError(f'Conflicting ID: {library}:{slug}')
            if body is not None:
                path = Path('assets', library, slug + '.' + row.pop('ext'))
                (ROOT / path.parent).mkdir(exist_ok=True)
                (ROOT / path).write_bytes(body)
                row['src'] = './' + path.as_posix()
            row.setdefault('group', pack['name'])
            row.setdefault('attribution', pack['author'])
            row['keywords'] = list(dict.fromkeys([title, pack['name'], row['group'], *row.get('keywords', [])]))
            row.update(id=f'{library}:{slug}', collection=library, kind='image')
            items[slug] = copies[identity] = row
        if not items:
            raise ValueError(f'Empty feed: {library}')
        rows = [items[slug] for slug in sorted(items)]
        (DATA / f'{library}.json').write_text(json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + '\n')
        print(f'{library}: {len(rows)}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, help='Optional directory of pinned Git tree responses (<repository>/tree)')
    build(parser.parse_args().cache)
