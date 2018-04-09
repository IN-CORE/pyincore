import pytest
import json

from pyincore import IncoreClient, FragilityService, InsecureIncoreClient


@pytest.fixture
def fragilitysvc():
    cred = None
    try:
        with open(".incorepw", 'r') as f:
            cred = f.read().splitlines()
    except EnvironmentError:
        return None
    # client = IncoreClient("https://incore2-services.ncsa.illinois.edu", cred[0], cred[1])
    client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", cred[0])
    return FragilityService(client)


def test_get_fragility_set(fragilitysvc):
    id = "5894e7111a74393018c3c586"
    metadata = fragilitysvc.get_fragility_set(id)

    assert metadata['id'] == id

def test_map_fragilities(fragilitysvc):
    with open("test_data/inventories.json",'r') as f:
        inventories = json.load(f)
    key = ''
    metadata = fragilitysvc.map_fragilities(inventories, key)

    assert False

def test_map_fragility(fragilitysvc):

    with open("test_data/inventory.json", 'r') as f:
        inventory = json.load(f)

    key = ''
    metadata = fragilitysvc.map_fragility(inventory, key)

    assert False