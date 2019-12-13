# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from jose import jwt
from pyincore import DataService, IncoreClient, Dataset, NetworkDataset, NetworkData

import ast
import os
import pytest
import re


@pytest.fixture
def datasvc(monkeypatch):
    try:
        with open(".incorepw", 'r') as f:
            cred = f.read().splitlines()
            f.close()
    except EnvironmentError:
        assert False
    credentials = jwt.decode(cred[0], cred[1])
    monkeypatch.setattr("builtins.input", lambda x: credentials["username"])
    monkeypatch.setattr("getpass.getpass", lambda y: credentials["password"])
    client = IncoreClient(token_file_name=".incrtesttoken")
    return DataService(client)


def test_get_dataset_metadata(datasvc):
    dataset_id = "5a284f0ac7d30d13bc0819c4"
    metadata = datasvc.get_dataset_metadata(dataset_id)
    assert metadata['id'] == dataset_id


def test_get_dataset_files_metadata(datasvc):
    errors = []
    dataset_id = "5a284f0ac7d30d13bc0819c4"
    metadata = datasvc.get_dataset_metadata(dataset_id)
    fileDescriptor = datasvc.get_dataset_files_metadata(dataset_id)

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
    dataset_id = "5a284f0ac7d30d13bc0819c4"
    fname = datasvc.get_dataset_blob(dataset_id, join=True)

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
    with open('geotif_sample.json', 'r') as file:
        dataset_prop = ast.literal_eval(file.read())
    response = datasvc.create_dataset(dataset_prop)

    if 'id' not in response:
        assert False

    dataset_id = response['id']
    print('dataset is created with id ' + dataset_id)
    files = ['geotif_sample.tif']

    response = datasvc.add_files_to_dataset(dataset_id, files)
    assert response['id'] == dataset_id

    r = datasvc.delete_dataset(dataset_id)
    assert r["id"] == dataset_id


def test_create_dataset_shpfile(datasvc):
    """
    Testing create dataset with shapefile
    """
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
    assert response['id'] == dataset_id

    r = datasvc.delete_dataset(dataset_id)
    assert r["id"] == dataset_id


def test_update_dataset(datasvc):
    dataset_id = "5ace7322ec230944f695f5cf"
    property_name = "title"
    property_value = "test update dataset"
    response = datasvc.update_dataset(dataset_id, property_name, property_value)

    assert response[property_name] == property_value


def test_get_files(datasvc):
    metadata = datasvc.get_files()
    assert 'id' in metadata[0]


def test_get_file_metadata(datasvc):
    metadata = datasvc.get_file_metadata("5a284f24c7d30d13bc081adb")
    assert metadata['id'] == "5a284f24c7d30d13bc081adb"


def test_get_file_blob(datasvc):
    errors = []
    dataset_id = "5a284f24c7d30d13bc081adb"
    fname = datasvc.get_file_blob(dataset_id)

    if type(fname) != str:
        errors.append("doesn't return the correct filename!")
    # check if file or folder exists locally, which means successfully downloaded
    if not os.path.exists(fname):
        errors.append("no file has been downloaded!")

    assert not errors, "errors occured:\n{}".format("\n".join(errors))


def test_create_network_dataset(datasvc):
    # assert that we can't create a network dataset with an invalid path
    dataset = Dataset(datasvc.get_dataset_metadata("5cf696b05648c477129bfc21"))
    pytest.raises(TypeError, NetworkDataset, dataset)

    # assert we can successfully create a network dataset
    dataset = Dataset.from_data_service("5cf696b05648c477129bfc21", datasvc)
    network_dataset = NetworkDataset(dataset)
    assert network_dataset.graph is not None
    assert network_dataset.link is not None
    assert network_dataset.node is not None


def test_create_network_data(datasvc):
    dataset = Dataset.from_data_service("5cf696b05648c477129bfc21", datasvc)
    network_dataset = NetworkDataset(dataset)

    assert network_dataset.link is not None
    assert network_dataset.node is not None
    assert network_dataset.graph is not None

    # test that we can't create a network data object with an invalid file path
    with pytest.raises(FileNotFoundError):
        NetworkData(network_type="", file_path="")
    with pytest.raises(FileNotFoundError):
        NetworkData(network_type="test-type", file_path="test-file")
    with pytest.raises(FileNotFoundError):
        NetworkData(network_type="test-type", file_path="test-file")

