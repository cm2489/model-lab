import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  AGAIN, HARD, GOOD, EASY, NEW_PER_DAY, freshState, grade, isDue, unlockedCards,
  buildQueue, applyGrade, emptyReview, estimateMinutes, parseReview, intervalLabel,
} from '../lib/scheduler.js';

const NOW = Date.parse('2026-10-14T12:00:00-04:00');
const DAY = 864e5;

test('Again: 10 minutes, interval reset, ease down 0.2, lapse counted', () => {
  const s = grade({ due: null, iv: 10, ease: 2.5, reps: 3, lapses: 0 }, AGAIN, NOW);
  assert.equal(s.iv, 0);
  assert.equal(s.ease, 2.3);
  assert.equal(s.lapses, 1);
  assert.equal(s.reps, 4);
  assert.equal(Date.parse(s.due), NOW + 10 * 60 * 1000);
});

test('Hard: interval x 1.2, at least 1 day, ease down 0.15', () => {
  const s = grade({ due: null, iv: 10, ease: 2.5, reps: 3, lapses: 0 }, HARD, NOW);
  assert.equal(s.iv, 12);
  assert.ok(Math.abs(s.ease - 2.35) < 1e-9);
  assert.equal(Date.parse(s.due), NOW + 12 * DAY);
  assert.equal(grade(freshState(), HARD, NOW).iv, 1);
});

test('Good: first time 1 day, then interval x ease', () => {
  const first = grade(freshState(), GOOD, NOW);
  assert.equal(first.iv, 1);
  assert.equal(first.ease, 2.5);
  const second = grade(first, GOOD, NOW);
  assert.equal(second.iv, 2.5);
  assert.equal(Date.parse(second.due), NOW + 2.5 * DAY);
});

test('Easy: first time 2 days, then interval x ease x 1.3, ease up 0.1', () => {
  const first = grade(freshState(), EASY, NOW);
  assert.equal(first.iv, 2);
  assert.equal(first.ease, 2.6);
  const second = grade({ ...freshState(), iv: 4, reps: 2, ease: 2.5 }, EASY, NOW);
  assert.ok(Math.abs(second.iv - 4 * 2.5 * 1.3) < 1e-9);
});

test('ease never drops below 1.3', () => {
  let s = { ...freshState(), ease: 1.35, reps: 1, iv: 3 };
  s = grade(s, AGAIN, NOW);
  assert.equal(s.ease, 1.3);
  s = grade(s, HARD, NOW);
  assert.equal(s.ease, 1.3);
});

test('interval capped at 60 days', () => {
  const s = grade({ ...freshState(), iv: 40, ease: 2.5, reps: 5 }, EASY, NOW);
  assert.equal(s.iv, 60);
  assert.equal(Date.parse(s.due), NOW + 60 * DAY);
});

test('grade does not change its input', () => {
  const prev = { ...freshState(), iv: 3, reps: 2 };
  const copy = { ...prev };
  grade(prev, GOOD, NOW);
  assert.deepEqual(prev, copy);
});

test('interval labels', () => {
  assert.equal(intervalLabel(freshState(), AGAIN, NOW), '10 min');
  assert.equal(intervalLabel(freshState(), GOOD, NOW), '1 day');
  assert.equal(intervalLabel(freshState(), EASY, NOW), '2 days');
  const seen = { ...freshState(), iv: 1, reps: 1 };
  assert.equal(intervalLabel(seen, GOOD, NOW), '2.5 days');
  assert.equal(intervalLabel(seen, EASY, NOW), '3.3 days');
  assert.equal(intervalLabel({ ...seen, iv: 20 }, GOOD, NOW), '50 days');
});

const progress = { steps: { 'lab-0.1': { done: '2026-10-07T10:00:00-04:00' }, 'lab-0.2': { done: '2026-10-07T11:00:00-04:00' } } };
const cards = [
  { id: 'f1', lab: 'foundations', after_step: null, front: 'f', back: 'b' },
  { id: 'a', lab: 'lab-0', after_step: 'lab-0.1', front: 'a', back: 'b' },
  { id: 'b', lab: 'lab-0', after_step: 'lab-0.2', front: 'b', back: 'b' },
  { id: 'c', lab: 'lab-0', after_step: 'lab-0.3', front: 'c', back: 'b' },
  { id: 'd', lab: 'lab-1', after_step: 'lab-1.1', front: 'd', back: 'b' },
];

test('unlock by after_step; foundations only when included', () => {
  assert.deepEqual(unlockedCards(cards, progress).map((c) => c.id), ['a', 'b']);
  assert.deepEqual(unlockedCards(cards, progress, { includeFoundations: true }).map((c) => c.id), ['f1', 'a', 'b']);
  assert.deepEqual(unlockedCards(cards, { steps: {} }).map((c) => c.id), []);
  // A step entry without a done time is not done.
  assert.deepEqual(unlockedCards(cards, { steps: { 'lab-0.1': { done: null } } }).map((c) => c.id), []);
});

test('empty progress: zero cards in the queue', () => {
  const q = buildQueue({ cards, review: emptyReview(), progress: { steps: {} }, now: NOW });
  assert.equal(q.queue.length, 0);
});

