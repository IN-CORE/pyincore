# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import os

import numpy as np
import pytest
from jose import jwt

from pyincore import globals as pyglobals
from pyincore import HazardService, IncoreClient


@pytest.fixture
def hazardsvc(monkeypatch):
    try:
        with open(os.path.join(os.path.dirname(__file__), ".incorepw"), 'r') as f:
            cred = f.read().splitlines()
    except EnvironmentError:
        assert False
    credentials = jwt.decode(cred[0], cred[1])
    monkeypatch.setattr("builtins.input", lambda x: credentials["username"])
    monkeypatch.setattr("getpass.getpass", lambda y: credentials["password"])
    client = IncoreClient(service_url=pyglobals.INCORE_API_DEV_URL, token_file_name=".incrtesttoken")
    return HazardService(client)


def test_get_earthquake_hazard_metadata_list(hazardsvc):
    """
    test get /earthquakes endpoint
    """
    response = hazardsvc.get_earthquake_hazard_metadata_list()
    assert len(response) > 0 and 'id' in response[0].keys()


def test_get_earthquake_hazard_metadata(hazardsvc):
    """
    Testing get earthquake/{id}
    """
    response = hazardsvc.get_earthquake_hazard_metadata(
        "5b902cb273c3371e1236b36b")
    assert response['id'] == "5b902cb273c3371e1236b36b"


def test_get_earthquake_hazard_value(hazardsvc):
    """
    testing getting hazard value
    """
    hval = hazardsvc.get_earthquake_hazard_value("5b902cb273c3371e1236b36b",
                                                 "0.2 SA", "g", 35.07899,
                                                 -90.0178)
    assert hval == 0.5322993805448739


def test_get_earthquake_hazard_values(hazardsvc):
    """
    Testing getting multiple hazard values
    """
    hvals = hazardsvc.get_earthquake_hazard_values("5b902cb273c3371e1236b36b",
                                                   "0.2 SA", "g",
                                                   ["35.07899,-90.0178",
                                                    "35.17899,-90.0178"])
    assert hvals[0]['hazardValue'] == 0.5322993805448739 and hvals[1][
        'hazardValue'] == 0.5926201634382787


def test_get_earthquake_hazard_value_set(hazardsvc):
    # raster?demandType=0.2+SA&demandUnits=g&minX=-90.3099&minY=34.9942&maxX=-89.6231&maxY=35.4129&gridSpacing=0.01696
    x, y, hazard_val = hazardsvc.get_earthquake_hazard_value_set(
        "5ba92505ec23090435209071",
        "0.2 SA", "g",
        [[-90.3099, 34.9942], [-89.6231, 35.4129]], 0.01696)
    assert isinstance(x, np.ndarray) and isinstance(y, np.ndarray) \
           and isinstance(hazard_val, np.ndarray)


def test_get_liquefaction_values(hazardsvc):
    liq_vals = hazardsvc.get_liquefaction_values("5b902cb273c3371e1236b36b",
                                                 "5a284f53c7d30d13bc08249c",
                                                 "in",
                                                 ["35.18,-90.076",
                                                  "35.19,-90.0178"])
    assert liq_vals[0]['pgd'] == 94.28155130685825 and liq_vals[1][
        'pgd'] == 103.2176731165868


def test_get_soil_amplification_value(hazardsvc):
    """
    test /earthquakes/soil/amplification endpoint
    """
    soil_amplification_value = hazardsvc.get_soil_amplification_value("NEHRP",
                                                                      "5a284f20c7d30d13bc081aa6",
                                                                      32.3547,
                                                                      -89.3985,
                                                                      "pga",
                                                                      0.2, "A")
    assert soil_amplification_value == 0.8


def test_get_supported_earthquake_models(hazardsvc):
    """
    test /earthquakes/models endpoint
    """
    supported_models = hazardsvc.get_supported_earthquake_models()
    models = ["AtkinsonBoore1995", "ChiouYoungs2014"]

    # check if supported_models contains all elements in the models list
    assert all(elem in supported_models for elem in models)


def test_create_earthquake(hazardsvc):
    """
    Test creating both model and dataset based earthquakes
    """
    # Dataset Based Earthquake
    with open(os.path.join(pyglobals.TEST_DATA_DIR, "eq-dataset.json"), 'r') as file:
        eq_dataset_json = file.read()

    file_paths = [str(os.path.join(pyglobals.TEST_DATA_DIR, "eq-dataset1.tif")),
                  str(os.path.join(pyglobals.TEST_DATA_DIR, "eq-dataset2.tif"))]

    dataset_response = hazardsvc.create_earthquake(eq_dataset_json, file_paths)
    assert dataset_response["id"] is not None and dataset_response["hazardDatasets"][1]["datasetId"] is not None

    # Model Based Earthquake without files
    with open(os.path.join(pyglobals.TEST_DATA_DIR, "eq-model.json"), 'r') as file:
        eqmodel_json = file.read()

    model_response = hazardsvc.create_earthquake(eqmodel_json)
    assert model_response["id"] is not None


