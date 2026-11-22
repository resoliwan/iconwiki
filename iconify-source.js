// npm's gitHead for this release pins the artwork to the indexed version.
export const iconifyVersion = '2.2.560';
const revision = 'd1fdcf54272b299075b4fbf21851147e8c3846f9';

export function artworkURL(prefix) {
  return `https://raw.githubusercontent.com/iconify/icon-sets/${revision}/json/${prefix}.json`;
}
