#!/usr/bin/env bash
# Put the repository back to the buggy baseline so the same demo can be run again.
#
# The demo is destructive by design: agents open branches, PRs get merged into main, and the defect the
# next run is supposed to find is no longer there. `demo-baseline` is an immutable tag on the original
# buggy tree, and this restores main to it.
#
#   ./scripts/reset_demo.sh              # restore main locally
#   ./scripts/reset_demo.sh --push       # and force it on the remote (the demo repo, nobody else's work)
#   ./scripts/reset_demo.sh --check      # just report whether the baseline is intact
set -euo pipefail
cd "$(dirname "$0")/.."

TAG="${DEMO_BASELINE_TAG:-demo-baseline}"
REMOTE="${DEMO_REMOTE:-origin}"

git rev-parse -q --verify "refs/tags/$TAG" >/dev/null || {
  echo "no $TAG tag in this clone — fetch it first:  git fetch $REMOTE --tags"; exit 1; }

if [ "${1:-}" = "--check" ]; then
  echo "baseline  $TAG -> $(git rev-parse --short "$TAG")"
  echo "main      $(git rev-parse --short main 2>/dev/null || echo '(absent)')"
  if [ "$(git rev-parse "$TAG")" = "$(git rev-parse main 2>/dev/null || echo x)" ]; then
    echo "main IS the baseline — the demo is armed"
  else
    echo "main has moved off the baseline — run without --check to restore it"
  fi
  exit 0
fi

git checkout -q main 2>/dev/null || git checkout -q -b main "$TAG"
git reset --hard -q "$TAG"
git clean -qfd -e .venv -e '*.egg-info'
echo "main restored to $TAG ($(git rev-parse --short "$TAG"))"

# The agent branches from previous runs pile up; a run reuses a branch by name, so stale ones confuse
# the next demo more than they help.
for b in $(git branch --list 'agent_fix/*' --format='%(refname:short)'); do
  git branch -qD "$b" && echo "  removed stale branch $b"
done

if [ "${1:-}" = "--push" ]; then
  git push -q --force-with-lease "$REMOTE" main
  echo "pushed main to $REMOTE"
fi

echo
echo "verifying the baseline is genuinely buggy…"
./scripts/verify_demo.sh --quiet && echo "ARMED — 8 tickets reproduce, shipped suite green"
