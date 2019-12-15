# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from jose import jwt
from pyincore import IncoreClient
from pyincore import SpaceService

import pytest


@pytest.fixture
def spacesvc(monkeypatch):
    try:
        with open(".incorepw", 'r') as f:
            cred = f.read().splitlines()
    except EnvironmentError:
        assert False
    credentials = jwt.decode(cred[0], cred[1])
    monkeypatch.setattr("builtins.input", lambda x: credentials["username"])
    monkeypatch.setattr("getpass.getpass", lambda y: credentials["password"])
    client = IncoreClient()
    return SpaceService(client)


@pytest.mark.parametrize("space,expected", [
    ({'mettadatta': {'name': 'bad'}}, 400),
])
def test_create_space(spacesvc, space, expected):
    # assert that trying to create a space with invalid data throws an error
    with pytest.raises(Exception):
        assert spacesvc.create_space(space)


def test_add_dataset_to_space(spacesvc):
    # this is the id of the space "incrtest". If that space is deleted, this test will throw an error.
    space_id = "5c813be55648c42a9168d5c1"
    member_id = "5a284f83c7d30d13bc0827ec"
    space = spacesvc.add_dataset_to_space(space_id=space_id, dataset_id=member_id)
    assert member_id in space["members"]
    # TODO: add a test_remove_dataset_to_space


@pytest.mark.parametrize("space_id,space,expected", [
    ("5c89287d5648c42a917569d8", {'metadata': {'name': 'test-space'}}, 400),
    ("5c75bd1a9e503f2ea0500000", {'metadata': {'name': 'not found'}}, 404),
])
def test_update_space(spacesvc, space_id, space, expected):
    """
    If the new name already exists, it will throw a bad request exception
    """
    with pytest.raises(Exception):
        assert spacesvc.update_space(space_id=space_id, space=space)


def test_get_spaces(spacesvc):
    metadata = spacesvc.get_spaces()
    assert 'members' in metadata[0].keys()


def test_get_space(spacesvc):
    space_id = "5c813be55648c42a9168d5c1"
    space = spacesvc.get_space_by_id(space_id)
    assert "id" in space and space["id"] == space_id
