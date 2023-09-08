import pytest

from pyincore import Dataset

from pyincore.models.hazardDataset import HurricaneDataset
from pyincore.models.hurricane import Hurricane


def get_remote_hurricane(hurricane_id: str):
    hazardsvc = pytest.hazardsvc
    datasvc = pytest.datasvc
    hurricane = Hurricane.from_hazard_service(hurricane_id, hazardsvc, datasvc)
    return hurricane


def test_create_hurricane_from_remote():
    hurricane = get_remote_hurricane("64e904cea88e824e009a1aa2")
    assert len(hurricane.hazardDatasets) != 0
    assert isinstance(hurricane.hazardDatasets[0], HurricaneDataset)
    assert isinstance(hurricane.hazardDatasets[0].dataset, Dataset)


def test_create_hurricane():
    pass
    # fragility_set = get_fragility_set("fragility_curve.json")
    # assert len(fragility_set.fragility_curves) != 0
