import { test } from 'node:test';
import assert from 'node:assert/strict';
import { loadJSON, makeStore } from '../lib/data.js';

function memoryStorage() {
  const m = new Map();
  return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)) };
}
const ok = (data) => async () => ({ ok: true, status: 200, json: async () => data });
const status = (code) => async () => ({ ok: false, status: code, json: async () => ({}) });
const offline = async () => { throw new TypeError('Failed to fetch'); };

test('live fetch saves a copy; a later failure shows the saved copy', async () => {
  const store = makeStore(memoryStorage());
  const live = await loadJSON('x', { key: 'k', store, fetchImpl: ok({ a: 1 }) });
  assert.deepEqual(live, { data: { a: 1 }, source: 'live' });
  const off = await loadJSON('x', { key: 'k', store, fetchImpl: offline });
  assert.equal(off.source, 'saved');
  assert.deepEqual(off.data, { a: 1 });
  const err = await loadJSON('x', { key: 'k', store, fetchImpl: status(500) });
  assert.equal(err.source, 'saved');
});

test('no saved copy: fallback', async () => {
  const store = makeStore(memoryStorage());
  const r = await loadJSON('x', { key: 'k', store, fetchImpl: offline, fallback: [] });
  assert.deepEqual(r, { data: [], source: 'none' });
});

test('optional file 404: empty, not an error', async () => {
  const store = makeStore(memoryStorage());
  const r = await loadJSON('x', { key: 'k', store, fetchImpl: status(404), fallback: [], optional: true });
  assert.deepEqual(r.data, []);
  assert.equal(r.source, 'missing');
});

test('storage that throws on every call does not break loading', async () => {
  const angry = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); } };
  const store = makeStore(angry);
  assert.equal(store.get('k'), null);
  assert.equal(store.set('k', 1), false);
  const r = await loadJSON('x', { key: 'k', store, fetchImpl: ok([1]) });
  assert.deepEqual(r.data, [1]);
  const r2 = await loadJSON('x', { key: 'k', store, fetchImpl: offline, fallback: null });
  assert.equal(r2.source, 'none');
});

test('bad JSON body falls back to saved copy', async () => {
  const store = makeStore(memoryStorage());
  await loadJSON('x', { key: 'k', store, fetchImpl: ok({ good: true }) });
  const bad = async () => ({ ok: true, status: 200, json: async () => { throw new SyntaxError('bad'); } });
  const r = await loadJSON('x', { key: 'k', store, fetchImpl: bad });
  assert.equal(r.source, 'saved');
  assert.deepEqual(r.data, { good: true });
});
