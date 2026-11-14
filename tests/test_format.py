# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import subprocess
import sys

from pyincore.globals import PYINCORE_ROOT_FOLDER

PATHS = ["pyincore", "tests", "recipes", "scripts", "docs"]


def test_conformance():
    """Test that pyIncore conforms to the project's style rules.

    This defers to flake8 so there is a single source of truth: settings,
    including the non-ML CGE exclusions, live in .flake8 and are shared with the
    pre-commit hooks and the CI lint job. flake8 also honours `# noqa`, which a
    bare pycodestyle run does not.
    """
    result = subprocess.run(
        [sys.executable, "-m", "flake8", *PATHS],
        cwd=PYINCORE_ROOT_FOLDER,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"\n{result.stdout}{result.stderr}"
