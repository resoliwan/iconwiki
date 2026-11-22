// GitHub stores a collection's SVG bodies, sizes and aliases together.
export function svgForIcon(set, name) {
  const aliases = [];
  while (!Object.hasOwn(set.icons, name)) {
    const alias = set.aliases?.[name];
    if (!alias || aliases.includes(alias)) throw new Error('Unknown icon');
    aliases.push(alias);
    name = alias.parent;
  }
  const icon = set.icons[name];
  const fields = [set, icon, ...aliases.reverse()];
  let left = 0, top = 0, width = 16, height = 16;
  let hFlip = false, vFlip = false, rotate = 0;
  for (const field of fields) {
    left = field.left ?? left;
    top = field.top ?? top;
    width = field.width ?? width;
    height = field.height ?? height;
    hFlip = hFlip !== !!field.hFlip;
    vFlip = vFlip !== !!field.vFlip;
    rotate = (rotate + (field.rotate || 0)) % 4;
  }

  let body = icon.body;
  if (hFlip || vFlip || rotate) {
    const flip = `scale(${hFlip ? -1 : 1} ${vFlip ? -1 : 1})`;
    const cx = left + width / 2, cy = top + height / 2;
    if (rotate % 2) [width, height] = [height, width];
    body = `<g transform="translate(${width / 2} ${height / 2}) rotate(${rotate * 90}) ${flip} translate(${-cx} ${-cy})">${body}</g>`;
    left = top = 0;
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${width}" height="${height}" viewBox="${left} ${top} ${width} ${height}">${body}</svg>`;
}

const cached = new Map();
const loading = new Map();

function readCollection(url) {
  if (cached.has(url)) {
    const set = cached.get(url);
    cached.delete(url);
    cached.set(url, set);
    return set;
  }
  if (!loading.has(url)) {
    const pending = fetch(url).then(async response => {
      if (!response.ok) throw new Error(`Artwork unavailable (${response.status})`);
      const set = await response.json();
      cached.set(url, set);
      if (cached.size > 3) cached.delete(cached.keys().next().value);
      return set;
    }).finally(() => loading.delete(url));
    loading.set(url, pending);
  }
  return loading.get(url);
}

let observer;
export function showArtwork(img, item) {
  if (!item.artworkSet) {
    img.src = item.src;
    return;
  }
  img.dataset.artworkSet = item.artworkSet;
  img.dataset.slug = item.id.slice(item.id.indexOf(':') + 1);
  observer ??= new IntersectionObserver(entries => {
    for (const { target, isIntersecting } of entries) {
      if (!isIntersecting || !target.isConnected) continue;
      observer.unobserve(target);
      void draw(target);
    }
  });
  observer.observe(img);
}

async function draw(img) {
  try {
    const set = await readCollection(img.dataset.artworkSet);
    if (!img.isConnected) return;
    // Keep upstream markup in an image context, including for animated SVGs.
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgForIcon(set, img.dataset.slug));
  } catch {
    img.alt = 'Artwork unavailable';
    img.title = 'Could not load artwork from GitHub';
  }
}

export function forgetArtwork(container) {
  if (observer) for (const img of container.querySelectorAll('img[data-artwork-set]')) observer.unobserve(img);
}
