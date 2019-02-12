import pytest
import numpy as np

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
    assert len(response) > 0 and 'id' in response[0].keys()

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

def test_get_earthquake_hazard_value_set(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    # raster?demandType=0.2+SA&demandUnits=g&minX=-90.3099&minY=34.9942&maxX=-89.6231&maxY=35.4129&gridSpacing=0.01696
    x, y, hazard_val = hazardsvc.get_earthquake_hazard_value_set("5ba92505ec23090435209071",
                                                                 "0.2 SA", "g",
                                                                 [[-90.3099, 34.9942],[-89.6231, 35.4129]],0.01696)
    assert isinstance(x, np.ndarray) and isinstance(y, np.ndarray) \
           and isinstance(hazard_val, np.ndarray)

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
    assert len(response)>0 and 'id' in response[0].keys()

def test_get_tornado_hazard_metadata(hazardsvc):
    """
    Testing get tornado/{id}
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    response = hazardsvc.get_tornado_hazard_metadata("5c62e9ecc11bb380daa9cb75")
    assert response['id'] == "5c62e9ecc11bb380daa9cb75"

def test_get_tornado_hazard_value(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"

    hval = hazardsvc.get_tornado_hazard_value("5c62e9ecc11bb380daa9cb75", "mph", 35.228, -97.478, 0)
    assert ((hval > 85) and (hval <  165))

def test_get_tornado_hazard_values(hazardsvc):
    """
    Testing getting multiple hazard values
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    hvals = hazardsvc.get_tornado_hazard_values("5c62e9ecc11bb380daa9cb75", "mph",
                                                   ["35.228, -97.478", "35.229, -97.465"])

    assert ((hvals[0]['hazardValue'] > 85) and (hvals[0]['hazardValue'] < 165)) and hvals[1]['hazardValue'] == 0

def test_create_tornado_model(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    with open("tornado_model.json", 'r') as file:
        tornado_json = file.read()

    response = hazardsvc.create_tornado(tornado_json)
    assert response["id"] is not None

# TODO: we don't have any dataset tornado yet, we'll test it when we have those shapefiles
# def test_create_tornado_dataset(hazardsvc):
#     if hazardsvc is None:
#         assert False, ".incorepw does not exist!"
#     with open("torndo_dataset.json", 'r') as file:
#         tornado_json = file.read()
#     file_paths = ["","",""]
#     response = hazardsvc.create_tornado(tornado_json, file_paths)
#
#     assert response["id"] is not None

def test_get_tsunami_hazard_metadata_list(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    response = hazardsvc.get_tsunami_hazard_metadata_list()
    assert len(response)>0 and 'id' in response[0].keys()

def test_get_tsunami_hazard_metadata(hazardsvc):
    """
    Testing get tsunami/{id}
    """
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    response = hazardsvc.get_tsunami_hazard_metadata("5bc9e25ef7b08533c7e610dc")
    assert response['id'] == "5bc9e25ef7b08533c7e610dc"

def test_get_tsunami_hazard_value(hazardsvc):
    response = hazardsvc.get_tsunami_hazard_value("5bc9ead7f7b08533c7e610e0",
                                                   "hmax", "m", 46.006, -123.935)
    assert response == 5.900000095367432

def test_get_tsunami_hazard_values(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"
    response = hazardsvc.get_tsunami_hazard_values("5bc9ead7f7b08533c7e610e0",
                                                   "hmax", "m", ["46.006,-123.935", "46.007, -123.969"])
    assert response[0]["hazardValue"]==5.900000095367432 \
           and response[1]["hazardValue"]==4.099999904632568

def test_create_tsunami_hazard(hazardsvc):
    if hazardsvc is None:
        assert False, ".incorepw does not exist!"

    with open("tsunami.json", 'r') as file:
        tsunami_json = file.read()

    file_paths = ["Tsu_100yr_Vmax.tif", "Tsu_100yr_Mmax.tif", "Tsu_100yr_Hmax.tif"];
    response = hazardsvc.create_tsunami_hazard(tsunami_json, file_paths)
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
    assert len(response) > 0 and 'id' in response[0].keys()

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
