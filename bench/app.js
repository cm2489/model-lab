// Lab bench: the page. Pure logic lives in lib/ and is unit-tested there.
// This file only loads data, renders, and runs the review flow.
// It never writes progress.json; review state lives in this browser only.

import { formatLongDate, formatShortDate, formatTime } from './lib/time.js';
import {
  normalizeProgress, nextStep, orderedLabs, labDoneCount, whereLabel, docUrl,
  weekSessions, shelf, safeUrl, isStepDone,
} from './lib/progress.js';
import {
  GRADES, buildQueue, applyGrade, emptyReview, estimateMinutes, parseReview,
  intervalLabel, isFoundations,
} from './lib/scheduler.js';
import { loadJSON, makeStore } from './lib/data.js';

// ---------- setup ----------

const params = new URLSearchParams(location.search);
const fixtureParam = params.get('fixture');
const FIXTURE = fixtureParam && /^[a-z0-9-]{1,40}$/.test(fixtureParam) ? fixtureParam : null;
const NS = FIXTURE ? `bench:fixture:${FIXTURE}:` : 'bench:';
const REVIEW_KEY = `${NS}review`;

let rawStorage = null;
try { rawStorage = window.localStorage; } catch { rawStorage = null; }
const store = makeStore(rawStorage);

const S = {
  labs: { labs: [] },
  cards: [],
  progress: normalizeProgress(null),
  review: emptyReview(),
  fixedNow: null,
  notes: [],
  sources: {},
};

const $ = (id) => document.getElementById(id);
const now = () => (S.fixedNow != null ? S.fixedNow : Date.now());

