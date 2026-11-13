#!/bin/bash
# Run the end-to-end analysis tests under tests/pyincore/analyses.
#
# These are NOT pytest tests. 81 of 86 are plain scripts guarded by
# `if __name__ == "__main__"`, and the mlenabledcge* ones run at module import.
# Only a few define a collectable `def test_*`, and those carry a __main__ guard
# too, so every file is executed the same way, from its own directory (the tests
# resolve data files relative to the cwd), via run_analysis_script.py - which
# turns a run_analysis() that returns False into a non-zero exit.
#
# usage: run_analyses_tests.sh <targets> [log-dir]
#
#   targets   space/comma separated analysis directory names (e.g. "indp joplincge"),
#             test file paths, or "all"
#   log-dir   where per-test logs and summary.tsv are written (default: analyses-logs)
#
# Exits non-zero if any test failed.

set -u

TARGETS="${1:-all}"
LOG_DIR="${2:-analyses-logs}"
TEST_ROOT="tests/pyincore/analyses"
# Per-test wall-clock cap, in seconds. Some CGE/INDP runs legitimately take tens
# of minutes, so this is generous.
TEST_TIMEOUT="${TEST_TIMEOUT_SECONDS:-3600}"
RUNNER_SHIM="$(cd "$(dirname "$0")" && pwd)/run_analysis_script.py"

if [ ! -d "$TEST_ROOT" ]; then
  echo "error: $TEST_ROOT not found; run this from the repository root" >&2
  exit 2
fi

mkdir -p "$LOG_DIR"
SUMMARY="$LOG_DIR/summary.tsv"
printf "status\trc\tseconds\ttest\n" > "$SUMMARY"

# Collect the test files to run.
files=""
if [ "$TARGETS" = "all" ]; then
  files=$(find "$TEST_ROOT" -name 'test_*.py' | sort)
else
  for target in $(echo "$TARGETS" | tr ',' ' '); do
    if [ -f "$target" ]; then
      found="$target"
    elif [ -d "$TEST_ROOT/$target" ]; then
      found=$(find "$TEST_ROOT/$target" -name 'test_*.py' | sort)
    else
      echo "error: no tests found for target '$target'" >&2
      exit 2
    fi
    files="$files $found"
  done
fi

files=$(echo "$files" | tr ' ' '\n' | grep -v '^$' | sort -u)
total=$(echo "$files" | grep -c .)
if [ "$total" -eq 0 ]; then
  echo "error: no test files selected" >&2
  exit 2
fi
echo "Running $total analysis test(s), timeout ${TEST_TIMEOUT}s each"

failed=0
for f in $files; do
  key=$(echo "$f" | sed "s|$TEST_ROOT/||; s|/|__|g; s|\.py$||")
  log="$LOG_DIR/$key.log"
  start=$SECONDS
  # `timeout` is not on macOS by default; perl's alarm is portable enough.
  ( cd "$(dirname "$f")" \
      && perl -e 'alarm shift; exec @ARGV' "$TEST_TIMEOUT" \
           python "$RUNNER_SHIM" "$(basename "$f")" ) > "$log" 2>&1
  rc=$?
  dur=$((SECONDS - start))
  if [ "$rc" -eq 0 ]; then
    status="PASS"
  else
    status="FAIL"
    failed=$((failed + 1))
  fi
  printf "%s\t%s\t%s\t%s\n" "$status" "$rc" "$dur" "$f" >> "$SUMMARY"
  echo "[$status rc=$rc ${dur}s] $f"
  if [ "$rc" -ne 0 ]; then
    echo "----- last 40 lines of $log -----"
    tail -40 "$log"
    echo "---------------------------------"
  fi
done

echo
echo "$((total - failed))/$total passed"
[ "$failed" -eq 0 ]
