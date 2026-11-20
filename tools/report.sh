#!/usr/bin/env bash
# Assemble a job's markdown report from the pieces the steps left behind.
# Usage: report.sh "<title>"
set -uo pipefail
OUT="$RUNNER_TEMP/out"
echo "## $1"
echo
if [ -s "$OUT/facts.txt" ]; then
  echo '```'
  cat "$OUT/facts.txt"
  echo '```'
  echo
fi
if [ -s "$OUT/checks.md" ]; then
  echo "| Check | Result | Detail |"
  echo "|---|---|---|"
  cat "$OUT/checks.md"
  echo
else
  echo "No checks ran."
  echo
fi
if [ -s "$OUT/sizes.md" ]; then
  echo "Build output by file type:"
  echo
  cat "$OUT/sizes.md"
  echo
fi
