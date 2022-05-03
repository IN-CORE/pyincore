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
