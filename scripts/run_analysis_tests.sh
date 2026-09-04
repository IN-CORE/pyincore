#!/usr/bin/env bash
# Run each tests/pyincore/analyses/*/test_*.py as a plain Python script.
#
# Usage:
#   ./scripts/run_analysis_tests.sh
#   ./scripts/run_analysis_tests.sh bridgedamage buildingdamage
#   ./scripts/run_analysis_tests.sh --log logs/analysis_tests.log
#   ./scripts/run_analysis_tests.sh --stop-on-fail
#
# Notes:
#   - buildingdamage only runs test_buildingdamage_multihazard.py
#   - username/password prompts stay on your real terminal (TTY preserved)
#   - --log uses `script` so prompts still surface while output is recorded
#
# Requires: conda/env with pyincore; IN-CORE credentials (.incorepw) optional.

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANALYSES_DIR="${ROOT_DIR}/tests/pyincore/analyses"
STOP_ON_FAIL=0
LOG_FILE=""
FILTERS=()
REEXEC_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stop-on-fail|-x)
      STOP_ON_FAIL=1
      REEXEC_ARGS+=("$1")
      shift
      ;;
    --log)
      LOG_FILE="$2"
      REEXEC_ARGS+=("--log" "$2")
      shift 2
      ;;
    --_logging)
      # internal: already running under script(1)
      shift
      ;;
    -h|--help)
      sed -n '2,16p' "$0"
      exit 0
      ;;
    *)
      FILTERS+=("$1")
      REEXEC_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ ! -d "${ANALYSES_DIR}" ]]; then
  echo "ERROR: analyses test dir not found: ${ANALYSES_DIR}" >&2
  exit 1
fi

# Re-exec under script(1) so logging keeps a real TTY for input()/getpass()
if [[ -n "${LOG_FILE}" && -z "${_ANALYSIS_TESTS_UNDER_SCRIPT:-}" ]]; then
  mkdir -p "$(dirname "${LOG_FILE}")"
  export _ANALYSIS_TESTS_UNDER_SCRIPT=1
  echo "Logging to ${LOG_FILE} (TTY preserved for username/password prompts)"
  exec script -q "${LOG_FILE}" /bin/bash "$0" --_logging "${REEXEC_ARGS[@]}"
fi

cd "${ROOT_DIR}"

# Return newline-separated script paths for one analysis directory.
# buildingdamage is limited to the multihazard script only.
list_scripts_for_analysis() {
  local name="$1"
  local dir="$2"

  if [[ "${name}" == "buildingdamage" ]]; then
    local only="${dir}/test_buildingdamage_multihazard.py"
    if [[ -f "${only}" ]]; then
      printf '%s\n' "${only}"
    fi
    return 0
  fi

  local f
  shopt -s nullglob
  for f in "${dir}"/test_*.py; do
    printf '%s\n' "${f}"
  done
  shopt -u nullglob
}

DIRS=()
if [[ ${#FILTERS[@]} -gt 0 ]]; then
  for name in "${FILTERS[@]}"; do
    if [[ ! -d "${ANALYSES_DIR}/${name}" ]]; then
      echo "ERROR: unknown analysis: ${name}" >&2
      exit 1
    fi
    DIRS+=("${name}")
  done
else
  for d in "${ANALYSES_DIR}"/*/; do
    [[ -d "$d" ]] || continue
    name="$(basename "$d")"
    if [[ -n "$(list_scripts_for_analysis "${name}" "${d%/}")" ]]; then
      DIRS+=("${name}")
    fi
  done
  IFS=$'\n' DIRS=($(printf '%s\n' "${DIRS[@]}" | sort))
  unset IFS
fi

PASSED=()
FAILED=()
SKIPPED=()

echo "Running analysis scripts under ${ANALYSES_DIR}"
echo "Note: buildingdamage -> test_buildingdamage_multihazard.py only"
echo

for name in "${DIRS[@]}"; do
  dir="${ANALYSES_DIR}/${name}"

  scripts=()
  while IFS= read -r script; do
    [[ -n "${script}" ]] || continue
    scripts+=("${script}")
  done < <(list_scripts_for_analysis "${name}" "${dir}")

  if [[ ${#scripts[@]} -eq 0 ]]; then
    echo "========== SKIP ${name} (no matching test_*.py) =========="
    SKIPPED+=("${name}")
    echo
    continue
  fi

  echo "========== ${name} =========="
  analysis_ok=1
  for script in "${scripts[@]}"; do
    echo "--- python $(basename "${script}") ---"
    # Keep stdin on the real TTY so username/password prompts surface
    if ! (
      cd "${dir}"
      python "$(basename "${script}")" </dev/tty
    ); then
      analysis_ok=0
      FAILED+=("${name}/$(basename "${script}")")
      if [[ "${STOP_ON_FAIL}" -eq 1 ]]; then
        echo
        echo "Stopped on first failure (--stop-on-fail)."
        echo "==================== SUMMARY ===================="
        echo "Passed analyses: ${#PASSED[@]}"
        echo "Failed scripts:  ${#FAILED[@]}"
        printf '  - %s\n' "${FAILED[@]}"
        exit 1
      fi
    fi
    echo
  done

  if [[ "${analysis_ok}" -eq 1 ]]; then
    PASSED+=("${name}")
  fi
  echo
done

echo "==================== SUMMARY ===================="
echo "Passed analyses: ${#PASSED[@]}"
echo "Failed scripts:  ${#FAILED[@]}"
echo "Skipped:         ${#SKIPPED[@]}"
if [[ -n "${LOG_FILE}" ]]; then
  echo "Log file:        ${LOG_FILE}"
fi

if [[ ${#FAILED[@]} -gt 0 ]]; then
  echo
  echo "Failed scripts:"
  for item in "${FAILED[@]}"; do
    echo "  - ${item}"
  done
  exit 1
fi

exit 0
