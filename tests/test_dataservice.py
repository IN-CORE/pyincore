# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import ast

import pytest
import os
import re

from pyincore import IncoreClient, DataService, InsecureIncoreClient
from pyincore.globals import INCORE_API_DEV_URL


@pytest.fixture
def datasvc():
    client = InsecureIncoreClient(INCORE_API_DEV_URL)

    return DataService(client)


def test_get_dataset_metadata(datasvc):
    id = "5a284f0ac7d30d13bc0819c4"
    metadata = datasvc.get_dataset_metadata(id)
    assert metadata['id'] == id


def test_get_dataset_files_metadata(datasvc):
    errors = []
    id = "5a284f0ac7d30d13bc0819c4"
    metadata = datasvc.get_dataset_metadata(id)
    fileDescriptor = datasvc.get_dataset_files_metadata(id)

    if 'id' not in fileDescriptor[0].keys():
        errors.append("response does not seem right!")

    # compare the id in fileDescriptors field in metadata with the
    # id returned by /file endpoint
    if metadata['fileDescriptors'][0]['id'] != fileDescriptor[0]['id']:
        errors.append(
            "it doesn't fetch the right fileDescriptors for this id!")

    assert not errors, "errors occured:\n{}".format("\n".join(errors))


def test_get_dataset_file_metadata(datasvc):
    dataset_id = "5a284f0bc7d30d13bc081a28"
    file_id = "5a284f0bc7d30d13bc081a2b"
    metadata = datasvc.get_dataset_file_metadata(dataset_id, file_id)
    assert 'id' in metadata.keys() and metadata['id'] == file_id


def test_get_dataset_blob(datasvc):
    errors = []
    id = "5a284f0ac7d30d13bc0819c4"
    fname = datasvc.get_dataset_blob(id, join=True)

    if type(fname) != str:
        errors.append("doesn't return the correct filename!")
    # check if file or folder exists locally, which means successfully downloaded
    if not os.path.exists(fname):
        errors.append("no file or folder has been downloaded!")

    assert not errors, "errors occured:\n{}".format("\n".join(errors))


def test_get_datasets(datasvc):
    errors = []
    datatype = "ergo:buildingDamageVer4"
    metadata = datasvc.get_datasets(datatype=datatype, title="building")

    if 'id' not in metadata[0].keys():
        errors.append("response is not right!")
    if not re.search(r'building', metadata[0]['title'].lower()):
        errors.append("title doesn't match!")
    if not re.search(datatype, metadata[0]['dataType']):
        errors.append("datatype doesn't match!")

    assert not errors, "errors occured:\n{}".format("\n".join(errors))


def test_create_dataset_geotif(datasvc):
    """
    Testing create dataset with geotif file
    """
    dataset_prop = {}
    with open('geotif_sample.json', 'r') as file:
        dataset_prop = ast.literal_eval(file.read())
    response = datasvc.create_dataset(dataset_prop)

    if 'id' not in response:
        assert False

    dataset_id = response['id']
    print('dataset is created with id ' + dataset_id)
    files = ['geotif_sample.tif']
    response = datasvc.add_files_to_dataset(dataset_id, files)

    # TODO: need to delete the test dataset

    assert response['id'] == dataset_id


def test_create_dataset_shpfile(datasvc):
    """
    Testing create dataset with shapefile
    """
    dataset_prop = {}
    with open('shp_sample.json', 'r') as file:
        dataset_prop = ast.literal_eval(file.read())
    response = datasvc.create_dataset(dataset_prop)

    if 'id' not in response:
        assert False

    dataset_id = response['id']
    print('dataset is created with id ' + dataset_id)
    files = ['shp_sample/shp_sample.shp',
             'shp_sample/shp_sample.dbf',
             'shp_sample/shp_sample.shx',
             'shp_sample/shp_sample.prj']
    response = datasvc.add_files_to_dataset(dataset_id, files)

    # TODO: need to delete the test dataset

    assert response['id'] == dataset_id


def test_update_dataset(datasvc):
    id = "5ace7322ec230944f695f5cf"
    property_name = "title"
    property_value = "test update dataset"
    response = datasvc.update_dataset(id, property_name, property_value)

    assert response[property_name] == property_value


def test_get_files(datasvc):
    metadata = datasvc.get_files()
    assert 'id' in metadata[0]


def test_get_file_metadata(datasvc):
    metadata = datasvc.get_file_metadata("5a284f24c7d30d13bc081adb")
    assert metadata['id'] == "5a284f24c7d30d13bc081adb"


def test_get_file_blob(datasvc):
    errors = []
    id = "5a284f24c7d30d13bc081adb"
    fname = datasvc.get_file_blob(id)

    if type(fname) != str:
        errors.append("doesn't return the correct filename!")
    # check if file or folder exists locally, which means successfully downloaded
    if not os.path.exists(fname):
        errors.append("no file has been downloaded!")

    assert not errors, "errors occured:\n{}".format("\n".join(errors))


@pytest.mark.parametrize("space,expected", [
    ({'mettadatta': {'name': 'bad'}}, 400),
])
def test_create_space(datasvc, space, expected):
    response = datasvc.create_space(space)

    assert response.status_code == expected


@pytest.mark.parametrize("space_id,dataset_id,expected", [
    ("5c89287d5648c42a917569d8", "5a284f09c7d30d13bc0819a6", 200),
    ("5c89287d5648c42a917569d8", "5a284f09c7d30d13b0000000", 404),
    ("5c75bd1a9e503f2ea0000000", "5a284f09c7d30d13bc0819a6", 404),
])
def test_add_dataset_to_space(datasvc, space_id, dataset_id, expected):
    response = datasvc.add_dataset_to_space(space_id=space_id, dataset_id=dataset_id)

    assert response.status_code == expected


@pytest.mark.parametrize("space_id,space,expected", [
    ("5c89287d5648c42a917569d8", {'metadata': {'name': 'test-space'}}, 400),
    ("5c75bd1a9e503f2ea0500000", {'metadata': {'name': 'not found'}}, 404),
])
def test_update_space(datasvc, space_id, space, expected):
    """
    If the new name already exists, it will throw a bad request exception
    """
    response = datasvc.update_space(space_id=space_id, space=space)

    assert response.status_code == expected


def test_get_spaces(datasvc):
    metadata = datasvc.get_spaces()

    assert 'members' in metadata[0].keys()


def test_get_space(datasvc):
    response = datasvc.get_space("5c89287d5648c42a917569d8")

    assert response.status_code == 200
