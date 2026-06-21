# Bank Statement LiteParse

Extract structured credit card transactions from bank statement PDFs. Parsing uses [LiteParse](https://github.com/run-llama/liteparse) for spatial text extraction; bank-specific logic maps that text into transaction rows.

**Currently supported:** TD credit card statements (`td_credit`). The codebase is modular so additional banks can be added under `src/banks/` and `src/web/banks/`.

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
python src/extract_transactions.py path/to/statement.pdf
```

This auto-detects the bank, parses the PDF, and writes two files next to the input (or use `--json` / `--csv` to set paths):

- `statement.transactions.json` — full payload with metadata and transactions
- `statement.transactions.csv` — flat transaction table

### Examples

Auto-detect bank from statement content:

```bash
python src/extract_transactions.py statement.pdf
```

Specify the bank explicitly:

```bash
python src/extract_transactions.py statement.pdf --bank td_credit
```

Custom output paths:

```bash
python src/extract_transactions.py statement.pdf --json out/transactions.json --csv out/transactions.csv
```

Re-run extraction from an existing LiteParse JSON file (skip PDF parsing):

```bash
python src/extract_transactions.py tmp/liteparse-output-nov2024.json
```

Show LiteParse progress while parsing:

```bash
python src/extract_transactions.py statement.pdf --verbose
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

### Run locally

ES modules and WASM require HTTP — `file://` URLs will not work.

```bash
cd src/web
python -m http.server 8080
```

Open [http://localhost:8080](http://localhost:8080) in your browser.

### Use the UI

1. Wait for the status line to show **Ready** (WASM loads from jsDelivr on first visit).
2. Drop a statement PDF onto the drop zone, or click to choose a file.
3. View statement metadata and the transaction table.
4. Download **JSON** or **CSV** with the download buttons.
5. Optionally expand **Show raw LiteParse JSON** for debugging.

The status line reports which bank extractor was detected (e.g. `TD Credit Card`).

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
  extract_transactions.py   # Python CLI entry point
  common/                   # Shared types, dates, clustering, output, PDF loading
  banks/
    base.py                 # BankExtractor interface
    td_credit.py            # TD credit card extractor
    registry.py             # Bank registration and auto-detection
  web/
    index.html              # Browser UI
    extract_transactions.js # JS entry point and re-exports
    common/                 # Shared JS utilities
    banks/                  # Bank-specific JS extractors
    validate_parity.mjs       # Parity test script
```

## Adding a new bank

1. Implement `BankExtractor` in `src/banks/your_bank.py` (`detect`, `extract_meta`, `extract_transactions`).
2. Register it in `src/banks/registry.py`.
3. Port the same logic to `src/web/banks/your_bank.js` and register in `src/web/banks/registry.js`.

Shared logic (date normalization, row clustering, amount parsing, output formatting) lives in `common/` and should be reused rather than duplicated in each bank module.
