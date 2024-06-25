import json
import os

import pytest
from networkx import Graph

from pyincore import Dataset, NetworkDataset, BaseAnalysis
from pyincore.globals import PYINCORE_ROOT_FOLDER


@pytest.fixture
def datasvc():
    return pytest.datasvc


@pytest.fixture
def client():
    return pytest.client


def test_from_data_service(datasvc):
    dataset_id = "62719fc857f1d94b047447e6"
    network = NetworkDataset.from_data_service(dataset_id, datasvc)
    assert len(network.nodes.file_descriptors) >= 4
    assert len(network.links.file_descriptors) >= 4
    assert len(network.graph.file_descriptors) == 1
    assert network.nodes is not None
    assert network.graph is not None
    assert network.links is not None
    assert isinstance(network.nodes, Dataset)
    assert network.nodes.data_type == "incore:epnNodeVer1"
    assert network.links.data_type == "incore:epnLinkVer1"
    assert network.graph.data_type == "incore:epnGraph"
    assert network.nodes.local_file_path.find("epn_nodes.shp") != -1
    assert network.links.local_file_path.find("epn_links.shp") != -1
    assert network.graph.local_file_path.find("graph.csv") != -1


def test_from_json_str():
    print(PYINCORE_ROOT_FOLDER)
    with open(os.path.join(PYINCORE_ROOT_FOLDER, "tests/data/network/network_dataset.json"), "r") as f:
        json_dict = json.load(f)
    network = NetworkDataset.from_json_str(json.dumps(json_dict), folder_path="../data/network/")
    assert network.nodes is not None
    assert network.graph is not None
    assert network.links is not None
    assert isinstance(network.nodes, Dataset)
    assert network.nodes.data_type == json_dict["networkDataset"]["node"]["dataType"]
    assert network.links.data_type == json_dict["networkDataset"]["link"]["dataType"]
    assert network.graph.data_type == json_dict["networkDataset"]["graph"]["dataType"]
    assert network.nodes.local_file_path.find("epn_nodes.shp") != -1
    assert network.links.local_file_path.find("epn_links.shp") != -1
    assert network.graph.local_file_path.find("graph.csv") != -1


def test_from_files():
    node_file_path = "../data/network/epn_nodes.shp"
    link_file_path = "../data/network/epn_links.shp"
    graph_file_path = "../data/network/graph.csv"
    network_data_type = "incore:network"
    link_data_type = "incore:epnLinkVer1"
    node_data_type = "incore:epnNodeVer1"
    graph_data_type = "incore:epnGraph"
    network = NetworkDataset.from_files(node_file_path, link_file_path, graph_file_path, network_data_type,
                                        link_data_type, node_data_type, graph_data_type)
    assert network.nodes is not None
    assert network.graph is not None
    assert network.links is not None
    assert isinstance(network.nodes, Dataset)
    assert network.nodes.data_type == node_data_type
    assert network.links.data_type == link_data_type
    assert network.graph.data_type == graph_data_type
    assert network.nodes.local_file_path.find("epn_nodes.shp") != -1
    assert network.links.local_file_path.find("epn_links.shp") != -1
    assert network.graph.local_file_path.find("graph.csv") != -1


def test_get_node_inventory(datasvc):
    dataset_id = "62719fc857f1d94b047447e6"
    network = NetworkDataset.from_data_service(dataset_id, datasvc)
    nodes = list(network.get_nodes())
    assert nodes[0]['properties']["guid"] == "9c39623d-920e-49e6-b272-83b2ec954b84"


def test_get_link_inventory(datasvc):
    dataset_id = "62719fc857f1d94b047447e6"
    network = NetworkDataset.from_data_service(dataset_id, datasvc)
    links = list(network.get_links())
    assert links[0]['properties']["guid"] == "a4f63126-bb4b-45e7-9029-47984155f859"


def test_get_graph_table(datasvc):
    dataset_id = "62719fc857f1d94b047447e6"
    network = NetworkDataset.from_data_service(dataset_id, datasvc)
    graph = list(network.get_graph())
    assert graph[0]["linkid"] == "1"
    assert graph[0]["fromnode"] == "1"
    assert graph[0]["tonode"] == "2"


def test_get_graph_networkx(datasvc):
    dataset_id = "62719fc857f1d94b047447e6"
    network = NetworkDataset.from_data_service(dataset_id, datasvc)
    graph_nx = network.get_graph_networkx()
    assert isinstance(graph_nx, Graph)


def test_set_input_dataset(datasvc, client):
    dataset_id = "62719fc857f1d94b047447e6"
    network = NetworkDataset.from_data_service(dataset_id, datasvc)
    base_analysis = BaseAnalysis(client)
    base_analysis.input_datasets = {"network": {"spec": {
                    'id': 'network',
                    'required': True,
                    'description': 'network',
                    'type': ['incore:epnNetwork'],
                }, "value": None}}
    assert base_analysis.set_input_dataset("network", network) is True
