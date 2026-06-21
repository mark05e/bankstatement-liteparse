#!/usr/bin/env node
/** Compare JS extractor output against Python CLI results in tmp/. */

import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import {
  extractTransactionsFromPages,
  extractMeta,
  buildOutput,
} from "./extract_transactions.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "../..");
const tmp = join(root, "tmp");

const fixtures = [
  { liteparse: "liteparse-output-nov2024.json", expected: "nov2024.transactions.json" },
  { liteparse: "liteparse-output-dec2024.json", expected: "dec2024.transactions.json" },
  { liteparse: "liteparse-output-jan2025.json", expected: "jan2025.transactions.json" },
];

let failed = 0;

for (const { liteparse, expected } of fixtures) {
  const liteparsePath = join(tmp, liteparse);
  const expectedPath = join(tmp, expected);

  let data;
  try {
    data = JSON.parse(readFileSync(liteparsePath, "utf8"));
  } catch (err) {
    if (err.code === "ENOENT") {
      console.log(`SKIP ${liteparse} (file not found)`);
      continue;
    }
    throw err;
  }

  const pages = data.pages;
  const meta = extractMeta(pages);
  const transactions = extractTransactionsFromPages(pages, meta);
  const actual = buildOutput(transactions, meta, liteparsePath);

  let expectedPayload;
  try {
    expectedPayload = JSON.parse(readFileSync(expectedPath, "utf8"));
  } catch (err) {
    if (err.code === "ENOENT") {
      console.log(`SKIP ${expected} (file not found)`);
      continue;
    }
    throw err;
  }

  const errors = [];

  if (actual.transaction_count !== expectedPayload.transaction_count) {
    errors.push(`transaction_count: ${actual.transaction_count} vs ${expectedPayload.transaction_count}`);
  }

  if (actual.account_number !== expectedPayload.account_number) {
    errors.push(`account_number: ${actual.account_number} vs ${expectedPayload.account_number}`);
  }

  if (actual.statement_date !== expectedPayload.statement_date) {
    errors.push(`statement_date: ${actual.statement_date} vs ${expectedPayload.statement_date}`);
  }

  if (actual.statement_period?.start !== expectedPayload.statement_period?.start) {
    errors.push(`period.start: ${actual.statement_period?.start} vs ${expectedPayload.statement_period?.start}`);
  }

  if (actual.statement_period?.end !== expectedPayload.statement_period?.end) {
    errors.push(`period.end: ${actual.statement_period?.end} vs ${expectedPayload.statement_period?.end}`);
  }

  const expTxns = expectedPayload.transactions;
  if (actual.transactions.length !== expTxns.length) {
    errors.push(`transactions length: ${actual.transactions.length} vs ${expTxns.length}`);
  } else {
    for (let i = 0; i < expTxns.length; i++) {
      const a = actual.transactions[i];
      const e = expTxns[i];
      for (const key of ["transaction_date", "posting_date", "description", "amount", "page"]) {
        if (a[key] !== e[key]) {
          errors.push(`txn[${i}].${key}: ${JSON.stringify(a[key])} vs ${JSON.stringify(e[key])}`);
        }
      }
    }
  }

  if (errors.length) {
    console.log(`FAIL ${liteparse}`);
    for (const err of errors.slice(0, 10)) console.log(`  - ${err}`);
    if (errors.length > 10) console.log(`  ... and ${errors.length - 10} more`);
    failed++;
  } else {
    console.log(`PASS ${liteparse} (${actual.transaction_count} transactions)`);
  }
}

if (failed) {
  process.exit(1);
}

console.log("All parity checks passed.");
