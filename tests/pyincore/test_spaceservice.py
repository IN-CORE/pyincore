# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import os

import pytest

from pyincore import globals as pyglobals
from pyincore import IncoreClient, SpaceService


@pytest.fixture
def spacesvc(monkeypatch):
    return pytest.spacesvc


@pytest.mark.parametrize("space,expected", [
    ({'mettadatta': {'name': 'bad'}}, 400),
])
def test_create_space(spacesvc, space, expected):
    # assert that trying to create a space with invalid data throws an error
    with pytest.raises(Exception):
        assert spacesvc.create_space(space)


@pytest.mark.skip(reason="Need to debug")
def test_add_and_remove_member(spacesvc):
    # this is the id of the space "incrtest". If that space is deleted, this test will throw an error.
    space_id = "5c813be55648c42a9168d5c1"
    member_id = "5db87fbe6541940001b84f87"
    space = spacesvc.add_dataset_to_space(space_id=space_id, dataset_id=member_id)
    assert member_id in space["members"]


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


def test_get_space_by_name(spacesvc):
    space_name = "incore"
    space = spacesvc.get_space_by_name(space_name)
    assert "id" in space[0]
