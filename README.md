# Bank Statement LiteParse

Extract structured credit card transactions from bank statement PDFs. Parsing uses [LiteParse](https://github.com/run-llama/liteparse) for spatial text extraction; bank-specific logic maps that text into transaction rows.

**Live demo:** [mark05e.github.io/bankstatement-liteparse](https://mark05e.github.io/bankstatement-liteparse/)

**Currently supported:** TD credit card statements (`td_credit`). The codebase is modular so additional banks can be added under `src/python/banks/` and `src/web/banks/`.

## Requirements

| Tool | Requirements |
|------|----------------|
| Python CLI | Python 3.10+, `liteparse` package |
| Web UI | A local HTTP server and a modern browser (Chrome, Firefox, Edge). No Node.js or build step required. |

## Python CLI

### Install

```bash
pip install liteparse
```

### Run

From the project root:

```bash
python src/python/extract_transactions.py path/to/statement.pdf
```

This auto-detects the bank, parses the PDF, and writes two files next to the input (or use `--json` / `--csv` to set paths):

- `statement.transactions.json` — full payload with metadata and transactions
- `statement.transactions.csv` — flat transaction table

### Examples

Auto-detect bank from statement content:

```bash
python src/python/extract_transactions.py statement.pdf
```

Specify the bank explicitly:

```bash
python src/python/extract_transactions.py statement.pdf --bank td_credit
```

Custom output paths:

```bash
python src/python/extract_transactions.py statement.pdf --json out/transactions.json --csv out/transactions.csv
```

Re-run extraction from an existing LiteParse JSON file (skip PDF parsing):

```bash
python src/python/extract_transactions.py tmp/liteparse-output-nov2024.json
```

Show LiteParse progress while parsing:

```bash
python src/python/extract_transactions.py statement.pdf --verbose
```

### CLI options

| Option | Description |
|--------|-------------|
| `input` | PDF path, or an existing LiteParse JSON file |
| `--bank` | Bank extractor ID (default: auto-detect). Currently: `td_credit` |
| `--json` | Output JSON path |
| `--csv` | Output CSV path |
| `--verbose` | Show LiteParse parsing progress |

## Web UI

The web app runs entirely in the browser: LiteParse WASM (loaded from CDN) parses the PDF, then JavaScript extractors produce the same JSON/CSV output as the Python CLI.

**Try it online:** [https://mark05e.github.io/bankstatement-liteparse/](https://mark05e.github.io/bankstatement-liteparse/)

### Run locally

ES modules and WASM require HTTP — `file://` URLs will not work.

```bash
cd src/web
echo "Open http://localhost:8080"
python -m http.server 8080
```

One-liner:

```bash
cd src/web && echo "Open http://localhost:8080" && python -m http.server 8080
```

### Use the UI

1. Wait for the status line to show **Ready** (WASM loads from jsDelivr on first visit).
2. Drop one or more statement PDFs onto the drop zone, or click to choose files.
3. Watch the progress bar and file queue as each PDF is parsed sequentially.
4. Click a completed file in the queue to view its metadata and transaction table.
5. Download **JSON** or **CSV** for the currently selected file.
6. After a batch finishes, use **Download all JSON (ZIP)** or **Download all CSV (ZIP)** to export every successful file at once.
7. Optionally expand **Show raw LiteParse JSON** for debugging.

Non-PDF files in a drop are skipped with a warning. If one PDF in a batch fails, the rest still process; failed files show an error badge in the queue and are omitted from ZIP downloads.

The status line reports batch completion and which bank extractor was detected (e.g. `TD Credit Card`).

## Output format

JSON output includes statement metadata and a transaction list:

```json
{
  "source": "statement.pdf",
  "bank_id": "td_credit",
  "bank_name": "TD Credit Card",
  "account_number": "4520 88XX XXXX 9902",
  "statement_date": "2024-11-27",
  "statement_period": {
    "start": "2024-11-04",
    "end": "2024-11-27"
  },
  "transaction_count": 20,
  "transactions": [
    {
      "transaction_date": "2024-11-15",
      "posting_date": "2024-11-18",
      "description": "UBER CANADA/UBEREATS TORONTO",
      "amount": 79.46,
      "page": 1
    }
  ]
}
```

CSV columns: `transaction_date`, `posting_date`, `description`, `amount`, `page`.

## Validate JS/Python parity

If you have fixture files in `tmp/`, you can confirm the JavaScript extractor matches the Python CLI:

```bash
node src/web/validate_parity.mjs
```

This compares JS output against `tmp/*.transactions.json` files produced by the Python tool.

## Project layout

```
src/
  python/
    extract_transactions.py # Python CLI entry point
    common/                 # Shared types, dates, clustering, output, PDF loading
    banks/
      base.py               # BankExtractor interface
      td_credit.py          # TD credit card extractor
      registry.py           # Bank registration and auto-detection
  web/
    index.html              # Browser UI
    extract_transactions.js # JS entry point and re-exports
    common/                 # Shared JS utilities (output, liteparse, batch)
    banks/                  # Bank-specific JS extractors
    validate_parity.mjs     # Parity test script
```

## Adding a new bank

1. Implement `BankExtractor` in `src/python/banks/your_bank.py` (`detect`, `extract_meta`, `extract_transactions`).
2. Register it in `src/python/banks/registry.py`.
3. Port the same logic to `src/web/banks/your_bank.js` and register in `src/web/banks/registry.js`.

Shared logic (date normalization, row clustering, amount parsing, output formatting) lives in each tree's `common/` folder and should be reused rather than duplicated in each bank module.
