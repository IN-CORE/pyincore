"""Execute an analysis test script so that soft failures are not silent.

Only three of the 86 analysis tests assert on anything. The rest call
run_analysis() and discard the return value, but BaseAnalysis.run_analysis
returns False - or a (False, message) tuple - when dataset, hazard or parameter
validation fails. Without this wrapper such a script still exits 0 and the
runner reports a pass.

Only an explicit False is treated as a failure. A None return is left alone,
since an analysis whose run() has no explicit return is not necessarily broken.

usage: run_analysis_script.py <test_script.py>
"""

import runpy
import sys

from pyincore.baseanalysis import BaseAnalysis

_original_run_analysis = BaseAnalysis.run_analysis
_failures = []


def _checked_run_analysis(self, *args, **kwargs):
    result = _original_run_analysis(self, *args, **kwargs)

    if isinstance(result, tuple):
        ok = result[0] if result else False
    else:
        ok = result

    if ok is False:
        _failures.append(f"{type(self).__name__}.run_analysis() returned {result!r}")

    return result


BaseAnalysis.run_analysis = _checked_run_analysis

script = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(script, run_name="__main__")

if _failures:
    print("", file=sys.stderr)
    for failure in _failures:
        print(f"FAILED: {failure}", file=sys.stderr)
    sys.exit(1)