def test_get_earthquake_aleatory_uncertainty(hazardsvc):
    hazard_id = "5c535f57c5c0e4ccead71a1a"
    demand_type = "PGA"
    model_response = hazardsvc. \
        get_earthquake_aleatory_uncertainty(hazard_id, demand_type)
    assert model_response[demand_type] is not None and \
           (0 < model_response[demand_type] <= 1)


def test_get_earthquake_variance(hazardsvc):
    hazard_id = "5c535f57c5c0e4ccead71a1a"
    variance_type = "total"
    demand_type = "PGA"
    demand_units = "g"
    points = ["35.927, -89.919"]

    model_response = hazardsvc.get_earthquake_variance(
        hazard_id, variance_type, demand_type, demand_units, points)
    assert model_response[0] is not None and \
           (0 < model_response[0]["variance"] <= 1)


def test_get_tornado_hazard_metadata_list(hazardsvc):
    response = hazardsvc.get_tornado_hazard_metadata_list()
    assert len(response) > 0 and 'id' in response[0].keys()


def test_get_tornado_hazard_metadata(hazardsvc):
    """
    Testing get tornado/{id}
    """
    response = hazardsvc.get_tornado_hazard_metadata(
        "5c6726705648c40890ba03a7")
    assert response['id'] == "5c6726705648c40890ba03a7"


def test_create_tornado_scenario(hazardsvc):
    with open(os.path.join(pyglobals.TEST_DATA_DIR, "tornado.json"), 'r') as file:
        scenario = file.read()
    response = hazardsvc.create_tornado_scenario(scenario)
    assert response["id"] is not None


def test_get_tornado_hazard_value(hazardsvc):
    hval = hazardsvc.get_tornado_hazard_value("5c6726705648c40890ba03a7",
                                              "mph", 35.228, -97.478, 0)
    assert ((hval > 85) and (hval < 165))


def test_get_tornado_hazard_values(hazardsvc):
    """
    Testing getting multiple hazard values
    """
    hvals = hazardsvc.get_tornado_hazard_values("5c6726705648c40890ba03a7",
                                                "mph",
                                                ["35.228, -97.478",
                                                 "35.229, -97.465"])

    assert ((hvals[0]['hazardValue'] > 85) and (
                hvals[0]['hazardValue'] < 165)) and hvals[1][
               'hazardValue'] == 0


def test_get_tsunami_hazard_metadata_list(hazardsvc):
    response = hazardsvc.get_tsunami_hazard_metadata_list()
    assert len(response) > 0 and 'id' in response[0].keys()


def test_get_tsunami_hazard_metadata(hazardsvc):
    """
    Testing get tsunami/{id}
    """
    response = hazardsvc.get_tsunami_hazard_metadata(
        "5bc9e25ef7b08533c7e610dc")
    assert response['id'] == "5bc9e25ef7b08533c7e610dc"


def test_get_tsunami_hazard_value(hazardsvc):
    response = hazardsvc.get_tsunami_hazard_value("5bc9ead7f7b08533c7e610e0",
                                                  "hmax", "m", 46.006,
                                                  -123.935)
    assert response == 5.900000095367432


def test_get_tsunami_hazard_values(hazardsvc):
    response = hazardsvc.get_tsunami_hazard_values("5bc9ead7f7b08533c7e610e0",
                                                   "hmax", "m",
                                                   ["46.006,-123.935",
                                                    "46.007, -123.969"])
    assert response[0]["hazardValue"] == 5.900000095367432 and response[1]["hazardValue"] == 4.099999904632568


def test_create_tsunami_hazard(hazardsvc):
    with open(os.path.join(pyglobals.TEST_DATA_DIR, "tsunami.json"), 'r') as file:
        tsunami_json = file.read()

    file_paths = [str(os.path.join(pyglobals.TEST_DATA_DIR, "Tsu_100yr_Vmax.tif")),
                  str(os.path.join(pyglobals.TEST_DATA_DIR, "Tsu_100yr_Mmax.tif")),
                  str(os.path.join(pyglobals.TEST_DATA_DIR, "Tsu_100yr_Hmax.tif"))]
    response = hazardsvc.create_tsunami_hazard(tsunami_json, file_paths)
    assert response["id"] is not None and response["hazardDatasets"][1][
        "datasetId"] is not None


