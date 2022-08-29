# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pytest

from pyincore import globals as pyglobals
from pyincore.analyses.tornadoepndamage.tornadoepndamage import \
    TornadoEpnDamage
from pyincore import IncoreClient


@pytest.fixture
def datasvc():
    return pytest.datasvc


def test_tornado_epn_damage_analysis(datasvc):
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    ted = TornadoEpnDamage(client)

    epn_network_id = "62719fc857f1d94b047447e6"
    tornado_id = '5df913b83494fe000861a743'

    ted.load_remote_input_dataset("epn_network", epn_network_id)

    result_name = "tornado_dmg_result"
    ted.set_parameter("result_name", result_name)
    ted.set_parameter('tornado_id', tornado_id)
    ted.set_parameter('seed', 1001)

    ted.run_analysis()
