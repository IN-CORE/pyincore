# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import os.path


from pyincore import IncoreClient

# from pyincore import DataService

user = {
    "service_url": "http://localhost:8080",
    "local": True,
    "username": "incrtest",
    "usergroups": ["incore_ncsa"],
}


def test_client_success():
    """
    testing successful login
    """
    client = IncoreClient(**user)
    assert "incrtest" in str(client.session.headers["x-auth-userinfo"])
    assert "incore_ncsa" in str(client.session.headers["x-auth-usergroup"])


def test_delete_repo_cache():
    client = IncoreClient(**user)
    hashed_repo_dir_path = client.hashed_svc_data_dir
    client.clear_cache()
    assert os.path.exists(hashed_repo_dir_path) is False


# def test_get_dataset_metadata():
#     client = IncoreClient(**user)
#     datasvc_internal = DataService(client)
#     dataset_id = "5a284f09c7d30d13bc0819a6"
#     metadata = datasvc_internal.get_dataset_metadata(dataset_id)
#     assert metadata["id"] == dataset_id
