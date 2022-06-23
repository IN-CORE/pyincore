import json
import os
from pathlib import Path

import pytest
from networkx import Graph

from pyincore.utils.networkutil import NetworkUtil as networkutil
from pyincore import Dataset, NetworkDataset, BaseAnalysis
from pyincore import IncoreClient
import pyincore.globals as pyglobals

import json
import os
from pathlib import Path

import pytest
from networkx import Graph

from pyincore import DataService, NetworkDataset, BaseAnalysis
from pyincore.globals import PYINCORE_ROOT_FOLDER


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


def test_validate_network_node_ids():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    datasvc = DataService(client)
    epn_network_id = "62719fc857f1d94b047447e6"
    network_dataset = NetworkDataset.from_data_service(epn_network_id, datasvc)
    node_id = "NODENWID"
    fromnode = "fromnode"
    tonode = "tonode"
    networkutil.validate_network_node_ids(network_dataset, fromnode, tonode, node_id)

    # network_data_type = "incore:network"
    # link_data_type = "incore:epnLinkVer1"
    # node_data_type = "incore:epnNodeVer1"
    # graph_data_type = "incore:epnGraph"
    # network = NetworkDataset.from_files(node_file_path, link_file_path, graph_file_path, network_data_type,
    #                                     link_data_type, node_data_type, graph_data_type)
    # assert network.nodes is not None
    # assert network.graph is not None
    # assert network.links is not None
    # assert isinstance(network.nodes, Dataset)
    # assert network.nodes.data_type == node_data_type
    # assert network.links.data_type == link_data_type
    # assert network.graph.data_type == graph_data_type
    # assert network.nodes.local_file_path.find("epn_nodes.shp") != -1
    # assert network.links.local_file_path.find("epn_links.shp") != -1
    # assert network.graph.local_file_path.find("graph.csv") != -1

if __name__ == '__main__':
    # test_create_network_graph_from_link()
    test_validate_network_node_ids()()
