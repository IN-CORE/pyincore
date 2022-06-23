# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import pyincore.globals as pyglobals
import os
import pytest

from pyincore.utils.networkutil import NetworkUtil as networkutil
from pyincore import NetworkDataset


@pytest.fixture
def datasvc():
    return pytest.datasvc


@pytest.fixture
def client():
    return pytest.client


def test_build_link_by_node():
    node_file_path = os.path.join(pyglobals.PYINCORE_ROOT_FOLDER, "tests/data/network/epn_nodes.shp")
    graph_file_path = os.path.join(pyglobals.PYINCORE_ROOT_FOLDER, "tests/data/network/graph.csv")
    out_link_file_path = os.path.join(pyglobals.PYINCORE_ROOT_FOLDER, "tests/data/network/out_links.shp")

    node_id = "NODENWID"

    networkutil.build_link_by_node(node_file_path, graph_file_path, node_id, out_link_file_path)

    assert True


def test_build_node_by_link():
    link_file_path = os.path.join(pyglobals.PYINCORE_ROOT_FOLDER, "tests/data/network/epn_links.shp")
    out_node_file_path = os.path.join(pyglobals.PYINCORE_ROOT_FOLDER, "tests/data/network/out_nodes.shp")
    out_graph_file_path = os.path.join(pyglobals.PYINCORE_ROOT_FOLDER, "tests/data/network/out_graph.csv")

    link_id = "linknwid"
    fromnode = "fromnode"
    tonode = "tonode"

    networkutil.build_node_by_link(link_file_path, link_id, fromnode, tonode, out_node_file_path,
                                   out_graph_file_path)

    assert True


def test_create_network_graph_from_link():
    link_file_path = os.path.join(pyglobals.PYINCORE_ROOT_FOLDER, "tests/data/network/epn_links.shp")

    fromnode = "fromnode"
    tonode = "tonode"

    graph, coords = networkutil.create_network_graph_from_link(link_file_path, fromnode, tonode)

    if graph is not None and coords is not None:
        assert True


def test_validate_network_node_ids(datasvc):
    epn_network_id = "62719fc857f1d94b047447e6"
    network_dataset = NetworkDataset.from_data_service(epn_network_id, datasvc)
    node_id = "NODENWID"
    fromnode = "fromnode"
    tonode = "tonode"
    validate = networkutil.validate_network_node_ids(network_dataset, fromnode, tonode, node_id)

    assert validate
