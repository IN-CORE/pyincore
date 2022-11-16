# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import os

import pytest


@pytest.fixture
def datasvc_clowder():
    return pytest.datasvc_clowder


def test_get_dataset_blob_clowder(datasvc_clowder):
    errors = []
    dataset_id = "63755d06e4b0a2eb0196b5cb"
    fname = datasvc_clowder.get_dataset_blob(dataset_id, join=True)

    if type(fname) != str:
        errors.append("doesn't return the correct filename!")
    # check if file or folder exists locally, which means successfully downloaded
    if not os.path.exists(fname):
        errors.append("no file or folder has been downloaded!")

    assert not errors, "errors occured:\n{}".format("\n".join(errors))


def test_get_dataset_metadata_clowder(datasvc_clowder):
    dataset_id = "6375572ae4b0a2eb0196b56d"
    metadata = datasvc_clowder.get_dataset_metadata(dataset_id)
    assert len(metadata) == 2
