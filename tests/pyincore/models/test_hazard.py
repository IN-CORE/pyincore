import pytest
import os
from pyincore import Dataset
from pyincore.models.flood import Flood

from pyincore.models.hazardDataset import HurricaneDataset, FloodDataset
from pyincore.models.hurricane import Hurricane

from pyincore import globals as pyglobals

hazardsvc = pytest.hazardsvc
datasvc = pytest.datasvc


def get_remote_hurricane(hurricane_id: str):
    hurricane = Hurricane.from_hazard_service(hurricane_id, hazardsvc)
    return hurricane


def test_create_hurricane_from_remote():
    hurricane = get_remote_hurricane("64e904cea88e824e009a1aa2")
    assert len(hurricane.hazardDatasets) != 0
    assert isinstance(hurricane.hazardDatasets[0], HurricaneDataset)

    # attach dataset from remote
    hurricane.hazardDatasets[0].from_data_service(datasvc)
    assert isinstance(hurricane.hazardDatasets[0].dataset, Dataset)
    assert hurricane.hazardDatasets[1].dataset is None


def test_create_hurricane_from_local():

    # create the hurricane object
    hurricane = Hurricane.from_json_file(os.path.join(pyglobals.TEST_DATA_DIR, "hurricane-dataset.json"))

    # attach dataset from local file
    hurricane.hazardDatasets[0].from_file((os.path.join(pyglobals.TEST_DATA_DIR, "Wave_Raster.tif")))
    hurricane.hazardDatasets[1].from_file(os.path.join(pyglobals.TEST_DATA_DIR, "Surge_Raster.tif"))
    hurricane.hazardDatasets[2].from_file(os.path.join(pyglobals.TEST_DATA_DIR, "Inundation_Raster.tif"))

    assert len(hurricane.hazardDatasets) != 0
    assert isinstance(hurricane.hazardDatasets[0], HurricaneDataset)
    assert isinstance(hurricane.hazardDatasets[0].dataset, Dataset)
    assert isinstance(hurricane.hazardDatasets[1].dataset, Dataset)
    assert isinstance(hurricane.hazardDatasets[2].dataset, Dataset)


def test_create_flood_from_local():

    flood = Flood.from_json_file(os.path.join(pyglobals.TEST_DATA_DIR, "flood-dataset.json"))

    # attach dataset from local file
    flood.hazardDatasets[0].from_file((os.path.join(pyglobals.TEST_DATA_DIR, "flood-inundationDepth-50ft.tif")))
    flood.hazardDatasets[1].from_file(os.path.join(pyglobals.TEST_DATA_DIR, "flood-WSE-50ft.tif"))

    payload = [
        {
            "demands": ["inundationDepth", "waterSurfaceElevation"],
            "units": ["ft", "m"],
            "loc": "34.61,-79.04"
        },
    ]
    assert len(flood.hazardDatasets) != 0
    assert not isinstance(flood.hazardDatasets[0], HurricaneDataset)
    assert isinstance(flood.hazardDatasets[0], FloodDataset)
    assert isinstance(flood.hazardDatasets[0].dataset, Dataset)

    values = flood.read_hazard_values(payload)
    assert values[0]['hazardValues'] == [4.114662170410156, 37.26129305419922]


def test_read_hazard_values_from_remote():
    payload = [
        {
            "demands": ["waveHeight", "surgeLevel"],
            "units": ["m", "m"],
            "loc": "29.22,-95.06"
        },
        {
            "demands": ["waveHeight", "surgeLevel"],
            "units": ["cm", "cm"],
            "loc": "29.23,-95.05"
        },
        {
            "demands": ["waveHeight", "inundationDuration"],
            "units": ["in", "hr"],
            "loc": "29.22,-95.06"
        }
    ]
    hurricane = get_remote_hurricane("5f10837c01d3241d77729a4f")
    values = hurricane.read_hazard_values(payload, hazard_service=hazardsvc, timeout=(30, 600))
    assert len(values) == len(payload) \
           and len(values[0]['demands']) == len(payload[0]['demands']) \
           and values[0]['units'] == payload[0]['units'] \
           and len(values[0]['hazardValues']) == len(values[0]['demands']) \
           and all(isinstance(hazardval, float) for hazardval in values[0]['hazardValues']) \
           and values[0]['hazardValues'] == [1.54217780024576, 3.663398872786693]


def test_read_hazard_values_from_local():
    payload = [
        {
            "demands": ["waveHeight", "surgeLevel"],
            "units": ["m", "m"],
            "loc": "29.22,-95.06"
        },
        {
            "demands": ["waveHeight", "surgeLevel"],
            "units": ["cm", "in"],
            "loc": "29.22,-95.06"
        },
        {
            "demands": ["inundationDuration", "inundationDuration"],
            "units": ["hr", "s"],
            "loc": "29.22,-95.06"
        },
        {
            "demands": ["waveHeight", "surgeLevel"],
            "units": ["m", "m"],
            "loc": "29.34,-94.94"
        }
    ]

    # create the hurricane object
    hurricane = Hurricane.from_json_file(os.path.join(pyglobals.TEST_DATA_DIR, "hurricane-dataset.json"))

    # attach dataset from local file
    hurricane.hazardDatasets[0].from_file((os.path.join(pyglobals.TEST_DATA_DIR, "Wave_Raster.tif")))
    hurricane.hazardDatasets[0].set_threshold(threshold_value=3.28084, threshold_unit="ft")

    hurricane.hazardDatasets[1].from_file(os.path.join(pyglobals.TEST_DATA_DIR, "Surge_Raster.tif"))
    hurricane.hazardDatasets[2].from_file(os.path.join(pyglobals.TEST_DATA_DIR, "Inundation_Raster.tif"))

    values = hurricane.read_hazard_values(payload)
    assert len(values) == len(payload)
    assert len(values[0]['demands']) == len(payload[0]['demands'])
    assert values[0]['units'] == payload[0]['units']
    assert len(values[0]['hazardValues']) == len(values[0]['demands'])
    assert all(isinstance(hazardval, float) for hazardval in values[0]['hazardValues'])
    assert values[0]['hazardValues'] == [1.54217780024576, 3.663398872786693]
    assert values[1]['hazardValues'] == [1.54217780024576*100, 3.663398872786693*39.3701]  # unit conversion
    assert values[2]['hazardValues'] == [18.346923306935572, 18.346923306935572*3600]  # unit conversion
    assert values[3]['hazardValues'] == [None, 3.471035889851387]  # test threshold
