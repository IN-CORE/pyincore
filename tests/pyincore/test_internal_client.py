# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import os.path


from pyincore import IncoreInternalClient


user = {
    "username": "incrtest",
    "usergroups": ["incore_admin", "incore_user", "ncsa_admin"],
}


def test_client_success():
    """
    testing successful login
    """
    client = IncoreInternalClient(**user)
    assert "incrtest" in str(client.session.headers["x-auth-userinfo"])
    assert "incore_admin" in str(client.session.headers["x-auth-usergroup"])


def test_delete_repo_cache():
    client = IncoreInternalClient(**user)
    hashed_repo_dir_path = client.hashed_svc_data_dir
    client.clear_cache()
    assert os.path.exists(hashed_repo_dir_path) is False
