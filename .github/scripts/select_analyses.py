"""Work out which analyses the analyses-tests workflow should run.

Prints a GitHub Actions matrix (a JSON list of {"analysis", "tests"} entries)
plus a human-readable reason, on stdout as `name=value` lines suitable for
$GITHUB_OUTPUT.

usage: select_analyses.py <scope> [argument]

  all              every analysis directory that contains test_*.py
  select  <list>   comma/space separated analysis names
  changed <range>  analyses touched by a git diff range, e.g. origin/develop...HEAD
"""

import json
import os
import subprocess
import sys
from pathlib import Path

TEST_ROOT = Path("tests/pyincore/analyses")
CODE_ROOT = Path("pyincore/analyses")

# A few analysis packages don't share a name with their test directory.
CODE_TO_TEST_DIR = {
    "buildingnonstructuraldamage": "buildingnonstructdamage",
    "joplincgeanalysis": "joplincge",
}


def all_analyses():
    return sorted(
        d.name for d in TEST_ROOT.iterdir() if d.is_dir() and any(d.glob("test_*.py"))
    )


def changed_analyses(diff_range):
    files = subprocess.run(
        ["git", "diff", "--name-only", diff_range],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()

    known = set(all_analyses())
    selected, core_touched = set(), []
    for f in files:
        path = Path(f)
        parts = path.parts
        if len(parts) >= 4 and parts[:3] == ("tests", "pyincore", "analyses"):
            if parts[3] in known:
                selected.add(parts[3])
        elif len(parts) >= 3 and parts[:2] == ("pyincore", "analyses"):
            name = CODE_TO_TEST_DIR.get(parts[2], parts[2])
            if name in known:
                selected.add(name)
        elif len(parts) == 2 and parts[0] == "pyincore":
            # Core module (client.py, dataset.py, ...) - affects everything, but
            # running all 86 tests on every such change is too expensive to do
            # implicitly, so just flag it.
            core_touched.append(f)

    return sorted(selected), core_touched


def main():
    scope = sys.argv[1] if len(sys.argv) > 1 else "all"
    argument = sys.argv[2] if len(sys.argv) > 2 else ""
    core_touched = []

    if scope == "all":
        names = all_analyses()
        reason = f"all {len(names)} analyses"
    elif scope == "select":
        requested = [n for n in argument.replace(",", " ").split() if n]
        known = set(all_analyses())
        unknown = [n for n in requested if n not in known]
        if unknown:
            print(f"Unknown analyses: {', '.join(unknown)}", file=sys.stderr)
            print(f"Known: {', '.join(sorted(known))}", file=sys.stderr)
            sys.exit(1)
        names = sorted(set(requested))
        reason = f"explicitly selected: {', '.join(names)}"
    elif scope == "changed":
        names, core_touched = changed_analyses(argument)
        reason = (
            f"changed in {argument}: {', '.join(names)}"
            if names
            else f"no analyses changed in {argument}"
        )
    else:
        print(f"Unknown scope: {scope}", file=sys.stderr)
        sys.exit(1)

    matrix = [
        {
            "analysis": n,
            "tests": " ".join(
                sorted(p.name for p in (TEST_ROOT / n).glob("test_*.py"))
            ),
        }
        for n in names
    ]

    if core_touched:
        reason += (
            f" (note: {len(core_touched)} core pyincore file(s) also changed - "
            "consider re-running with scope=all)"
        )

    output = os.environ.get("GITHUB_OUTPUT")
    lines = [
        f"matrix={json.dumps(matrix)}",
        f"count={len(matrix)}",
        f"reason={reason}",
    ]
    if output:
        with open(output, "a") as f:
            f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
