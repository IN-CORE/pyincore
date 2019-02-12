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
    #client = IncoreClient("https://incore2-services.ncsa.illinois.edu", cred[0], cred[1])
    client =   InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888",
            cred[0])

    return HazardService(client)

def test_get_earthquake_hazard_metadata_list(hazardsvc):
    '''
    test get /earthquakes endpoint
    '''
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    response = hazardsvc.get_earthquake_hazard_metadata_list()
    assert 'id' in response[0]

def test_get_earthquake_hazard_metadata(hazardsvc):
    """
    Testing get earthquake/{id}
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    response = hazardsvc.get_earthquake_hazard_metadata("5b902cb273c3371e1236b36b")
    assert response['id'] == "5b902cb273c3371e1236b36b"

def test_get_earthquake_hazard_value(hazardsvc):
    """
    testing getting hazard value
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    hval = hazardsvc.get_earthquake_hazard_value("5b902cb273c3371e1236b36b", "0.2 SA", "g", 35.07899,-90.0178)
    assert hval == 0.5322993805448739

def test_get_earthquake_hazard_values(hazardsvc):
    """
    Testing getting multiple hazard values
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    hvals = hazardsvc.get_earthquake_hazard_values("5b902cb273c3371e1236b36b", "0.2 SA", "g",
                                                   ["35.07899,-90.0178", "35.17899,-90.0178"])
    assert hvals[0]['hazardValue'] == 0.5322993805448739 and hvals[1]['hazardValue'] == 0.5926201634382787

# TODO
# def test_get_earthquake_hazard_value_set

def test_get_liquefaction_values(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    liq_vals = hazardsvc.get_liquefaction_values("5b902cb273c3371e1236b36b","5a284f53c7d30d13bc08249c", "in",
                                ["35.18,-90.076", "35.19,-90.0178"])
    assert liq_vals[0]['pgd'] == 94.28155130685825 and liq_vals[1]['pgd'] == 103.2176731165868

def test_get_soil_amplification_value(hazardsvc):
    """
    test /earthquakes/soil/amplification endpoint
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    soil_amplification_value = hazardsvc.get_soil_amplification_value("NEHRP", "5a284f20c7d30d13bc081aa6",
                                                                      32.3547, -89.3985, "pga", 0.2, "A")
    assert soil_amplification_value == 0.8

def test_get_supported_earthquake_models(hazardsvc):
    """
    test /earthquakes/models endpoint
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    models = hazardsvc.get_supported_earthquake_models()
    assert models == [ "AtkinsonBoore1995", "ChiouYoungs2014"]

def test_create_earthquake(hazardsvc):
    """
    Test creating both model and dataset based earthquakes
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"

    # Dataset Based Earthquake
    with open("eq-dataset.json", 'r') as file:
        eq_dataset_json = file.read()

    file_paths = ["eq-dataset1.tif", "eq-dataset2.tif"];

    dataset_response = hazardsvc.create_earthquake(eq_dataset_json, file_paths)
    assert dataset_response["id"] is not None and \
           dataset_response["hazardDatasets"][1]["datasetId"] is not None

    # Model Based Earthquake without files
    with open("eq-model.json", 'r') as file:
        eqmodel_json = file.read()

    model_response = hazardsvc.create_earthquake(eqmodel_json)
    assert model_response["id"] is not None

def test_get_tornado_hazard_metadata_list(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    response = hazardsvc.get_tornado_hazard_metadata_list()
    assert 'id' in response[0]

def test_get_tornado_hazard_metadata(hazardsvc):
    """
    Testing get tornado/{id}
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    response = hazardsvc.get_tornado_hazard_metadata("5ad0f35eec230965e6d98d0c")
    assert response['id'] == "5ad0f35eec230965e6d98d0c"

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

def test_get_tornado_hazard_values(hazardsvc):
    """
    Testing getting multiple hazard values
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    hvals = hazardsvc.get_tornado_hazard_values("5ad0f35eec230965e6d98d0c", "mph",
                                                   ["35.228, -97.478", "35.229, -97.465"])

    assert ((hvals[0]['hazardValue'] > 85) and (hvals[0]['hazardValue'] < 165)) and hvals[1]['hazardValue'] == 0

def test_get_tsunami_hazard_metadata_list(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    response = hazardsvc.get_tsunami_hazard_metadata_list()
    assert 'id' in response[0]

def test_get_tsunami_hazard_metadata(hazardsvc):
    """
    Testing get tsunami/{id}
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    response = hazardsvc.get_tsunami_hazard_metadata("5bc9e25ef7b08533c7e610dc")
    assert response['id'] == "5bc9e25ef7b08533c7e610dc"

def test_create_tsunami_hazard(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"

    with open("tsunami.json", 'r') as file:
        tsunami_inputs = file.read()

    file_paths = ["", ""];
    response = hazardsvc.create_tsunami_hazard(tsunami_inputs, file_paths)
    assert response["id"] is not None and response["hazardDatasets"][1]["datasetId"] is not None

def test_create_hurricane_windfield(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"

    scenario = ""
    with open("hurricanewf.json", 'r') as file:
        hurr_wf_inputs = file.read()

    response = hazardsvc.create_hurricane_windfield(hurr_wf_inputs)
    assert response["id"] is not None

def test_get_hurricanewf_metadata(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    response = hazardsvc.get_hurricanewf_metadata("5bd3d6a1f242fe0cf903cb0e")
    assert response['id'] == "5bd3d6a1f242fe0cf903cb0e"

def test_get_hurricanewf_metadata_list(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    response = hazardsvc.get_hurricanewf_metadata_list()
    assert len(response) > 0

def test_get_hurricanewf_values(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    hvals = hazardsvc.get_hurricanewf_values("5bd3d6a1f242fe0cf903cb0e", "velocity",
        "kmph", ["28,-81"])

    assert (hvals[0]['hazardValue'] == 60.21153835934114)

def test_get_hurricanewf_json(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    hjson = hazardsvc.get_hurricanewf_json("florida", 1, -83, "28,-81", 6, 10, "circular" )

    assert len(hjson["hurricaneSimulations"]) > 0

def test_get_hazard_api_definition(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    swagger_json = hazardsvc.get_hazard_api_definition()

    assert "swagger" in swagger_json and "paths" in swagger_json
