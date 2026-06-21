/** TD Bank credit card statement extractor. */

import { clusterRows, parseAmount, rowFields } from "../common/clustering.js";
import {
  MONTH_DAY_DATE_RE,
  monthDayToIso,
  normalizeMonthDayDate,
} from "../common/dates.js";

const SKIP_DESCRIPTIONS = new Set([
  "PREVIOUS STATEMENT BALANCE",
  "TOTAL NEW BALANCE",
  "Continued",
]);
const STATEMENT_DATE_RE = /STATEMENT\s+DATE:\s+(\w+)\s+(\d{1,2}),\s+(\d{4})/i;
const STATEMENT_PERIOD_RE =
  /STATEMENT\s+PERIOD:\s+(\w+)\s+(\d{1,2}),\s+(\d{4})\s+to\s+(\w+)\s+(\d{1,2}),\s+(\d{4})/i;
const ACCOUNT_RE = /(\d{4}\s+\d{2}XX\s+XXXX\s+\d{4})/;
const AMOUNT_RE = /^-?\$[\d,]+\.\d{2}$/;

const COLUMNS = [
  ["txn_date", 40, 85],
  ["post_date", 85, 130],
  ["description", 130, 300],
  ["amount", 300, 360],
];
const LEFT_PANEL_MAX_X = 360;
const ROW_CLUSTER_TOLERANCE = 6.0;
const MAX_DESCRIPTION_GAP = 35.0;
const TRANSACTION_PAGE_MARKER = "TRANSACTION POSTING";

export const tdCreditExtractor = {
  id: "td_credit",
  name: "TD Credit Card",

  detect(pages) {
    for (const page of pages) {
      const text = page.text || "";
      if (text.includes(TRANSACTION_PAGE_MARKER) && ACCOUNT_RE.test(text)) {
        return true;
      }
    }
    return false;
  },

  extractMeta(pages) {
    const meta = {
      account_number: null,
      statement_date: null,
      statement_period_start: null,
      statement_period_end: null,
    };

    for (const page of pages) {
      const text = page.text || "";
      if (!meta.statement_date) {
        const match = STATEMENT_DATE_RE.exec(text);
        if (match) {
          meta.statement_date = monthDayToIso(match[1], match[2], parseInt(match[3], 10));
        }
      }
      if (!meta.statement_period_start) {
        const match = STATEMENT_PERIOD_RE.exec(text);
        if (match) {
          const startYear = parseInt(match[3], 10);
          const endYear = parseInt(match[6], 10);
          meta.statement_period_start = monthDayToIso(match[1], match[2], startYear);
          meta.statement_period_end = monthDayToIso(match[4], match[5], endYear);
        }
      }
      if (!meta.account_number) {
        const match = ACCOUNT_RE.exec(text);
        if (match) {
          meta.account_number = match[1];
        }
      }
      if (meta.statement_date && meta.statement_period_start && meta.account_number) {
        break;
      }
    }

    return meta;
  },

  extractTransactions(pages, meta = null) {
    meta = meta || this.extractMeta(pages);
    const transactions = [];
    let pending = null;

    const flushPending = () => {
      if (pending) {
        transactions.push(pending.transaction);
        pending = null;
      }
    };

    for (const page of pages) {
      const pageNum = page.page;
      if (!(page.text || "").includes(TRANSACTION_PAGE_MARKER)) continue;

      const leftItems = (page.text_items || []).filter((item) => item.x < LEFT_PANEL_MAX_X);
      for (const cluster of clusterRows(leftItems, ROW_CLUSTER_TOLERANCE)) {
        const fields = rowFields(cluster, COLUMNS);
        const txnRaw = fields.txn_date;
        const postRaw = fields.post_date;
        const description = fields.description;
        const amountRaw = fields.amount;

        if (txnRaw && MONTH_DAY_DATE_RE.test(txnRaw) && amountRaw && AMOUNT_RE.test(amountRaw)) {
          const desc = description || "";
          if (SKIP_DESCRIPTIONS.has(desc.toUpperCase())) {
            flushPending();
            continue;
          }

          flushPending();
          pending = {
            transaction: {
              transaction_date: normalizeMonthDayDate(txnRaw, meta),
              posting_date: normalizeMonthDayDate(postRaw || txnRaw, meta),
              description: desc,
              amount: parseAmount(amountRaw),
              page: pageNum,
            },
            anchor_y: cluster.y_ref,
          };
          continue;
        }

        if (
          pending &&
          pending.transaction.page === pageNum &&
          description &&
          !txnRaw &&
          !amountRaw &&
          cluster.y_ref - pending.anchor_y <= MAX_DESCRIPTION_GAP
        ) {
          pending.transaction.description = `${pending.transaction.description} ${description}`.trim();
          pending.anchor_y = cluster.y_ref;
        }
      }
    }

    flushPending();
    return transactions;
  },
};
