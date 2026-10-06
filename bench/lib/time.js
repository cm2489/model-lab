// Eastern Time helpers. Every date the bench shows or counts is Eastern Time
// (America/New_York). Calendar dates are handled as "YYYY-MM-DD" strings and
// moved with UTC arithmetic, so daylight-saving changes never shift a day.

export const TZ = 'America/New_York';

const ymdFormat = new Intl.DateTimeFormat('en-CA', {
  timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit',
});

const YMD = /^\d{4}-\d{2}-\d{2}$/;

/** Eastern calendar date of an instant, as "YYYY-MM-DD". */
export function etDate(when = new Date()) {
  const d = when instanceof Date ? when : new Date(when);
  const parts = {};
  for (const p of ymdFormat.formatToParts(d)) parts[p.type] = p.value;
  return `${parts.year}-${parts.month}-${parts.day}`;
}

/** Move a "YYYY-MM-DD" date by n calendar days. */
export function addDays(ymd, n) {
  const [y, m, d] = ymd.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d + n)).toISOString().slice(0, 10);
}

/** 0 for Monday through 6 for Sunday. */
export function weekdayIndex(ymd) {
  const [y, m, d] = ymd.split('-').map(Number);
  return (new Date(Date.UTC(y, m - 1, d)).getUTCDay() + 6) % 7;
}

/** The Monday-to-Sunday Eastern week that contains `now`. */
export function weekRange(now = new Date()) {
  const today = etDate(now);
  const start = addDays(today, -weekdayIndex(today));
  return { start, end: addDays(start, 6) };
}

/**
 * Turn a date-like value into an Eastern "YYYY-MM-DD".
 * A bare date is taken as already Eastern. A timestamp is converted.
 */
export function toEtDate(value) {
  if (typeof value !== 'string' && !(value instanceof Date)) return null;
  if (typeof value === 'string' && YMD.test(value)) return value;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return etDate(d);
}

/** "Tuesday, October 6, 2026" in Eastern Time. */
export function formatLongDate(now = new Date()) {
  return new Intl.DateTimeFormat('en-US', {
    timeZone: TZ, weekday: 'long', month: 'long', day: 'numeric', year: 'numeric',
  }).format(now);
}

/** "Oct 16" for a "YYYY-MM-DD" (or timestamp) value, Eastern. */
export function formatShortDate(value) {
  const ymd = toEtDate(value);
  if (!ymd) return '';
  const [y, m, d] = ymd.split('-').map(Number);
  return new Intl.DateTimeFormat('en-US', {
    timeZone: 'UTC', month: 'short', day: 'numeric',
  }).format(new Date(Date.UTC(y, m - 1, d)));
}

/** "3:40 PM" in Eastern Time. */
export function formatTime(when) {
  return new Intl.DateTimeFormat('en-US', {
    timeZone: TZ, hour: 'numeric', minute: '2-digit',
  }).format(when instanceof Date ? when : new Date(when));
}