def test_create_and_delete_hurricane(hazardsvc):
    """
        Also deletes the created dataset
    """
    with open(os.path.join(pyglobals.TEST_DATA_DIR, "hurricane-dataset.json"), 'r') as file:
        hurricane_json = file.read()

    file_paths = [str(os.path.join(pyglobals.TEST_DATA_DIR, "Wave_Raster.tif")),
                  str(os.path.join(pyglobals.TEST_DATA_DIR, "Surge_Raster.tif")),
                  str(os.path.join(pyglobals.TEST_DATA_DIR, "Inundation_Raster.tif"))]
    post_response = hazardsvc.create_hurricane(hurricane_json, file_paths)
    assert post_response["id"] is not None and post_response["hazardDatasets"][1][
        "datasetId"] is not None

    del_response = hazardsvc.delete_hurricane(post_response["id"])
    assert del_response["id"] is not None


def test_get_hurricane_metadata(hazardsvc):
    response = hazardsvc.get_hurricane_metadata("5f10837c01d3241d77729a4f")
    assert response['id'] == "5f10837c01d3241d77729a4f"


def test_get_hurricane_metadata_list(hazardsvc):
    response = hazardsvc.get_hurricane_metadata_list()
    assert len(response) > 0 and 'id' in response[0].keys()


def test_get_hurricane_values(hazardsvc):
    response = hazardsvc.get_hurricane_values("5f10837c01d3241d77729a4f",
                                              "waveHeight", "m", ["29.22,-95.06", "29.20, -95.10"])
    assert response[0]["hazardValue"] == 18.346923306935572 and response[1]["hazardValue"] == 14.580423799099865


def test_search_hurricanes(hazardsvc):
    response = hazardsvc.search_hurricanes("Galveston")
    assert response[0]["id"] is not None


def test_create_and_delete_flood(hazardsvc):
    """
        Also deletes the created dataset
    """
    with open(os.path.join(pyglobals.TEST_DATA_DIR, "flood-dataset.json"), 'r') as file:
        flood_json = file.read()

    file_paths = [str(os.path.join(pyglobals.TEST_DATA_DIR, "flood-inundationDepth-50ft.tif")),
                  str(os.path.join(pyglobals.TEST_DATA_DIR, "flood-WSE-50ft.tif"))]
    post_response = hazardsvc.create_flood(flood_json, file_paths)
    assert post_response["id"] is not None and post_response["hazardDatasets"][1][
        "datasetId"] is not None

    del_response = hazardsvc.delete_flood(post_response["id"])
    assert del_response["id"] is not None


def test_get_flood_metadata(hazardsvc):
    # TODO add id of published flood
    response = hazardsvc.get_flood_metadata("5f4d02e99f43ee0dde768406")
    assert response['id'] == "5f4d02e99f43ee0dde768406"


def test_get_flood_metadata_list(hazardsvc):
    response = hazardsvc.get_flood_metadata_list()
    assert len(response) > 0 and 'id' in response[0].keys()


def test_get_flood_values(hazardsvc):
    response = hazardsvc.get_flood_values("5f4d02e99f43ee0dde768406", "waterSurfaceElevation", "m",
                                          ["34.60,-79.16", "34.62,-79.16"])
    assert response[0]["hazardValue"] == 137.69830322265625 and response[1]["hazardValue"] == 141.17652893066406


def test_search_floods(hazardsvc):
    response = hazardsvc.search_floods("Lumberton")
    assert response[0]["id"] is not None


@pytest.mark.skip(reason="performance issues")
def test_create_hurricane_windfield(hazardsvc):
    with open(os.path.join(pyglobals.TEST_DATA_DIR, "hurricanewf.json"), 'r') as file:
        hurr_wf_inputs = file.read()

    response = hazardsvc.create_hurricane_windfield(hurr_wf_inputs)
    assert response["id"] is not None


@pytest.mark.skip(reason="performance issues")
def test_get_hurricanewf_metadata(hazardsvc):
    response = hazardsvc.get_hurricanewf_metadata("5bd3d6a1f242fe0cf903cb0e")
    assert response['id'] == "5bd3d6a1f242fe0cf903cb0e"


@pytest.mark.skip(reason="performance issues")
def test_get_hurricanewf_metadata_list(hazardsvc):
    response = hazardsvc.get_hurricanewf_metadata_list(coast="florida")
    assert len(response) > 0 and 'id' in response[0].keys()


@pytest.mark.skip(reason="performance issues")
def test_get_hurricanewf_values(hazardsvc):
    hvals = hazardsvc.get_hurricanewf_values("5cffdcf35648c404a6414f7e",
                                             "3s", "mph", ["28,-81"], 10.0, 0.03)

    assert (pytest.approx(hvals[0]['hazardValue'], 1e-6) == 81.57440785011988)


@pytest.mark.skip(reason="performance issues")
def test_get_hurricanewf_json(hazardsvc):
    hjson = hazardsvc.get_hurricanewf_json("florida", 1, -83, "28,-81", "3s", "kmph", 6, 10,
                                           "circular")

    assert len(hjson["hurricaneSimulations"]) > 0
