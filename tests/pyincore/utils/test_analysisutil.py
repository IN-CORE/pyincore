from pyincore.utils.analysisutil import AnalysisUtil
import pytest


@pytest.mark.parametrize(
    "hazard_vals, hazard_type, expected",
    [
        ([], "tornado", "error"),
        ([1.5, 2], "tornado", "yes"),
        ([None, None], "tsunami", "no"),
        ([1.5, None], "hurricane", "partial"),
        ([1.5], "earthquake", "yes"),
        ([1, None, -9999.1], "tornado", "error"),
        ([1.5, 2.5], "hurricanewindfield", "n/a"),
        ([-9999.99], "flood", "error"),
    ],
)
def test_get_exposure_from_hazard_values(hazard_vals, hazard_type, expected):
    hazard_exposure = AnalysisUtil.get_exposure_from_hazard_values(
        hazard_vals, hazard_type
    )
    assert hazard_exposure == expected
