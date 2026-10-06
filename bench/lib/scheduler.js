// Flashcard scheduler: SM-2-lite, ported from the grading rules of an earlier
// course app (Again 10 minutes, Hard x1.2, Good x ease, Easy x ease x 1.3,
// ease floor 1.3, 60-day cap). Added here: at most 8 new cards a day, due
// cards before new cards, and lab cards unlocked only by finished lab steps.

import { etDate } from './time.js';
import { isStepDone } from './progress.js';

export const AGAIN = 0;
export const HARD = 1;
export const GOOD = 2;
export const EASY = 3;
export const GRADES = [
  { value: AGAIN, label: 'Again' },
  { value: HARD, label: 'Hard' },
  { value: GOOD, label: 'Good' },
  { value: EASY, label: 'Easy' },
];

export const NEW_PER_DAY = 8;
export const MAX_INTERVAL_DAYS = 60;
export const EASE_FLOOR = 1.3;
export const START_EASE = 2.5;
const DAY_MS = 864e5;
const AGAIN_MS = 10 * 60 * 1000;
const SECONDS_PER_CARD = 20;

export function freshState() {
  return { due: null, iv: 0, ease: START_EASE, reps: 0, lapses: 0 };
}

/** Grade a card. Returns a new state; the input is not changed. */
export function grade(prev, g, now = Date.now()) {
  const s = { ...freshState(), ...(prev || {}) };
  if (g === AGAIN) {
    s.lapses += 1;
    s.iv = 0;
    s.ease = Math.max(EASE_FLOOR, s.ease - 0.2);
    s.due = new Date(now + AGAIN_MS).toISOString();
  } else if (g === HARD) {
    s.iv = Math.max(1, s.iv * 1.2);
    s.ease = Math.max(EASE_FLOOR, s.ease - 0.15);
  } else if (g === GOOD) {
    s.iv = s.iv === 0 ? 1 : s.iv * s.ease;
  } else if (g === EASY) {
    s.iv = s.iv === 0 ? 2 : s.iv * s.ease * 1.3;
    s.ease += 0.1;
  } else {
    throw new RangeError(`Unknown grade: ${g}`);
  }
  s.iv = Math.min(s.iv, MAX_INTERVAL_DAYS);
  if (g !== AGAIN) s.due = new Date(now + s.iv * DAY_MS).toISOString();
  s.reps += 1;
  return s;
}

/** Short label for when a grade would bring the card back: "10 min", "1 day", "4 days". */
export function intervalLabel(prev, g, now = Date.now()) {
  if (g === AGAIN) return '10 min';
  const iv = grade(prev, g, now).iv;
  // One decimal under 10 days so Good and Easy never show the same label.
  const days = iv < 10 ? Math.round(iv * 10) / 10 : Math.round(iv);
  return days === 1 ? '1 day' : `${days} days`;
}

export function isNew(state) {
  return !state || !state.reps;
}

export function isDue(state, now = Date.now()) {
  if (isNew(state)) return false;
  if (!state.due) return true;
  return Date.parse(state.due) <= now;
}

export function isFoundations(card) {
  return card.lab === 'foundations';
}

/** Cards the learner may see: lab cards whose step is done, foundations only when included. */
export function unlockedCards(cards, progress, { includeFoundations = false } = {}) {
  return (cards || []).filter((c) => {
    if (isFoundations(c)) return includeFoundations;
    if (c.after_step == null) return true;
    return isStepDone(progress, c.after_step);
  });
}

export function emptyReview() {
  return { version: 1, cards: {}, daily: { date: null, new: 0 }, includeFoundations: false };
}

/** New cards already introduced today (Eastern). */
export function newIntroducedToday(review, now = Date.now()) {
  const d = review && review.daily;
  return d && d.date === etDate(new Date(now)) ? d.new || 0 : 0;
}

/**
 * The review queue: due cards first (oldest due first), then new cards up to
 * what is left of today's cap, in content order.
 */
export function buildQueue({ cards, review, progress, now = Date.now(), includeFoundations }) {
  const rev = review || emptyReview();
  const include = includeFoundations ?? !!rev.includeFoundations;
  const open = unlockedCards(cards, progress, { includeFoundations: include });
  const states = rev.cards || {};
  const due = open
    .filter((c) => isDue(states[c.id], now))
    .sort((a, b) => (Date.parse(states[a.id].due || 0) || 0) - (Date.parse(states[b.id].due || 0) || 0));
  const newLeft = Math.max(0, NEW_PER_DAY - newIntroducedToday(rev, now));
  const fresh = open.filter((c) => isNew(states[c.id])).slice(0, newLeft);
  const waiting = open
    .filter((c) => !isNew(states[c.id]) && !isDue(states[c.id], now))
    .map((c) => Date.parse(states[c.id].due))
    .filter((t) => !Number.isNaN(t))
    .sort((a, b) => a - b);
  return {
    due,
    fresh,
    queue: [...due, ...fresh],
    newLeft,
    unlocked: open.length,
    nextDue: waiting.length ? new Date(waiting[0]).toISOString() : null,
  };
}

/** Record a grade in the review store. Returns a new review object. */
export function applyGrade(review, cardId, g, now = Date.now()) {
  const rev = review || emptyReview();
  const prev = rev.cards && rev.cards[cardId];
  const today = etDate(new Date(now));
  let daily = rev.daily && rev.daily.date === today ? { ...rev.daily } : { date: today, new: 0 };
  if (isNew(prev)) daily = { date: today, new: (daily.new || 0) + 1 };
  return {
    ...rev,
    cards: { ...(rev.cards || {}), [cardId]: grade(prev, g, now) },
    daily,
  };
}

/** Rough minutes for a queue: about 20 seconds a card, at least 1 minute. */
export function estimateMinutes(count) {
  if (!count) return 0;
  return Math.max(1, Math.round((count * SECONDS_PER_CARD) / 60));
}

/** Parse an exported review string. Throws with a plain message when it is not one. */
export function parseReview(text) {
  let data;
  try {
    data = JSON.parse(String(text).trim());
  } catch {
    throw new Error('That is not valid JSON.');
  }
  if (!data || typeof data !== 'object' || Array.isArray(data) || typeof data.cards !== 'object' || data.cards === null || Array.isArray(data.cards)) {
    throw new Error('That does not look like a review export.');
  }
  const cards = {};
  for (const [id, s] of Object.entries(data.cards)) {
    if (!s || typeof s !== 'object') continue;
    const iv = Number(s.iv);
    const ease = Number(s.ease);
    const reps = Number(s.reps);
    if (!Number.isFinite(iv) || !Number.isFinite(ease) || !Number.isFinite(reps)) continue;
    cards[id] = {
      due: typeof s.due === 'string' && !Number.isNaN(Date.parse(s.due)) ? s.due : null,
      iv: Math.min(Math.max(iv, 0), MAX_INTERVAL_DAYS),
      ease: Math.max(EASE_FLOOR, ease),
      reps: Math.max(0, Math.floor(reps)),
      lapses: Math.max(0, Math.floor(Number(s.lapses) || 0)),
    };
  }
  const daily = data.daily && typeof data.daily.date === 'string'
    ? { date: data.daily.date, new: Math.max(0, Number(data.daily.new) || 0) }
    : { date: null, new: 0 };
  return { version: 1, cards, daily, includeFoundations: !!data.includeFoundations };
}
