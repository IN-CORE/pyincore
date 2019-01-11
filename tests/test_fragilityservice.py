import ast

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
    id = "5b47b2d7337d4a36187c61c9"
    metadata = fragilitysvc.get_fragility_set(id)

    assert metadata['id'] == id


def test_map_fragilities_single_inventory(fragilitysvc):
    inventory = {}
    with open("single_inventory.json", 'r') as file:
        inventory = ast.literal_eval(file.read())
    mapping_id = '5b47b2d9337d4a36187c7564'
    key = "High-Retrofit Drift-Sensitive Fragility ID Code"
    frag_set = fragilitysvc.map_fragilities(mapping_id, [inventory], key)

    assert inventory['id'] in frag_set.keys()


def test_map_fragilities_multiple_inventory(fragilitysvc):
    inventories = []
    with open("multiple_inventory.json", 'r') as file:
        inventories = ast.literal_eval(file.read())
    mapping_id = '5b47b2d9337d4a36187c7564'
    key = "High-Retrofit Drift-Sensitive Fragility ID Code"
    frag_set = fragilitysvc.map_fragilities(mapping_id, inventories, key)

    assert (inventories[0]['id'] in frag_set.keys()) and (len(frag_set) == len(inventories))
