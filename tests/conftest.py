import os

import pytest
from _pytest.monkeypatch import MonkeyPatch

from jose import jwt

from pyincore import (
    globals as pyglobals,
    IncoreClient
)


@pytest.hookimpl()
def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    try:
        with open(os.path.join(os.path.dirname(__file__), "pyincore/.incorepw"), 'r') as f:
            cred = f.read().splitlines()
    except EnvironmentError:
        assert False
    credentials = jwt.decode(cred[0], cred[1])

    monkeypatch = MonkeyPatch()
    monkeypatch.setattr("builtins.input", lambda x: credentials["username"])
    monkeypatch.setattr("getpass.getpass", lambda y: credentials["password"])
    IncoreClient(service_url=pyglobals.INCORE_API_DEV_URL, token_file_name=".incrtesttoken")
    print("Successfully initialized Incore Client.")
