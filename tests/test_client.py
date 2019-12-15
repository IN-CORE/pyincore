# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import pytest
from jose import jwt
from pyincore import IncoreClient


def test_client_success(monkeypatch):
    """
    testing successful login
    """
    try:
        with open(".incorepw", 'r') as f:
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
