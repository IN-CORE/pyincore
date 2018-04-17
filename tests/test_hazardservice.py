import pytest

from pyincore import IncoreClient, InsecureIncoreClient
from pyincore import HazardService


@pytest.fixture
def hazardsvc():
    cred = None
    try:
        with open(".incorepw", 'r') as f:
            cred = f.read().splitlines()
    except EnvironmentError:
        return None
    # client = IncoreClient("https://incore2-services.ncsa.illinois.edu", cred[0], cred[1])
    client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", cred[0])

    return HazardService(client)


def test_get_eq_hazard_value(hazardsvc):
    """
    testing getting hazard value
    https://incore2-services.ncsa.illinois.edu/hazard/api/earthquakes/59f3315ec7d30d4d6741b0bb/value?demandType=0.2+SA&demandUnits=g&siteLat=35.07899&siteLong=-90.0178
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    hval = hazardsvc.get_hazard_value("59f3315ec7d30d4d6741b0bb", "0.2 SA", "g", 35.07899, -90.0178)
    assert hval == 0.5322993805448739


def test_get_eq_hazard_values(hazardsvc):

    assert False


def test_get_eq_hazard_value_set(hazardsvc):

    assert False


def test_create_earthquake(hazardsvc):
    """
    Test creating earthquake
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    config = ""
    with open("eq.json", 'r') as file:
        config = file.read()
    response = hazardsvc.create_earthquake(config)
    assert response["id"] is not None


def test_create_tornado_scenario(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"

    scenario = ""
    with open("tornado.json", 'r') as file:
        scenario = file.read()

    response = hazardsvc.create_tornado_scenario(scenario)
    assert response["id"] is not None


def test_get_tornado_hazard_value(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"

    hval = hazardsvc.get_tornado_hazard_value("5ad0f35eec230965e6d98d0c", "mph", 35.228, -97.478, 0)
    assert ((hval > 85) and (hval <  165))
