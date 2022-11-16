import os

import pytest
from _pytest.monkeypatch import MonkeyPatch

from jose import jwt

from pyincore import (
    globals as pyglobals,
    IncoreClient, DataService, FragilityService, RepairService, RestorationService, HazardService, SpaceService,
    ClowderClient
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
    client = IncoreClient(service_url=pyglobals.INCORE_API_DEV_URL, token_file_name=".incrtesttoken")
    clowder_client = ClowderClient(service_url="http://localhost:8000/", token_file_name=".clowderapikey")
    pytest.client = client
    pytest.datasvc = DataService(client)
    pytest.datasvc_clowder = DataService(clowder_client)
    pytest.fragilitysvc = FragilityService(client)
    pytest.repairsvc = RepairService(client)
    pytest.restorationsvc = RestorationService(client)
    pytest.hazardsvc = HazardService(client)
    pytest.spacesvc = SpaceService(client)
    print(f"Successfully initialized Incore client and services. Using {pyglobals.INCORE_API_DEV_URL}")
