// Keep typing responsive, coalesce intermediate queries, and respect IME commits.
export function bindSearchInput(input, { change, invalidate, search, delay = 80 }) {
  let timer = null;
  let composing = false;
  const cancel = () => { clearTimeout(timer); timer = null; };
  const commit = immediate => { cancel(); search(immediate); };
  const edit = event => {
    cancel();
    change(input.value);
    invalidate();
    if (composing || event.isComposing) return;
    timer = setTimeout(() => commit(false), delay);
  };
  input.addEventListener('compositionstart', () => { composing = true; cancel(); invalidate(); });
  input.addEventListener('compositionend', event => { composing = false; edit(event); });
  input.addEventListener('input', edit);
  input.addEventListener('keydown', event => {
    if (event.key !== 'Enter' || composing || event.isComposing || event.keyCode === 229 || event.repeat) return;
    event.preventDefault();
    change(input.value);
    commit(true);
  });
  return { cancel, get pending() { return composing || timer !== null; } };
}
