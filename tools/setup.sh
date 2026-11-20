#!/usr/bin/env bash
# Prepare a runner: download the archive, check its SHA-256, extract it,
# install Lean, fetch prebuilt Mathlib and confirm the Mathlib pin.
set -euo pipefail
: "${MATHLIB_REV:?}" "${RUNNER_TEMP:?}" "${GITHUB_WORKSPACE:?}" "${GITHUB_PATH:?}"

sudo rm -rf /usr/share/dotnet /usr/local/lib/android /opt/ghc /opt/hostedtoolcache/CodeQL /usr/local/share/boost || true
command -v zstd > /dev/null || { sudo apt-get update -qq && sudo apt-get install -y -qq zstd; }

bash "$(dirname "$0")/fetch.sh"
cd "$GITHUB_WORKSPACE/x/lean"

curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none
echo "$HOME/.elan/bin" >> "$GITHUB_PATH"
export PATH="$HOME/.elan/bin:$PATH"
lean --version

lake exe cache get
got="$(git -C .lake/packages/mathlib rev-parse HEAD)"
echo "mathlib at $got"
test "$got" = "$MATHLIB_REV"
test -z "$(git -C .lake/packages/mathlib status --porcelain)"
# Stop if the prebuilt Mathlib is incomplete; building it here would take hours.
lake build +Mathlib --no-build

{
  echo "runner: $(nproc) cores, $(free -g | awk '/^Mem:/ {print $2}') GB RAM, $(df -BG --output=avail / | tail -1 | tr -d ' ') free disk"
  echo "lean: $(lean --version)"
  echo "mathlib: $got (clean checkout, prebuilt cache complete)"
  echo "archive sha256: $ARCHIVE_SHA256"
} > "$RUNNER_TEMP/out/facts.txt"
cat "$RUNNER_TEMP/out/facts.txt"
