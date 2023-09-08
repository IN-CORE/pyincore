import pytest
import os
from pyincore import Dataset

from pyincore.models.hazardDataset import HurricaneDataset
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
            "units": ["cm", "cm"],
            "loc": "29.23,-95.05"
        },
        {
            "demands": ["waveHeight", "inundationDuration"],
            "units": ["in", "hr"],
            "loc": "29.22,-95.06"
        }
    ]

    # create the hurricane object
    hurricane = Hurricane.from_json_file(os.path.join(pyglobals.TEST_DATA_DIR, "hurricane-dataset.json"))

    # attach dataset from local file
    hurricane.hazardDatasets[0].from_file((os.path.join(pyglobals.TEST_DATA_DIR, "Wave_Raster.tif")))
    hurricane.hazardDatasets[1].from_file(os.path.join(pyglobals.TEST_DATA_DIR, "Surge_Raster.tif"))
    hurricane.hazardDatasets[2].from_file(os.path.join(pyglobals.TEST_DATA_DIR, "Inundation_Raster.tif"))

    values = hurricane.read_hazard_values(payload)
    assert len(values) == len(payload) \
           and len(values[0]['demands']) == len(payload[0]['demands']) \
           and values[0]['units'] == payload[0]['units'] \
           and len(values[0]['hazardValues']) == len(values[0]['demands']) \
           and all(isinstance(hazardval, float) for hazardval in values[0]['hazardValues']) \
           and values[0]['hazardValues'] == [1.54217780024576, 3.663398872786693]



