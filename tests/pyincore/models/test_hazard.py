import pytest

from pyincore import Dataset

from pyincore.models.hazardDataset import HurricaneDataset
from pyincore.models.hurricane import Hurricane

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

    # TODO replace below with local hazard construction once ready
    hurricane = get_remote_hurricane("5f10837c01d3241d77729a4f")
    hurricane.hazardDatasets[0].from_data_service(datasvc)
    hurricane.hazardDatasets[1].from_data_service(datasvc)
    hurricane.hazardDatasets[2].from_data_service(datasvc)

    values = hurricane.read_hazard_values(payload)
    assert len(values) == len(payload) \
           and len(values[0]['demands']) == len(payload[0]['demands']) \
           and values[0]['units'] == payload[0]['units'] \
           and len(values[0]['hazardValues']) == len(values[0]['demands']) \
           and all(isinstance(hazardval, float) for hazardval in values[0]['hazardValues']) \
           and values[0]['hazardValues'] == [1.54217780024576, 3.663398872786693]


def test_create_hurricane():
    pass
    # fragility_set = get_fragility_set("fragility_curve.json")
    # assert len(fragility_set.fragility_curves) != 0
