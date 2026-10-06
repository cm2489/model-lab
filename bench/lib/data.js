// Fetch JSON with a saved-copy fallback. Storage and fetch are injected so
// this runs under node tests; every storage access is wrapped in try/catch.

export function makeStore(storage) {
  return {
    get(key) {
      try {
        const raw = storage && storage.getItem(key);
        return raw == null ? null : JSON.parse(raw);
      } catch {
        return null;
      }
    },
    set(key, value) {
      try {
        if (storage) storage.setItem(key, JSON.stringify(value));
        return true;
      } catch {
        return false;
      }
    },
  };
}

/**
 * Load one JSON file.
 * source: 'live' (fetched now), 'saved' (fetch failed, last good copy used),
 * 'missing' (optional file answered 404 and nothing saved), 'none' (failed, nothing saved).
 */
export async function loadJSON(url, { key, store, fetchImpl, fallback = null, optional = false }) {
  try {
    const res = await fetchImpl(url, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (key) store.set(key, { data, savedAt: new Date().toISOString() });
      return { data, source: 'live' };
    }
    if (optional && res.status === 404) {
      const saved = key ? store.get(key) : null;
      // A file that is really gone stays gone; an older saved copy is not shown.
      return { data: fallback, source: 'missing', savedAt: saved ? saved.savedAt : null };
    }
  } catch {
    // Offline, blocked or bad JSON: fall through to the saved copy.
  }
  const saved = key ? store.get(key) : null;
  if (saved && 'data' in saved) return { data: saved.data, source: 'saved', savedAt: saved.savedAt || null };
  return { data: fallback, source: 'none' };
}
