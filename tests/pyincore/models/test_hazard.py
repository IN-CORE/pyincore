import pytest

from pyincore import Dataset

from pyincore.models.hazardDataset import HurricaneDataset
from pyincore.models.hurricane import Hurricane


def get_remote_hurricane(hurricane_id: str):
    hazardsvc = pytest.hazardsvc
    hurricane = Hurricane.from_hazard_service(hurricane_id, hazardsvc)
    return hurricane


def test_create_hurricane_from_remote():
    hurricane = get_remote_hurricane("64e904cea88e824e009a1aa2")
    assert len(hurricane.hazardDatasets) != 0
    assert isinstance(hurricane.hazardDatasets[0], HurricaneDataset)

    # attach dataset from remote
    datasvc = pytest.datasvc
    hurricane.hazardDatasets[0].from_data_service(datasvc)
    assert isinstance(hurricane.hazardDatasets[0].dataset, Dataset)
    assert hurricane.hazardDatasets[1].dataset is None


def test_create_hurricane():
    pass
    # fragility_set = get_fragility_set("fragility_curve.json")
    # assert len(fragility_set.fragility_curves) != 0
