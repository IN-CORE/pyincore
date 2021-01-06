import pytest
import os
import jwt

from pyincore import IncoreClient
from pyincore.globals import INCORE_API_DEV_URL
from pyincore_viz.otherutil import OtherUtil as util


@pytest.fixture
def client(monkeypatch):
    try:
        with open(os.path.join(os.path.dirname(__file__), ".incorepw"), 'r') as f:
            cred = f.read().splitlines()
    except EnvironmentError:
        assert False
    credentials = jwt.decode(cred[0], cred[1])
    monkeypatch.setattr("builtins.input", lambda x: credentials["username"])
    monkeypatch.setattr("getpass.getpass", lambda y: credentials["password"])
    client = IncoreClient(service_url=INCORE_API_DEV_URL, token_file_name=".incrtesttoken")

    return client


def test_get_mapped_result(client):
    bldg_dataset_id = "5f9091df3e86721ed82f701d"
    bldg_dmg_dataset_id = "5f9868c00ace240b22a7f2a5"
    archetype_id = "5fca915fb34b193f7a44059b"

    ret_json, mapped_df = util.get_mapped_result_from_dataset_id(
        client, bldg_dataset_id, bldg_dmg_dataset_id, archetype_id)

    assert "by_cluster" in ret_json and "category" in ret_json

    assert "archetype" in mapped_df._info_axis.values and "category" in mapped_df._info_axis.values
