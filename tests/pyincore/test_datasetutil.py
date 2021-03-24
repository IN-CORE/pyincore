import pytest
import os
import jwt

from pyincore import IncoreClient, Dataset, DataService
from pyincore.globals import INCORE_API_DEV_URL
from pyincore.utils.datasetutil import DatasetUtil as util


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


def test_join_table_dataset_with_source_dataset(client):
    building_damage_id = '5a296b53c7d30d4af5378cd5'
    dataset = Dataset.from_data_service(building_damage_id, DataService(client))
    joined_gdf = util.join_table_dataset_with_source_dataset(dataset, client)

    # assert if the fields from each dataset exist
    assert 'year_built' in joined_gdf.keys() and 'meandamage' in joined_gdf.keys()


def test_join_datasets(client):
    building_id = '5a284f0bc7d30d13bc081a28'
    building_damage_id = '5a296b53c7d30d4af5378cd5'
    bldg_dataset = Dataset.from_data_service(building_id, DataService(client))
    bldg_dmg_dataset = Dataset.from_data_service(building_damage_id, DataService(client))
    joined_gdf = util.join_datasets(bldg_dataset, bldg_dmg_dataset)

    # assert if the fields from each dataset exist
    assert 'year_built' in joined_gdf.keys() and 'meandamage' in joined_gdf.keys()
