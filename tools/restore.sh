#!/usr/bin/env bash
# Restore the compiled files of earlier rounds into .lake/build.
# Usage (from the Lean project root): restore.sh <plan.json>
# Needs GH_TOKEN (actions: read) and GITHUB_REPOSITORY.
set -euo pipefail
plan="$1"
: "${GITHUB_REPOSITORY:?}" "${RUNNER_TEMP:?}"
OUT="$RUNNER_TEMP/out"
mkdir -p "$OUT" .lake

python3 -I -c '
import json, sys
for a in json.load(open(sys.argv[1]))["prior"]:
    print(a["run_id"], a["name"])
' "$plan" > "$OUT/prior.txt"

count=0
while read -r run name; do
  dir="$RUNNER_TEMP/restore/$name"
  rm -rf "$dir"
  ok=0
  for attempt in 1 2 3; do
    if gh run download "$run" --repo "$GITHUB_REPOSITORY" --name "$name" --dir "$dir"; then ok=1; break; fi
    rm -rf "$dir"
    sleep $((attempt * 20))
  done
  if [ "$ok" != 1 ]; then echo "could not download $name from run $run"; exit 1; fi
  while IFS= read -r -d '' f; do
    zstd -dc --long=27 "$f" | tar -C .lake -xf -
  done < <(find "$dir" -name '*.tar.zst' -print0 | sort -z)
  rm -rf "$dir"
  count=$((count + 1))
done < "$OUT/prior.txt"

files=0
if [ -d .lake/build/lib/lean ]; then files=$(find .lake/build/lib/lean -name '*.olean' | wc -l); fi
echo "restored $count artifact(s): $files compiled files, $(du -sm .lake/build 2>/dev/null | cut -f1 || echo 0) MB" | tee "$OUT/restore.txt"
