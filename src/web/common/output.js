/** Output formatting shared across bank extractors. */

export function buildOutput(transactions, meta, source, { bankId = null, bankName = null } = {}) {
  const payload = {
    source,
    account_number: meta.account_number,
    statement_date: meta.statement_date,
    statement_period: {
      start: meta.statement_period_start,
      end: meta.statement_period_end,
    },
    transaction_count: transactions.length,
    transactions,
  };
  if (bankId !== null) payload.bank_id = bankId;
  if (bankName !== null) payload.bank_name = bankName;
  return payload;
}

export function toCsv(transactions) {
  const fieldnames = ["transaction_date", "posting_date", "description", "amount", "page"];
  const escape = (value) => {
    const str = String(value);
    if (str.includes(",") || str.includes('"') || str.includes("\n")) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };
  const lines = [fieldnames.join(",")];
  for (const txn of transactions) {
    lines.push(fieldnames.map((key) => escape(txn[key])).join(","));
  }
  return lines.join("\n") + "\n";
}
