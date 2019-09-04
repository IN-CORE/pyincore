# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import pytest
import requests

from pyincore import IncoreClient, InsecureIncoreClient
from pyincore.globals import INCORE_API_DEV_URL, INCORE_API_DEV_INSECURE_URL


@pytest.fixture
def cred():
    c = []
    try:
        with open(".incorepw", 'r') as f:
            c = f.read().splitlines()
        return c
    except EnvironmentError:
        return None


def test_client_success(cred):
    """
    testing successful login
    """
    if cred is None:
        assert False, ".incorepw does not exist!"
    # client = IncoreClient(INCORE_API_DEV_URL, cred[0], cred[1])
    client = InsecureIncoreClient(INCORE_API_DEV_INSECURE_URL, cred[0])
    assert client.status is "success"


def test_client_fail():
    """
    testing failed login
    """
    client = IncoreClient(INCORE_API_DEV_URL, "foo", "pass")
    assert client.status is "fail"
