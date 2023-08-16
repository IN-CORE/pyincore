# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import json
import os

import pytest
from requests.exceptions import HTTPError

from pyincore import globals as pyglobals
from pyincore import SemanticService

from pyincore.globals import LOGGER

logger = LOGGER

@pytest.fixture
def semanticsvc():
    return pytest.semanticsvc


def test_get_all_semantic_types(semanticsvc):
    order = "asc"
    skip = 0
    limit = 10

    # get all semantic types without hyperlink
    hyperlink = False
    semantic_types = semanticsvc.get_all_semantic_types(
        hyperlink=hyperlink, 
        order=order, 
        skip=skip, 
        limit=limit
    )
    assert len(semantic_types) == limit and len(semantic_types[0].split("/")) <= 1, "Should not have hyperlink"

    # get all semantic types with hyperlink
    hyperlink = True
    semantic_types = semanticsvc.get_all_semantic_types(
        hyperlink=hyperlink, 
        order=order, 
        skip=skip, 
        limit=limit
    )
    assert len(semantic_types) == limit and len(semantic_types[0].split("/")) > 1, "Should have hyperlink"


def test_get_semantic_type_by_name(semanticsvc):
    semantic_type_exists = "ergo:bridgeDamage"
    semantic_type_not_exists = "bridgeDamage"

    # find semantic type by name which exists
    semantic_types = semanticsvc.get_semantic_type_by_name(semantic_type_exists)
    # Checks semantic dictionary is not empty
    assert type(semantic_types) == dict and bool(dict), f"Should find one semantic type as {semantic_type_exists} exists"
    # find semantic type by name which does not exist
    # this should raise error
    with pytest.raises(Exception) as excinfo:
        semantic_types = semanticsvc.get_semantic_type_by_name(semantic_type_not_exists)
        assert excinfo == HTTPError, f"Should raise HTTPError as {semantic_type_not_exists} does not exist"


def test_search_semantic_types(semanticsvc):
    search_term_exists = "wildFireDamageRaster"
    search_term_not_exists = "asdwerueidj"
    # search for term that should find an entry
    semantic_types = semanticsvc.search_semantic_type(search_term_exists)
    assert len(semantic_types) > 0, f"Should find at least one semantic type as {search_term_exists} exists"
    # search for term that should not find an entry
    semantic_types = semanticsvc.search_semantic_type(search_term_not_exists)
    assert len(semantic_types) == 0, f"Should not find any semantic type as {search_term_not_exists} does not exist"

