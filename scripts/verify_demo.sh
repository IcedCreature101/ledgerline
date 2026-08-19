#!/usr/bin/env bash
# Is this checkout a valid demo baseline?
#
# Two things have to be true at once, and they pull in opposite directions:
#   1. the SHIPPED suite is green   — the bugs are hidden from anyone who just runs the tests
#   2. every HELD-OUT test fails    — the bugs are all actually present
#
# A checkout where (1) fails is broken. A checkout where (2) fails has had a defect fixed already, and a
# demo run against it will find nothing.
#
# The verdict is pytest's EXIT CODE, not its output: reading "failed" out of a summary line matches the
# word in "FAILED tests/..." too, which reports a green suite as broken and a fixed bug as still present.
set -uo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
QUIET="${1:-}"
fail=0

$PY -m pytest tests/ -q -p no:cacheprovider >/tmp/ll_shipped.log 2>&1
if [ $? -ne 0 ]; then
  echo "SHIPPED SUITE IS NOT GREEN — the bugs are not hidden:"; tail -5 /tmp/ll_shipped.log; fail=1
else
  [ "$QUIET" = "--quiet" ] || echo "shipped suite: $(tail -1 /tmp/ll_shipped.log)"
fi

for f in .demo/gold/test_*.py; do
  $PY -m pytest "$f" -q -p no:cacheprovider >/tmp/ll_gold.log 2>&1
  if [ $? -ne 0 ]; then
    [ "$QUIET" = "--quiet" ] || printf "  reproduces   %-46s %s\n" "$(basename "$f")" \
      "$(grep -oE '[0-9]+ failed[^|]*' /tmp/ll_gold.log | tail -1)"
  else
    printf "  NOT PRESENT  %-46s (this defect is already fixed here)\n" "$(basename "$f")"; fail=1
  fi
done

[ $fail -eq 0 ] && [ "$QUIET" = "--quiet" ] && exit 0
[ $fail -eq 0 ] && echo "baseline is armed: shipped suite green, all 8 defects present"
exit $fail
