"""

Copyright (c) 2019 University of Illinois and others.  All rights reserved.
This program and the accompanying materials are made available under the
terms of the Mozilla Public License v2.0 which accompanies this distribution,
and is available at https://www.mozilla.org/en-US/MPL/2.0/

"""

import pytest

from pyincore import IncoreClient


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
    client = IncoreClient("https://incore2-services.ncsa.illinois.edu", cred[0], cred[1])
    assert client.status is "success"


def test_client_fail():
    """
    testing failed login
    """
    client = IncoreClient("https://incore2-services.ncsa.illinois.edu", "xxx", "xxxx")
    assert client.status is "fail"

