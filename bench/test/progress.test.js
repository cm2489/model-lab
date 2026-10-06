import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { nextStep, normalizeProgress, weekSessions, shelf, docUrl, whereText, safeUrl, labDoneCount } from '../lib/progress.js';
import { etDate, weekRange, addDays, toEtDate, formatLongDate } from '../lib/time.js';

const labs = JSON.parse(readFileSync(new URL('./labs.fixture.json', import.meta.url), 'utf8'));
const done = (ids) => ({ steps: Object.fromEntries(ids.map((id) => [id, { done: '2026-10-07T10:00:00-04:00', minutes: 20 }])) });

test('empty progress: next step is Lab 0 step 1', () => {
  const n = nextStep(labs, normalizeProgress({ updated: null, steps: {}, sessions: [], artifacts: [] }));
  assert.equal(n.lab.id, 'lab-0');
  assert.equal(n.step.id, 'lab-0.1');
  assert.equal(n.index, 1);
  assert.equal(n.total, 4);
});

test('next step skips done steps across labs, in lab order', () => {
  const n = nextStep(labs, done(['lab-0.1', 'lab-0.2', 'lab-0.3', 'lab-0.4', 'lab-1.1']));
  assert.equal(n.step.id, 'lab-1.2');
  assert.equal(n.index, 2);
  assert.equal(n.total, 7);
});

test('next step is the first gap, even if later steps are done', () => {
  const n = nextStep(labs, done(['lab-0.1', 'lab-0.3']));
  assert.equal(n.step.id, 'lab-0.2');
});

test('labs are ordered by number, not file order', () => {
  const shuffled = { labs: [labs.labs[2], labs.labs[0], labs.labs[1]] };
  assert.equal(nextStep(shuffled, done([])).lab.id, 'lab-0');
});

test('every step done: next step is null', () => {
  const all = labs.labs.flatMap((l) => l.steps.map((s) => s.id));
  assert.equal(nextStep(labs, done(all)), null);
  assert.equal(labDoneCount(labs.labs[1], done(all)), 7);
});

test('normalizeProgress tolerates junk', () => {
  for (const junk of [null, undefined, [], 'x', { steps: [], sessions: {}, artifacts: 'no' }]) {
    const p = normalizeProgress(junk);
    assert.deepEqual(p.steps, {});
    assert.deepEqual(p.sessions, []);
    assert.deepEqual(p.artifacts, []);
  }
});

test('doc links point at the lab document and step anchor on GitHub', () => {
  assert.equal(docUrl(labs.labs[2], labs.labs[2].steps[2]), 'https://github.com/cm2489/model-lab/blob/main/labs/02-first-fine-tune/README.md#step-3');
  assert.equal(whereText('laptop'), 'At your laptop, type /lab in Claude Code.');
  assert.equal(whereText('hosted'), 'At your laptop, type /lab in Claude Code.');
});

test('shelf: one slot per public artifact, filled from progress', () => {
  const s = shelf(labs, { artifacts: [{ lab: 'lab-1', title: 'Harness', url: 'https://example.com', shipped: '2026-10-13' }] });
  assert.equal(s.total, 5);
  assert.equal(s.filled, 1);
  assert.equal(s.slots[0].lab.id, 'lab-1');
  assert.equal(s.slots[0].artifact.title, 'Harness');
  assert.equal(shelf(labs, { artifacts: [] }).filled, 0);
});

test('safeUrl allows only http(s)', () => {
  assert.equal(safeUrl('javascript:alert(1)'), null);
  assert.equal(safeUrl('nope'), null);
  assert.equal(safeUrl('https://huggingface.co/x'), 'https://huggingface.co/x');
});

// ---- Eastern Time week counting ----

const sessions = (dates) => ({ sessions: dates.map((date) => ({ date, minutes: 30, steps: [] })) });

test('week runs Monday to Sunday in Eastern Time', () => {
  // Wednesday Oct 14 2026.
  assert.deepEqual(weekRange(new Date('2026-10-14T12:00:00-04:00')), { start: '2026-10-12', end: '2026-10-18' });
  // Monday itself starts the week; Sunday ends it.
  assert.deepEqual(weekRange(new Date('2026-10-12T00:00:00-04:00')), { start: '2026-10-12', end: '2026-10-18' });
  assert.deepEqual(weekRange(new Date('2026-10-18T23:59:00-04:00')), { start: '2026-10-12', end: '2026-10-18' });
});

test('Sunday night / Monday morning boundary, Eastern not UTC', () => {
  const p = sessions(['2026-10-11', '2026-10-12', '2026-10-18', '2026-10-19']);
  // Sunday Oct 18 at 22:30 Eastern is already Monday in UTC.
  const sunNight = new Date('2026-10-18T22:30:00-04:00');
  assert.equal(etDate(sunNight), '2026-10-18');
  const w1 = weekSessions(p, sunNight);
  assert.equal(w1.count, 2); // Oct 12 and Oct 18
  assert.equal(w1.minutes, 60);
  // Monday 00:10 Eastern: new week, only Oct 19 counts.
  const w2 = weekSessions(p, new Date('2026-10-19T00:10:00-04:00'));
  assert.equal(w2.count, 1);
  assert.equal(w2.start, '2026-10-19');
});

test('across the November DST change (Sunday Nov 1 2026, 2:00 EDT -> 1:00 EST)', () => {
  const p = sessions(['2026-10-26', '2026-10-31', '2026-11-01', '2026-11-02', '2026-11-08']);
  // 23:30 EST Sunday Nov 1 = 04:30 UTC Nov 2.
  const sunLate = new Date('2026-11-02T04:30:00Z');
  assert.equal(etDate(sunLate), '2026-11-01');
  const w1 = weekSessions(p, sunLate);
  assert.deepEqual([w1.start, w1.end, w1.count], ['2026-10-26', '2026-11-01', 3]);
  // 00:30 EST Monday Nov 2 = 05:30 UTC: new week. With the old -04:00 offset this would still be Sunday.
  const monEarly = new Date('2026-11-02T05:30:00Z');
  assert.equal(etDate(monEarly), '2026-11-02');
  const w2 = weekSessions(p, monEarly);
  assert.deepEqual([w2.start, w2.end, w2.count], ['2026-11-02', '2026-11-08', 2]);
  // During the repeated 1 a.m. hour on Nov 1, still the week of Oct 26.
  const repeated = new Date('2026-11-01T06:30:00Z'); // 01:30 EST
  assert.equal(weekSessions(p, repeated).start, '2026-10-26');
  assert.equal(addDays('2026-10-31', 2), '2026-11-02');
});

test('session timestamps with an offset are read in Eastern Time', () => {
  // 01:00 UTC on Oct 19 is 21:00 Eastern on Sunday Oct 18.
  assert.equal(toEtDate('2026-10-19T01:00:00Z'), '2026-10-18');
  const p = { sessions: [{ date: '2026-10-19T01:00:00Z', minutes: 40 }, { date: 'garbage', minutes: 99 }, { minutes: 5 }] };
  const w = weekSessions(p, new Date('2026-10-15T12:00:00-04:00'));
  assert.equal(w.count, 1);
  assert.equal(w.minutes, 40);
});

test('header date is the Eastern date', () => {
  // 02:00 UTC Oct 7 is still Oct 6 in New York.
  assert.equal(formatLongDate(new Date('2026-10-07T02:00:00Z')), 'Tuesday, October 6, 2026');
});