test('foundations toggle comes from the review store unless overridden', () => {
  const rev = { ...emptyReview(), includeFoundations: true };
  assert.deepEqual(buildQueue({ cards, review: rev, progress: { steps: {} }, now: NOW }).queue.map((c) => c.id), ['f1']);
  assert.deepEqual(buildQueue({ cards, review: rev, progress: { steps: {} }, now: NOW, includeFoundations: false }).queue.length, 0);
});

function manyCards(n) {
  return Array.from({ length: n }, (_, i) => ({ id: `n${i}`, lab: 'lab-0', after_step: 'lab-0.1', front: '', back: '' }));
}

test('new-card cap: 8 a day, counted across reviews the same Eastern day', () => {
  const deck = manyCards(20);
  let rev = emptyReview();
  let q = buildQueue({ cards: deck, review: rev, progress, now: NOW });
  assert.equal(q.fresh.length, NEW_PER_DAY);
  for (const c of q.fresh.slice(0, 5)) rev = applyGrade(rev, c.id, GOOD, NOW);
  assert.equal(rev.daily.new, 5);
  q = buildQueue({ cards: deck, review: rev, progress, now: NOW + 3600e3 });
  assert.equal(q.fresh.length, 3);
  for (const c of q.fresh) rev = applyGrade(rev, c.id, GOOD, NOW + 3600e3);
  q = buildQueue({ cards: deck, review: rev, progress, now: NOW + 3600e3 });
  assert.equal(q.fresh.length, 0);
  // Next Eastern day: 8 more.
  q = buildQueue({ cards: deck, review: rev, progress, now: NOW + DAY });
  assert.equal(q.fresh.length, 8);
});

test('regrading a seen card does not use the new-card cap', () => {
  let rev = applyGrade(emptyReview(), 'a', AGAIN, NOW);
  rev = applyGrade(rev, 'a', GOOD, NOW + 11 * 60e3);
  assert.equal(rev.daily.new, 1);
});

test('cap resets at Eastern midnight, not UTC midnight', () => {
  // 23:30 Eastern on Oct 14 is 03:30 UTC Oct 15; still the same Eastern day.
  const late = Date.parse('2026-10-14T23:30:00-04:00');
  let rev = emptyReview();
  for (const c of manyCards(8)) rev = applyGrade(rev, c.id, GOOD, NOW);
  const q = buildQueue({ cards: manyCards(12), review: rev, progress, now: late });
  assert.equal(q.fresh.length, 0);
  const q2 = buildQueue({ cards: manyCards(12), review: rev, progress, now: Date.parse('2026-10-15T00:05:00-04:00') });
  assert.equal(q2.fresh.length, 4);
});

test('due cards come before new cards, oldest due first; not-yet-due are left out', () => {
  const rev = {
    ...emptyReview(),
    cards: {
      b: { due: new Date(NOW - 1 * DAY).toISOString(), iv: 1, ease: 2.5, reps: 1, lapses: 0 },
      a: { due: new Date(NOW - 3 * DAY).toISOString(), iv: 1, ease: 2.5, reps: 1, lapses: 0 },
    },
  };
  const deck = [...cards, { id: 'e', lab: 'lab-0', after_step: 'lab-0.1', front: '', back: '' }];
  const q = buildQueue({ cards: deck, review: rev, progress, now: NOW });
  assert.deepEqual(q.queue.map((c) => c.id), ['a', 'b', 'e']);

  const later = { ...rev, cards: { ...rev.cards, a: { ...rev.cards.a, due: new Date(NOW + DAY).toISOString() } } };
  const q2 = buildQueue({ cards: deck, review: later, progress, now: NOW });
  assert.deepEqual(q2.queue.map((c) => c.id), ['b', 'e']);
  assert.equal(q2.nextDue, new Date(NOW + DAY).toISOString());
});

test('isDue: new cards are not "due", Again cards come back after 10 minutes', () => {
  assert.equal(isDue(undefined, NOW), false);
  const s = grade(freshState(), AGAIN, NOW);
  assert.equal(isDue(s, NOW + 9 * 60e3), false);
  assert.equal(isDue(s, NOW + 10 * 60e3), true);
});

test('estimate minutes', () => {
  assert.equal(estimateMinutes(0), 0);
  assert.equal(estimateMinutes(1), 1);
  assert.equal(estimateMinutes(9), 3);
});

test('export and import round-trip; bad input is refused', () => {
  let rev = applyGrade(emptyReview(), 'a', GOOD, NOW);
  rev = { ...rev, includeFoundations: true };
  assert.deepEqual(parseReview(JSON.stringify(rev)), rev);
  assert.throws(() => parseReview('not json'), /not valid JSON/);
  assert.throws(() => parseReview('[1,2]'), /review export/);
  assert.throws(() => parseReview('{"cards":null}'), /review export/);
  const cleaned = parseReview('{"cards":{"x":{"iv":"bad"},"y":{"iv":500,"ease":1,"reps":2,"due":"nope"}}}');
  assert.deepEqual(Object.keys(cleaned.cards), ['y']);
  assert.equal(cleaned.cards.y.iv, 60);
  assert.equal(cleaned.cards.y.ease, 1.3);
  assert.equal(cleaned.cards.y.due, null);
});
