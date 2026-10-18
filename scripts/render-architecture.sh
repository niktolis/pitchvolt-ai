#!/usr/bin/env bash
# Single D2 rendering entrypoint for local development and CI.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="$ROOT/docs/architecture/diagrams"
SVG_DIR="$ROOT/docs/architecture/rendered"
EXPORT_DIR="$ROOT/build/architecture"
MODE="render"
LAYOUT="${D2_LAYOUT:-elk}"

usage() {
  cat <<'HELP'
Usage: bash scripts/render-architecture.sh [--check | --export | --all]
  (default)  validate all D2 sources and regenerate Markdown-embedded SVGs
  --check    validate sources and check generated SVGs are up to date
  --export   generate PDF/PPTX exports in build/architecture (and SVGs)
  --all      same as --export
Environment: D2_LAYOUT (default: elk)
Requires: d2 CLI; for --check, diff.
HELP
}

if [[ $# -gt 1 ]]; then usage >&2; exit 2; fi
case "${1:-}" in
  "") ;;
  --check) MODE="check" ;;
  --export|--all) MODE="export" ;;
  --help|-h) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

D2_REQUIRED_VERSION="v0.9.0"
if ! command -v d2 >/dev/null 2>&1; then
  echo "D2 CLI is required. On macOS: brew install d2" >&2
  exit 127
fi

actual_version="$(d2 --version)"
if [[ "$actual_version" != "$D2_REQUIRED_VERSION" ]]; then
  echo "D2 version mismatch: expected $D2_REQUIRED_VERSION, got $actual_version" >&2
  exit 1
fi

shopt -s nullglob
sources=("$SOURCE_DIR"/*.d2)
if [[ ${#sources[@]} -eq 0 ]]; then
  echo "No D2 diagrams found under $SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$SVG_DIR"
if [[ "$MODE" == "export" ]]; then mkdir -p "$EXPORT_DIR"; fi

for source in "${sources[@]}"; do
  name="$(basename "$source" .d2)"
  output="$SVG_DIR/$name.svg"
  echo "Validating $name.d2"
  d2 validate "$source"
  if [[ "$MODE" == "check" ]]; then
    temp="$(mktemp "${TMPDIR:-/tmp}/pitchvolt-d2.XXXXXXXX.svg")"
    trap 'rm -f "$temp"' EXIT
    d2 --layout="$LAYOUT" "$source" "$temp"
    if [[ ! -f "$output" ]] || ! cmp -s "$temp" "$output"; then
      echo "Stale or missing render: $output. Run: bash scripts/render-architecture.sh" >&2
      exit 1
    fi
    rm -f "$temp"
    trap - EXIT
  else
    d2 --layout="$LAYOUT" "$source" "$output"
  fi
  if [[ "$MODE" == "export" ]]; then
    d2 --layout="$LAYOUT" "$source" "$EXPORT_DIR/$name.pdf"
    d2 --layout="$LAYOUT" "$source" "$EXPORT_DIR/$name.pptx"
  fi
done
echo "Architecture diagrams: ${#sources[@]} validated; mode=$MODE"
