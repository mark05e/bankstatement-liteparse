# Source layout

Two parallel implementations share the same extraction logic:

| Path | Runtime | Entry point |
|------|---------|-------------|
| `python/` | Python CLI | `extract_transactions.py` |
| `web/` | Browser (WASM + JS) | `index.html`, `extract_transactions.js` |

Each tree has matching `common/` utilities and `banks/` extractors. When adding a bank, implement and register it in **both** trees.

Cross-runtime parity: `node web/validate_parity.mjs` (from repo root: `node src/web/validate_parity.mjs`).
