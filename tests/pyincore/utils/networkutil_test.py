import json
import os
from pathlib import Path

import pytest
from networkx import Graph

from pyincore.utils.networkutil import NetworkUtil as networkutil
from pyincore import Dataset, NetworkDataset, BaseAnalysis
from pyincore.globals import PYINCORE_ROOT_FOLDER



@pytest.fixture
def datasvc():
    return pytest.datasvc


@pytest.fixture
def client():
    return pytest.client


def test_from_files():
    print(PYINCORE_ROOT_FOLDER)
    # with open(os.path.join(PYINCORE_ROOT_FOLDER, "tests/data/network/network_dataset.json"), "r") as f:
    #     json_dict = json.load(f)
    node_file_path = os.path.join(PYINCORE_ROOT_FOLDER, "tests/data/network/epn_nodes.shp")
    link_file_path = os.path.join(PYINCORE_ROOT_FOLDER, "tests/data/network/epn_links.shp")
    graph_file_path = os.path.join(PYINCORE_ROOT_FOLDER, "tests/data/network/graph.csv")
    out_node_file_path = os.path.join(PYINCORE_ROOT_FOLDER, "tests/data/network/out_nodes.shp")
    out_link_file_path = os.path.join(PYINCORE_ROOT_FOLDER, "tests/data/network/out_links.shp")

    link_id = "NODENWID"
    node_id = "NODENWID"

    networkutil.build_link_by_node(node_file_path, graph_file_path, node_id, out_link_file_path)
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
    test_from_files()
