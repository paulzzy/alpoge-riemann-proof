# Shared shell helpers for workflow steps. Source this file.
T="$GITHUB_WORKSPACE/tools"
OUT="$RUNNER_TEMP/out"
mkdir -p "$OUT"

# row "<check>" "<PASS|FAIL|INFO>" "<detail>": add a line to the checks table.
row() {
  printf '| %s | %s | %s |\n' "$1" "$2" "$3" | tee -a "$OUT/checks.md"
  if [ "$2" = "FAIL" ]; then touch "$OUT/failed"; fi
}

# no_build_check "<label>" <lake targets...>: PASS if lake says nothing needs building.
no_build_check() {
  local label="$1"; shift
  if lake build "$@" --no-build > "$OUT/nobuild.log" 2>&1; then
    row "$label" PASS "nothing needed rebuilding"
  else
    row "$label" FAIL "lake wants to rebuild: $(grep -m1 -E 'Building|error' "$OUT/nobuild.log" | tr '|' '/' | cut -c1-160)"
  fi
}
