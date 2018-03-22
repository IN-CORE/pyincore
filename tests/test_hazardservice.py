import pytest

from pyincore import IncoreClient
from pyincore import HazardService


@pytest.fixture
def hazardsvc():
    client = IncoreClient("https://incore2-services.ncsa.illinois.edu", "xxx", "xxx")
    return HazardService(client)


def test_get_hazard_value(hazardsvc):
    """
    testing getting hazard value
    https://incore2-services.ncsa.illinois.edu/hazard/api/earthquakes/59f3315ec7d30d4d6741b0bb/value?demandType=0.2+SA&demandUnits=g&siteLat=35.07899&siteLong=-90.0178
    """
    hval = hazardsvc.get_hazard_value("59f3315ec7d30d4d6741b0bb", "0.2 SA", "g", 35.07899, -90.0178)
    assert hval == 0.5322993805448739


def test_get_hazard_values(hazardsvc):
    """
    testing getting multiple hazard values
    """
    print("2", hazardsvc.base_earthquake_url)