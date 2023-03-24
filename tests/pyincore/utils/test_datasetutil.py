import pytest

from pyincore import Dataset, DataService
from pyincore.utils.datasetutil import DatasetUtil as util


@pytest.fixture
def client():
    return pytest.client


def test_join_table_dataset_with_source_dataset(client):
    building_damage_id = '5a296b53c7d30d4af5378cd5'
    dataset = Dataset.from_data_service(building_damage_id, DataService(client))
    joined_gdf = util.join_table_dataset_with_source_dataset(dataset, client)

    # assert if the fields from each dataset exist
    assert 'geometry' in joined_gdf.keys() and 'meandamage' in joined_gdf.keys()


def test_join_datasets(client):
    building_id = '5a284f0bc7d30d13bc081a28'
    building_damage_id = '5a296b53c7d30d4af5378cd5'
    bldg_dataset = Dataset.from_data_service(building_id, DataService(client))
    bldg_dmg_dataset = Dataset.from_data_service(building_damage_id, DataService(client))
    joined_gdf = util.join_datasets(bldg_dataset, bldg_dmg_dataset)

    # assert if the fields from each dataset exist
    assert 'year_built' in joined_gdf.keys() and 'meandamage' in joined_gdf.keys()
