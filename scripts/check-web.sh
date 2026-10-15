#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

uv run --frozen python scripts/export-openapi.py
npm --prefix web run contracts:generate
git diff --exit-code -- web/openapi.json web/src/api/generated.ts
npm --prefix web run check
