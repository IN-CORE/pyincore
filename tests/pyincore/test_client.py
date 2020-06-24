# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pytest
import requests
import os
from jose import jwt

from pyincore import Client, IncoreClient, InsecureIncoreClient, DataService


def test_client_success(monkeypatch):
    """
    testing successful login
    """
    try:
        with open(os.path.join(os.path.dirname(__file__), ".incorepw"), 'r') as f:
            cred = f.read().splitlines()
    except EnvironmentError:
        assert False
    credentials = jwt.decode(cred[0], cred[1])
    monkeypatch.setattr("builtins.input", lambda x: credentials["username"])
    monkeypatch.setattr("getpass.getpass", lambda y: credentials["password"])
    client = IncoreClient(token_file_name=".incrtesttoken")
    assert "bearer" in str(client.session.headers["Authorization"])


def test_client_fail(monkeypatch):
    """
    testing failed login
    """
    with pytest.raises(SystemExit):
        monkeypatch.setattr("builtins.input", lambda x: "incrtest")
        monkeypatch.setattr("getpass.getpass", lambda y: "invalid-password")
        IncoreClient(token_file_name=".none")


@pytest.mark.skip(reason="needs more thought on what to assert")
def test_delete_cache():
    r = Client.clear_cache()
    assert r is None


def test_insecure_client():
    """
    test insecure client
    """
    client = InsecureIncoreClient(username="incrtest")
    data_svc = DataService(client)
    try:
        r = data_svc.get_datasets()
        assert len(r) != 0
    except requests.HTTPError:
        assert False
