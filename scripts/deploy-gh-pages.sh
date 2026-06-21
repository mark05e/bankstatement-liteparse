#!/usr/bin/env bash
# Deploy src/web to the gh-pages branch (GitHub Pages).
# Usage (from repo root): ./scripts/deploy-gh-pages.sh
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

if [[ ! -f src/web/index.html ]]; then
  echo "Expected src/web/index.html — run this script from the repository root." >&2
  exit 1
fi

echo "Pushing src/web to origin/gh-pages via git subtree..."
git subtree push --prefix src/web origin gh-pages

echo ""
echo "Done. Site URL (after GitHub Pages is enabled):"
echo "  https://mark05e.github.io/bankstatement-liteparse/"
