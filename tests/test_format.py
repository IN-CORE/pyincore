# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import os
import pycodestyle

from pyincore.globals import PYINCORE_ROOT_FOLDER

paths = [
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/buildingdamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/buildingdamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/bridgedamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/bridgedamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/buildingeconloss/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/buildingeconloss/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/roaddamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/roaddamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/tornadoepndamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/tornadoepndamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/nonstructbuildingdamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/nonstructbuildingdamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/pipelinedamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/pipelinedamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/waterfacilitydamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/waterfacilitydamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/pipelinedamagerepairrate/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/pipelinedamagerepairrate/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/epfdamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/epfdamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/buildingfunctionality/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/buildingfunctionality/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/roadfailure/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/roadfailure/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/montecarlofailureprobability/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/montecarlofailureprobability/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/dataset.py'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/hazardservice.py'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/test_hazardservice.py'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/capitalshocks/capitalshocks.py'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/capitalshocks/test_capitalshocks.py'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/test_hazardservice.py'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/joplincge/test_joplincge.py'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/utils/dataprocessutil.py'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/test_dataprocessutil.py'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/utils/analysisutil.py'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/cumulativebuildingdamage/'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'pyincore/analyses/populationdislocation/'),
    os.path.join(PYINCORE_ROOT_FOLDER,
                 'tests/pyincore/analyses/cumulativebuildingdamage/test_cumulativebuildingdamage.py'),
    os.path.join(PYINCORE_ROOT_FOLDER, 'tests/pyincore/analyses/populationdislocation/test_populationdislocation.py')
]


def test_conformance(paths=paths):
    """Test that pyIncore conforms to PEP-8."""
    style = pycodestyle.StyleGuide(quiet=False, max_line_length=120)
    result = style.check_files(paths)
    assert result.total_errors == 0
