import json

import pytest
from networkx import DiGraph

from pyincore import Dataset, NetworkDataset
import os


@pytest.fixture
def datasvc():
    return pytest.datasvc


def test_from_data_service(datasvc):
    dataset_id = "62719fc857f1d94b047447e6"
    network = NetworkDataset.from_data_service(dataset_id, datasvc)
    assert len(network.node.file_descriptors) == 4
    assert len(network.link.file_descriptors) == 4
    assert len(network.graph.file_descriptors) == 1
    assert network.node is not None
    assert network.graph is not None
    assert network.link is not None
    assert isinstance(network.node, Dataset)
    assert network.node.data_type == "incore:epnNodeVer1"
    assert network.link.data_type == "incore:epnLinkVer1"
    assert network.graph.data_type == "incore:epnGraph"
    assert network.node.local_file_path.find("epn_nodes.shp") != -1
    assert network.link.local_file_path.find("epn_links.shp") != -1
    assert network.graph.local_file_path.find("graph.csv") != -1


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
    link_file_path = "../data/network/epn_links.shp"
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


def test_get_node_inventory(datasvc):
    dataset_id = "62719fc857f1d94b047447e6"
    network = NetworkDataset.from_data_service(dataset_id, datasvc)
    nodes = list(network.get_node_inventory())
    assert nodes[0]['properties']["guid"] == "9c39623d-920e-49e6-b272-83b2ec954b84"


def test_get_link_inventory(datasvc):
    dataset_id = "62719fc857f1d94b047447e6"
    network = NetworkDataset.from_data_service(dataset_id, datasvc)
    links = list(network.get_link_inventory())
    assert links[0]['properties']["guid"] == "a4f63126-bb4b-45e7-9029-47984155f859"


def test_get_graph_table(datasvc):
    dataset_id = "62719fc857f1d94b047447e6"
    network = NetworkDataset.from_data_service(dataset_id, datasvc)
    graph = list(network.get_graph_table())
    assert graph[0]["linkid"] == "1"
    assert graph[0]["fromnode"] == "1"
    assert graph[0]["tonode"] == "2"


def test_get_networkx_graph(datasvc):
    dataset_id = "62719fc857f1d94b047447e6"
    network = NetworkDataset.from_data_service(dataset_id, datasvc)
    networkx_graph, networkx_coords = network.get_networkx_graph(fromnode_fldname="fromnode",
                                                                    tonode_fldname="tonode", is_directed=True)
    assert isinstance(networkx_graph, DiGraph)
    assert networkx_coords[0] == (-97.4814000203988, 35.26650000753716)


def test_plot_network_graph(datasvc):
    dataset_id = "62719fc857f1d94b047447e6"
    network = NetworkDataset.from_data_service(dataset_id, datasvc)
    networkx_graph, networkx_coords = network.get_networkx_graph(fromnode_fldname="fromnode",
                                                                 tonode_fldname="tonode", is_directed=True)
    graph_png_fname = "test_graph.png"
    plt = NetworkDataset.plot_network_graph(networkx_graph, networkx_coords)
    plt.savefig(graph_png_fname)
    assert os.path.exists(graph_png_fname)
