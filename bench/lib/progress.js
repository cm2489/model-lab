// Read-only views over content/labs.json and progress.json.

import { toEtDate, weekRange } from './time.js';

export const REPO_BLOB = 'https://github.com/cm2489/model-lab/blob/main/';
export const WEEKLY_TARGET = 5;

export function normalizeProgress(p) {
  const src = p && typeof p === 'object' && !Array.isArray(p) ? p : {};
  return {
    updated: src.updated ?? null,
    steps: src.steps && typeof src.steps === 'object' && !Array.isArray(src.steps) ? src.steps : {},
    sessions: Array.isArray(src.sessions) ? src.sessions : [],
    artifacts: Array.isArray(src.artifacts) ? src.artifacts : [],
  };
}

export function isStepDone(progress, stepId) {
  const s = progress && progress.steps && progress.steps[stepId];
  return !!(s && s.done);
}

export function orderedLabs(labsDoc) {
  const labs = (labsDoc && Array.isArray(labsDoc.labs)) ? labsDoc.labs : [];
  return [...labs].sort((a, b) => (a.number ?? 0) - (b.number ?? 0));
}

/** First step, in lab order, that progress does not mark done. Null when every step is done. */
export function nextStep(labsDoc, progress) {
  for (const lab of orderedLabs(labsDoc)) {
    const steps = Array.isArray(lab.steps) ? lab.steps : [];
    const i = steps.findIndex((s) => !isStepDone(progress, s.id));
    if (i !== -1) return { lab, step: steps[i], index: i + 1, total: steps.length };
  }
  return null;
}

export function labDoneCount(lab, progress) {
  return (lab.steps || []).filter((s) => isStepDone(progress, s.id)).length;
}

export function whereText(where) {
  if (where === 'phone') return 'On your phone. Open the lab document below.';
  return 'At your laptop, type /lab in Claude Code.';
}

export function whereLabel(where) {
  return { laptop: 'Laptop', hosted: 'Hosted service', phone: 'Phone' }[where] || 'Laptop';
}

export function docUrl(lab, step) {
  if (!lab || !lab.doc) return null;
  const anchor = step && step.anchor ? `#${encodeURIComponent(step.anchor)}` : '';
  return `${REPO_BLOB}${lab.doc.split('/').map(encodeURIComponent).join('/')}${anchor}`;
}

/** Sessions in the Monday-to-Sunday Eastern week containing `now`. */
export function weekSessions(progress, now = new Date()) {
  const { start, end } = weekRange(now);
  const inWeek = (progress.sessions || []).filter((s) => {
    const d = toEtDate(s && s.date);
    return d && d >= start && d <= end;
  });
  const minutes = inWeek.reduce((sum, s) => sum + (Number(s.minutes) || 0), 0);
  return { count: inWeek.length, minutes, start, end, target: WEEKLY_TARGET };
}

/** One slot per lab with a public artifact; filled when progress lists one for that lab. */
export function shelf(labsDoc, progress) {
  const slots = orderedLabs(labsDoc)
    .filter((lab) => lab.artifact && lab.artifact.public)
    .map((lab) => {
      const shipped = (progress.artifacts || []).filter((a) => a && a.lab === lab.id);
      return { lab, artifact: shipped.length ? shipped[shipped.length - 1] : null };
    });
  return { slots, filled: slots.filter((s) => s.artifact).length, total: slots.length };
}

/** Only http(s) links are rendered as links. */
export function safeUrl(url) {
  if (typeof url !== 'string') return null;
  try {
    const u = new URL(url);
    return u.protocol === 'https:' || u.protocol === 'http:' ? u.href : null;
  } catch {
    return null;
  }
}
