/**
 * Bank statement transaction extraction from liteparse page data.
 * Re-exports TD extractor functions for backward compatibility.
 */

import { buildOutput, toCsv } from "./common/output.js";
import { tdCreditExtractor } from "./banks/td_credit.js";
import { detectExtractor, getExtractor, listExtractors } from "./banks/registry.js";

export { buildOutput, toCsv, detectExtractor, getExtractor, listExtractors };

/** @deprecated Use getExtractor("td_credit") or detectExtractor() */
export function extractMeta(pages) {
  return tdCreditExtractor.extractMeta(pages);
}

/** @deprecated Use getExtractor("td_credit") or detectExtractor() */
export function extractTransactionsFromPages(pages, meta = null) {
  return tdCreditExtractor.extractTransactions(pages, meta);
}

/**
 * Extract transactions using auto-detected or specified bank extractor.
 */
export function extract(pages, { bankId = null } = {}) {
  const extractor = bankId ? getExtractor(bankId) : detectExtractor(pages);
  if (!extractor) {
    const known = listExtractors().map((e) => e.id).join(", ");
    throw new Error(`Could not detect bank from statement. Known banks: ${known}`);
  }
  const meta = extractor.extractMeta(pages);
  const transactions = extractor.extractTransactions(pages, meta);
  return {
    extractor,
    meta,
    transactions,
    payload: buildOutput(transactions, meta, null, {
      bankId: extractor.id,
      bankName: extractor.name,
    }),
  };
}
