
from pyincore.utils.analysisutil import AnalysisUtil
import pytest


@pytest.mark.parametrize("hazard_vals, hazard_type, expected", [
    ([1.5, 2], "tornado", "yes"),
    ([None, None], "tornado", "no"),
    ([1.5, None], "tornado", "partial"),
    ([1.5], "earthquake", "n/a"),
    ([], "tornado", "error")
])
def test_get_exposure_from_hazard_values(hazard_vals, hazard_type, expected):
    hazard_exposure = AnalysisUtil.get_exposure_from_hazard_values(hazard_vals, hazard_type)
    assert hazard_exposure == expected
