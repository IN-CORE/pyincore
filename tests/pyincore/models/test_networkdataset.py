import json

import pytest

from pyincore import Dataset, IncoreClient, DataService, NetworkDataset


# @pytest.fixture
# def datasvc():
#     return pytest.datasvc


def test_from_data_service():
    client = IncoreClient()
    datasvc = DataService(client)
    dataset_id = "5f454c6fef0df52132b65b0b"
    network = NetworkDataset.from_data_service(dataset_id, datasvc)
    assert len(network.node.file_descriptors) == 4
    assert len(network.link.file_descriptors) == 4
    assert len(network.graph.file_descriptors) == 1
    assert network.node is not None
    assert network.graph is not None
    assert network.link is not None
    assert isinstance(network.node, Dataset)
    assert network.node.data_type == "water facility"
    assert network.link.data_type == "pipeline"
    assert network.graph.data_type == "table"
    assert network.node.local_file_path != ""


def test_from_json_str():
    with open("/Users/cwang138/Documents/INCORE-2.0/pyincore/tests/data/network/network_dataset.json", "r") as f:
        json_dict = json.load(f)
    network = NetworkDataset.from_json_str(json.dumps(json_dict), folder_path="../data/network/")
    assert network.node is not None
    assert network.graph is not None
    assert network.link is not None
    assert isinstance(network.node, Dataset)
    assert network.node.data_type == json_dict["networkDataset"]["node"]["networkType"]
    assert network.link.data_type == json_dict["networkDataset"]["link"]["networkType"]
    assert network.graph.data_type == json_dict["networkDataset"]["graph"]["networkType"]
    assert network.node.local_file_path.find("epn_nodes.shp") != -1
    assert network.link.local_file_path.find("epn_links.shp") != -1
    assert network.graph.local_file_path.find("graph.csv") != -1


def test_from_files():
    node_file_path = "../data/network/epn_nodes.shp"
    link_file_path = "../data/network/epn_link.shp"
    graph_file_path = "../data/network/graph.csv"
    link_data_type = "incore:epnLinkVer1"
    node_data_type = "incore:epnNodeVer1"
    graph_data_type = "incore:epnGraph"
    network = NetworkDataset.from_files(node_file_path, link_file_path, graph_file_path, link_data_type,
                                        node_data_type, graph_data_type)
    assert network.node is not None
    assert network.graph is not None
    assert network.link is not None
    assert isinstance(network.node, Dataset)
    assert network.node.data_type == node_data_type
    assert network.link.data_type == link_data_type
    assert network.graph.data_type == graph_data_type
    assert network.node.local_file_path.find("epn_nodes.shp") != -1
    assert network.link.local_file_path.find("epn_links.shp") != -1
    assert network.graph.local_file_path.find("graph.csv") != -1
