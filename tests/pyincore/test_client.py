# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import os.path

import pytest
import requests

from pyincore import Client, IncoreClient, InsecureIncoreClient, DataService


def test_client_success(monkeypatch):
    """
    testing successful login
    """
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


def test_delete_repo_cache():
    client = IncoreClient(token_file_name=".incrtesttoken")
    hashed_repo_dir_path = client.hashed_svc_data_dir
    client.clear_cache()
    assert os.path.exists(hashed_repo_dir_path) is False