function esc(v) {
  return String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function plural(n, one, many = `${one}s`) {
  return `${n} ${n === 1 ? one : many}`;
}

function stamp(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return `${formatShortDate(d)}, ${formatTime(d)}`;
}

// ---------- data ----------

const live = (data) => Promise.resolve({ data, source: 'live' });

async function loadFixture(name) {
  try {
    const res = await fetch(`dev/fixtures/${name}.json`, { cache: 'no-store' });
    if (res.ok) return await res.json();
  } catch { /* handled below */ }
  S.notes.push(`Fixture "${name}" could not be loaded. Showing real data.`);
  return null;
}

async function load() {
  const fx = FIXTURE ? await loadFixture(FIXTURE) : null;
  const opts = (name, extra = {}) => ({ key: `${NS}cache:${name}`, store, fetchImpl: fetch.bind(window), ...extra });

  const [labsR, cardsR, foundR, progR] = await Promise.all([
    loadJSON('../content/labs.json', opts('labs', { fallback: { labs: [] } })),
    fx && Array.isArray(fx.cards) ? live(fx.cards) : loadJSON('../content/cards.json', opts('cards', { fallback: [] })),
    fx && Array.isArray(fx.foundations) ? live(fx.foundations)
      : loadJSON('../foundations/cards.json', opts('foundations', { fallback: [], optional: true })),
    fx && fx.progress ? live(fx.progress) : loadJSON('../progress.json', opts('progress', { fallback: null })),
  ]);

  S.sources = { labs: labsR, cards: cardsR, foundations: foundR, progress: progR };
  S.labs = labsR.data && Array.isArray(labsR.data.labs) ? labsR.data : { labs: [] };
  if (fx && fx.labStatus) {
    S.labs = { ...S.labs, labs: S.labs.labs.map((l) => (fx.labStatus[l.id] ? { ...l, status: fx.labStatus[l.id] } : l)) };
  }
  const cardList = [
    ...(Array.isArray(cardsR.data) ? cardsR.data : []),
    ...(Array.isArray(foundR.data) ? foundR.data : []),
  ].filter((c) => c && typeof c.id === 'string' && c.front);
  const seen = new Set();
  S.cards = cardList.filter((c) => (seen.has(c.id) ? false : (seen.add(c.id), true)));
  S.progress = normalizeProgress(progR.data);

  if (fx && fx.now && !Number.isNaN(Date.parse(fx.now))) S.fixedNow = Date.parse(fx.now);
  if (fx && fx.review && store.get(REVIEW_KEY) == null) store.set(REVIEW_KEY, fx.review);

  const saved = store.get(REVIEW_KEY);
  try {
    S.review = saved ? parseReview(JSON.stringify(saved)) : emptyReview();
  } catch {
    S.review = emptyReview();
  }

  const names = { labs: 'the lab list', cards: 'cards', foundations: 'foundations cards', progress: 'progress' };
  const stale = Object.entries(S.sources).filter(([, r]) => r.source === 'saved');
  if (stale.length) {
    const when = stale.map(([, r]) => r.savedAt).filter(Boolean).sort()[0];
    S.notes.push(`Could not load the latest data. Showing saved copy of ${stale.map(([k]) => names[k]).join(', ')}${when ? ` from ${stamp(when)}` : ''}.`);
  }
  const failed = Object.entries(S.sources).filter(([k, r]) => r.source === 'none' && k !== 'foundations');
  if (failed.length) {
    S.notes.push(`Could not load ${failed.map(([k]) => names[k]).join(', ')}, and no saved copy exists yet.`);
  }
  if (FIXTURE) S.notes.push(`Test data: fixture "${FIXTURE}".`);
}

function saveReview() {
  if (!store.set(REVIEW_KEY, S.review)) {
    S.notes.push('This browser is not saving review history. Use Export to keep it.');
    renderNotice();
  }
}

// ---------- rendering ----------

const ICON_DONE = '<svg viewBox="0 0 16 16" aria-hidden="true"><circle class="done-ring" cx="8" cy="8" r="7"/><path class="tick" d="M4.8 8.3l2.1 2.1 4.3-4.6"/></svg>';
const ICON_OPEN = '<svg viewBox="0 0 16 16" aria-hidden="true"><circle class="ring" cx="8" cy="8" r="7"/></svg>';

const STATUS_WORD = { ready: 'Ready', draft: 'Draft', planned: 'Being built' };

function renderNotice() {
  const el = $('notice');
  const notes = [...new Set(S.notes)];
  el.hidden = notes.length === 0;
  el.textContent = notes.join(' ');
}

function renderNext() {
  const body = $('next-body');
  const n = nextStep(S.labs, S.progress);
  if (!S.labs.labs.length) {
    body.innerHTML = '<p class="muted">The lab list is not available right now.</p>';
    return;
  }
  if (!n) {
    body.innerHTML = `<p class="title">Every step is done.</p>
      <p class="meta">All ${S.labs.labs.length} labs in this track are finished.</p>`;
    return;
  }
  const { lab, step, index, total } = n;
  const url = docUrl(lab, step);
  let status = '';
  if (lab.status === 'planned') {
    status = `<p class="status-line">Lab ${esc(lab.number)} is still being built. This step is not ready to do yet.</p>`;
  } else if (lab.status === 'draft') {
    status = `<p class="status-line">Lab ${esc(lab.number)} is a draft: written, not yet checked end to end.</p>`;
  }
  const where = step.where === 'phone'
    ? '<p class="where">On your phone: open the lab document.</p>'
    : '<p class="where">At your laptop, type <code>/lab</code> in Claude Code.</p>';
  body.innerHTML = `
    <p class="pos">Lab ${esc(lab.number)} · step ${index} of ${total}</p>
    <p class="title">${esc(step.title)}</p>
    <p class="meta">${esc(step.minutes)} min · ${esc(whereLabel(step.where))} · ${esc(lab.title)}</p>
    ${lab.status === 'planned' ? '' : where}
    ${status}
    ${url ? `<a class="doc-link" href="${esc(url)}" rel="noopener">Open the lab document</a>` : ''}`;
}

function queue() {
  return buildQueue({ cards: S.cards, review: S.review, progress: S.progress, now: now() });
}

function renderRecall() {
  const q = queue();
  const n = q.queue.length;
  const body = $('recall-body');
  if (n > 0) {
    const parts = [];
    if (q.due.length) parts.push(`${q.due.length} to review`);
    if (q.fresh.length) parts.push(`${q.fresh.length} new`);
    body.innerHTML = `
      <button type="button" class="recall-btn" id="recall-start">
        <span class="figure">${plural(n, 'card')} due · about ${estimateMinutes(n)} min</span>
        <span class="go">Start</span>
      </button>
      <p class="figure-sub">${esc(parts.join(', '))}</p>`;
    $('recall-start').addEventListener('click', openReview);
  } else {
    let sub;
    const labCards = S.cards.filter((c) => !isFoundations(c)).length;
    if (!q.unlocked && !labCards) sub = 'No lab cards are written yet.';
    else if (!q.unlocked) sub = 'Cards unlock as you finish lab steps.';
    else if (q.nextDue) sub = `All caught up. Next card due ${stamp(q.nextDue)}.`;
    else if (q.newLeft === 0) sub = 'All caught up. More new cards tomorrow.';
    else sub = 'All caught up.';
    body.innerHTML = `<div class="recall-quiet"><p class="figure">0 cards due</p><p class="figure-sub">${esc(sub)}</p></div>`;
  }
  const fCount = S.cards.filter(isFoundations).length;
  const box = $('include-foundations');
  box.checked = !!S.review.includeFoundations;
  box.nextElementSibling.textContent = fCount
    ? `Include foundations (${plural(fCount, 'card')})`
    : 'Include foundations (none yet)';
}

function renderShelf() {
  const s = shelf(S.labs, S.progress);
  const body = $('shelf-body');
  if (!s.total) {
    body.innerHTML = '<p class="muted">No public artifacts are planned.</p>';
    return;
  }
  const items = s.slots.map(({ lab, artifact }) => {
    if (!artifact) {
      return `<li class="slot empty"><span class="lab-no">Lab ${esc(lab.number)}</span>
        <span class="what">${esc(lab.artifact.title)}</span></li>`;
    }
    const url = safeUrl(artifact.url);
    const title = esc(artifact.title || lab.artifact.title);
    return `<li class="slot"><span class="lab-no">Lab ${esc(lab.number)}</span>
      <span class="what">${url ? `<a href="${esc(url)}" rel="noopener">${title}</a>` : title}</span>
      ${artifact.shipped ? `<span class="when">Shipped ${esc(formatShortDate(artifact.shipped))}</span>` : ''}</li>`;
  }).join('');
  body.innerHTML = `<p class="figure">${s.filled} of ${s.total}</p>
    <p class="figure-sub">public artifacts shipped</p>
    <ol class="shelf">${items}</ol>`;
}

function renderWeek() {
  const w = weekSessions(S.progress, new Date(now()));
  $('week-body').innerHTML = `<p class="figure">${w.count} of ${w.target} sessions</p>
    <p class="figure-sub">${plural(w.minutes, 'minute')} · Mon ${esc(formatShortDate(w.start))} to Sun ${esc(formatShortDate(w.end))}</p>`;
}

function renderLabs() {
  const labs = orderedLabs(S.labs);
  const n = nextStep(S.labs, S.progress);
  const body = $('labs-body');
  if (!labs.length) {
    body.innerHTML = '<p class="muted">The lab list is not available right now.</p>';
    return;
  }
  const openIds = new Set([...body.querySelectorAll('details[open]')].map((d) => d.dataset.id));
  const firstRender = !body.querySelector('details');
  body.innerHTML = `<div class="labs">${labs.map((lab) => {
    const steps = lab.steps || [];
    const doneN = labDoneCount(lab, S.progress);
    const allDone = steps.length > 0 && doneN === steps.length;
    const open = firstRender ? (n && n.lab.id === lab.id) : openIds.has(lab.id);
    const statusWord = allDone ? 'Done' : (STATUS_WORD[lab.status] || '');
    const url = docUrl(lab, null);
    return `<details class="lab" data-id="${esc(lab.id)}"${open ? ' open' : ''}>
      <summary>
        <span class="lab-name"><span class="num">${esc(lab.number)}</span> ${esc(lab.title)}${statusWord ? `<span class="status">${esc(statusWord)}</span>` : ''}</span>
        <span class="lab-meta">${doneN} of ${steps.length}<span class="chev" aria-hidden="true"></span></span>
      </summary>
      ${lab.aim ? `<p class="aim">${esc(lab.aim)}</p>` : ''}
      <ul class="steps">${steps.map((s, i) => {
        const done = isStepDone(S.progress, s.id);
        const current = n && n.step.id === s.id;
        return `<li class="${done ? 'done' : ''}${current ? ' current' : ''}">
          <span class="mark">${done ? ICON_DONE : ICON_OPEN}</span>
          <span class="s-title">${i + 1}. ${esc(s.title)}<span class="sr-only">${done ? ', done' : ', not done'}${current ? ', next' : ''}</span></span>
          <span class="s-min">${esc(s.minutes)} min</span></li>`;
      }).join('')}</ul>
      ${url ? `<a class="lab-doc" href="${esc(url)}" rel="noopener">Lab ${esc(lab.number)} document</a>` : ''}
    </details>`;
  }).join('')}</div>`;
}

function renderFoot() {
  const up = S.progress.updated;
  $('foot').textContent = up
    ? `Progress last updated ${stamp(up)} Eastern. Times shown are Eastern.`
    : 'No lab steps logged yet. Times shown are Eastern.';
}

function renderAll() {
  $('today').textContent = formatLongDate(new Date(now()));
  renderNotice();
  renderNext();
  renderRecall();
  renderShelf();
  renderWeek();
  renderLabs();
  renderFoot();
}

// ---------- review flow ----------

const R = { list: [], i: 0, revealed: false, again: 0, graded: 0, opener: null };

function openReview() {
  const q = queue();
  if (!q.queue.length) return;
  R.list = q.queue;
  R.i = 0;
  R.revealed = false;
  R.again = 0;
  R.graded = 0;
  R.opener = document.activeElement;
  $('home').inert = true;
  document.body.classList.add('locked');
  $('review').hidden = false;
  renderReview();
}

function closeReview() {
  $('review').hidden = true;
  $('home').inert = false;
  document.body.classList.remove('locked');
  renderRecall();
  const target = $('recall-start') || $('include-foundations');
  if (target) target.focus();
}

function renderReview() {
  const card = R.list[R.i];
  const cardEl = $('review-card');
  const actions = $('review-actions');
  if (!card) {
    $('review-count').textContent = '';
    const back = R.again ? ` ${plural(R.again, 'card')} come${R.again === 1 ? 's' : ''} back in 10 minutes.` : '';
    cardEl.innerHTML = `<p class="end">Done for now.</p><p class="muted">${plural(R.graded, 'card')} reviewed.${esc(back)}</p>`;
    actions.innerHTML = '<button type="button" class="btn primary full" id="r-done">Back to the bench</button>';
    $('r-done').addEventListener('click', closeReview);
    $('r-done').focus();
    return;
  }
  $('review-count').textContent = `${R.i + 1} of ${R.list.length}`;
  const prev = S.review.cards[card.id];
  const labLabel = card.lab === 'foundations' ? 'Foundations' : (card.lab || '').replace('lab-', 'Lab ');
  cardEl.innerHTML = `
    <p class="concept">${esc(labLabel)}${card.concept ? ` · ${esc(card.concept)}` : ''}</p>
    <p class="front">${esc(card.front)}</p>
    ${R.revealed ? `<p class="back">${esc(card.back)}</p>` : ''}`;
  if (!R.revealed) {
    actions.innerHTML = `<button type="button" class="btn primary full" id="r-show">Show answer</button>
      <p class="keys">Space to show</p>`;
    $('r-show').addEventListener('click', reveal);
    $('r-show').focus();
  } else {
    actions.innerHTML = `<div class="grades" role="group" aria-label="How well did you recall it?">
      ${GRADES.map((g) => `<button type="button" class="btn" data-grade="${g.value}">${g.label}<small>${esc(intervalLabel(prev, g.value, now()))}</small></button>`).join('')}
      </div><p class="keys">Keys 1 to 4</p>`;
    actions.querySelectorAll('[data-grade]').forEach((b) => b.addEventListener('click', () => gradeCurrent(Number(b.dataset.grade))));
    actions.querySelector('[data-grade="2"]').focus();
  }
}

function reveal() {
  R.revealed = true;
  renderReview();
}

function gradeCurrent(g) {
  const card = R.list[R.i];
  if (!card || !R.revealed) return;
  S.review = applyGrade(S.review, card.id, g, now());
  saveReview();
  R.graded += 1;
  if (g === 0) R.again += 1;
  R.i += 1;
  R.revealed = false;
  renderReview();
}

document.addEventListener('keydown', (e) => {
  if ($('review').hidden) return;
  if (e.key === 'Escape') { e.preventDefault(); closeReview(); return; }
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const onButton = e.target instanceof HTMLButtonElement;
  if (!R.revealed && e.key === ' ' && !onButton && R.list[R.i]) { e.preventDefault(); reveal(); return; }
  if (R.revealed && /^[1-4]$/.test(e.key)) { e.preventDefault(); gradeCurrent(Number(e.key) - 1); }
});

// ---------- controls ----------

$('review-close').addEventListener('click', closeReview);

$('include-foundations').addEventListener('change', (e) => {
  S.review = { ...S.review, includeFoundations: e.target.checked };
  saveReview();
  renderRecall();
});

$('export-btn').addEventListener('click', async () => {
  const text = JSON.stringify(S.review);
  const ta = $('backup-text');
  ta.value = text;
  let copied = false;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      copied = true;
    }
  } catch { copied = false; }
  if (!copied) { ta.focus(); ta.select(); }
  $('backup-msg').textContent = copied
    ? `Copied ${plural(Object.keys(S.review.cards).length, 'card')} of history. Paste it somewhere safe.`
    : 'Selected. Copy it and paste it somewhere safe.';
});

$('import-btn').addEventListener('click', () => {
  const text = $('backup-text').value;
  const msg = $('backup-msg');
  if (!text.trim()) { msg.textContent = 'Paste exported data into the box first.'; return; }
  let next;
  try { next = parseReview(text); } catch (err) { msg.textContent = err.message; return; }
  const count = Object.keys(next.cards).length;
  if (!window.confirm(`Replace this browser's review history with the pasted data (${plural(count, 'card')})?`)) return;
  S.review = next;
  saveReview();
  msg.textContent = `Imported ${plural(count, 'card')} of history.`;
  renderRecall();
});

// Re-check the date and due cards when the tab comes back.
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && $('review').hidden) {
    $('today').textContent = formatLongDate(new Date(now()));
    renderRecall();
    renderWeek();
  }
});

// ---------- start ----------

function start() {
  renderAll();
  // Dev harness only: ?fixture=mid-track&review=front|back opens the review for screenshots.
  const r = FIXTURE && params.get('review');
  if (r === 'front' || r === 'back') {
    openReview();
    if (r === 'back' && R.list.length) reveal();
  }
}

load().then(start, (err) => {
  S.notes.push('Something went wrong while loading.');
  renderAll();
  console.error(err); // eslint-disable-line no-console
});

