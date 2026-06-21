/** Shared date parsing helpers for bank statement extractors. */

export const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
export const FULL_MONTHS = [
  "JANUARY",
  "FEBRUARY",
  "MARCH",
  "APRIL",
  "MAY",
  "JUNE",
  "JULY",
  "AUGUST",
  "SEPTEMBER",
  "OCTOBER",
  "NOVEMBER",
  "DECEMBER",
];
export const MONTH_DAY_DATE_RE = new RegExp(`^(${MONTHS.join("|")})\\s+(\\d{1,2})$`, "i");

const MONTH_TO_NUMBER = new Map([
  ...MONTHS.map((m, i) => [m, i + 1]),
  ...FULL_MONTHS.map((m, i) => [m, i + 1]),
]);

export function monthToNumber(monthName) {
  const num = MONTH_TO_NUMBER.get(monthName.toUpperCase());
  if (num === undefined) throw new Error(`Unknown month: ${monthName}`);
  return num;
}

export function monthDayToIso(monthName, day, year) {
  const month = monthToNumber(monthName);
  return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}-${String(parseInt(day, 10)).padStart(2, "0")}`;
}

export function inferYear(meta) {
  if (meta.statement_date) return parseInt(meta.statement_date.slice(0, 4), 10);
  if (meta.statement_period_end) return parseInt(meta.statement_period_end.slice(0, 4), 10);
  return 2024;
}

export function yearForMonthNumber(monthNum, meta) {
  if (meta.statement_period_start && meta.statement_period_end) {
    const startY = parseInt(meta.statement_period_start.slice(0, 4), 10);
    const startM = parseInt(meta.statement_period_start.slice(5, 7), 10);
    const endY = parseInt(meta.statement_period_end.slice(0, 4), 10);
    const endM = parseInt(meta.statement_period_end.slice(5, 7), 10);
    if (startY === endY) return startY;
    if (monthNum >= startM) return startY;
    return endY;
  }
  return inferYear(meta);
}

export function normalizeMonthDayDate(raw, meta) {
  const match = MONTH_DAY_DATE_RE.exec(raw.trim());
  if (!match) return raw.trim();
  const monthNum = monthToNumber(match[1]);
  const day = match[2];
  const year = yearForMonthNumber(monthNum, meta);
  return `${String(year).padStart(4, "0")}-${String(monthNum).padStart(2, "0")}-${String(parseInt(day, 10)).padStart(2, "0")}`;
}
