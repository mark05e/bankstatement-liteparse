/**
 * Bank statement transaction extraction from liteparse page data.
 * Use extract() as the single entry point.
 */

import { buildOutput, toCsv } from "./common/output.js";
import { detectExtractor, getExtractor, listExtractors } from "./banks/registry.js";

export { buildOutput, toCsv, detectExtractor, getExtractor, listExtractors };

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
