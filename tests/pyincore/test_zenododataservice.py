# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import os

import pytest


@pytest.fixture
def datasvc_zenodo():
    return pytest.datasvc_zenodo


# @pytest.mark.skip("access token not available yet")
def test_get_record(datasvc_zenodo):
    record_id = "7349052"
    record = datasvc_zenodo.get_record(record_id)
    assert record["conceptdoi"] == "10.5281/zenodo.7349051"
    assert len(record["files"]) == 1
