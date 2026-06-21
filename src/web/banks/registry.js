/** Registry of bank statement extractors. */

import { tdCreditExtractor } from "./td_credit.js";

const EXTRACTORS = {
  [tdCreditExtractor.id]: tdCreditExtractor,
};

export function listExtractors() {
  return Object.values(EXTRACTORS);
}

export function getExtractor(bankId) {
  const extractor = EXTRACTORS[bankId];
  if (!extractor) {
    const known = Object.keys(EXTRACTORS).sort().join(", ");
    throw new Error(`Unknown bank: ${bankId}. Known banks: ${known}`);
  }
  return extractor;
}

export function detectExtractor(pages) {
  for (const extractor of Object.values(EXTRACTORS)) {
    if (extractor.detect(pages)) {
      return extractor;
    }
  }
  return null;
}
