#!/usr/bin/env bash
# Download the archive, check its SHA-256 and extract it to $GITHUB_WORKSPACE/x.
set -euo pipefail
: "${ARCHIVE_BASE:?}" "${ARCHIVE_PARTS:?}" "${ARCHIVE_SHA256:?}"
: "${RUNNER_TEMP:?}" "${GITHUB_WORKSPACE:?}"

mkdir -p "$RUNNER_TEMP/dl" "$RUNNER_TEMP/out" "$GITHUB_WORKSPACE/x"
cd "$RUNNER_TEMP/dl"
for i in $(seq -w 1 "$ARCHIVE_PARTS"); do
  curl -fsSL --retry 5 --retry-delay 10 --retry-all-errors -O "${ARCHIVE_BASE}${i}"
done
echo "${ARCHIVE_SHA256}  -" > expected.sha256
cat lean.tar.gz.part?? | sha256sum -c expected.sha256
cat lean.tar.gz.part?? | tar xzf - -C "$GITHUB_WORKSPACE/x" --no-same-owner --no-same-permissions
cd "$GITHUB_WORKSPACE"
rm -rf "$RUNNER_TEMP/dl"
echo "lean files: $(find x/lean/src -name '*.lean' | wc -l)"
