# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import json
import os


from pyincore.dataservice import DataService

from pyincore import Dataset
import networkx as nx


class NetworkDataset:
    """This class wraps around the Dataset class.

    Args:
        dataset (obj): The dataset object we want to extract the network data from.

    """

    def __init__(self, dataset: Dataset):
        if (
            dataset.format == "shp-network"
            and dataset.metadata["networkDataset"] is not None
        ):
            self.metadata = dataset.metadata
            self.data_type = dataset.metadata["dataType"]
            self.nodes = NetworkDataset._network_component_from_dataset(dataset, "node")
            self.links = NetworkDataset._network_component_from_dataset(dataset, "link")
            self.graph = NetworkDataset._network_component_from_dataset(
                dataset, "graph"
            )
        else:
            # TODO why do we need those
            self._metadata = None
            self._data_type = None
            self._links = None
            self._nodes = None
            self._graph = None

    @classmethod
    def from_data_service(cls, id: str, data_service: DataService):
        """Get Dataset from Data service, get metadata as well.

        Args:
            id (str): ID of the Dataset.
            data_service (obj): Data service.

        Returns:
            obj: network dataset

        """
        metadata = data_service.get_dataset_metadata(id)
        dataset = Dataset(metadata)
        dataset.cache_files(data_service)

        return cls(dataset)

    @classmethod
    def from_dataset(cls, dataset: Dataset):
        """Turn Dataset into network component

        Args:
            dataset (obj): Dataset Object.

        Returns:
            obj: network dataset

        """

        return cls(dataset)

    @classmethod
    def from_json_str(
        cls, json_str, data_service: DataService = None, folder_path=None
    ):
        """Get Dataset from json string.

        Args:
            json_str (str): JSON of the Dataset.
            data_service (obj): Data Service class.
            folder_path (str): File path.

        Returns:
            obj: network dataset

        """
        dataset = Dataset(json.loads(json_str))

        # download file and set local file path using metadata from services
        if data_service is not None:
            dataset.cache_files(data_service)
        # if there is local files associates with the dataset
        elif folder_path is not None:
            dataset.local_file_path = folder_path
        else:
            raise ValueError(
                "You have to either use data services, or given pass local file path."
            )

        return cls(dataset)

    @classmethod
    def from_files(
        cls,
        node_file_path,
        link_file_path,
        graph_file_path,
        network_data_type,
        link_data_type,
        node_data_type,
        graph_data_type,
    ):
        """Create Dataset from the file.

        Args:
            node_file_path (str): File path.
            link_file_path (str): File path.
            graph_file_path (str): File path.
            link_data_type (str): Link data type.
            node_data_type (str): Node data type.
            graph_data_type (str): Graph data type.

        Returns:
            obj: Dataset from file.

        """
        metadata = {
            "id": "",
            "dataType": network_data_type,
            "fileDescriptors": [],
            "networkDataset": {
                "link": {"dataType": link_data_type, "fileName": link_file_path},
                "node": {"dataType": node_data_type, "fileName": node_file_path},
                "graph": {"dataType": graph_data_type, "fileName": graph_file_path},
            },
            "format": "shp-network",
        }
        dataset = Dataset(metadata)
        dataset.local_file_path = ""
        return cls(dataset)

    @staticmethod
    def _network_component_from_dataset(dataset: Dataset, network_type="link"):
        """
        Create a dataset object for network from another dataset
        Args:
            dataset: network dataset
            network_type: link, node or graph

        Returns: network component in dataset object

        """
        network_component_filename = dataset.metadata["networkDataset"][network_type][
            "fileName"
        ]
        network_component_metadata = {
            "dataType": dataset.metadata["networkDataset"][network_type]["dataType"],
            "format": f"shp-{network_type}",
            "id": f"{dataset.id}-{network_type}",
            "fileDescriptors": [
                fd
                for fd in dataset.file_descriptors
                if fd["filename"].find(network_component_filename.split(".")[0]) != -1
            ],
        }
        network_component = Dataset(network_component_metadata)
        try:
            file_path = os.path.join(
                dataset.local_file_path, network_component_filename
            )
        except FileNotFoundError:
            raise FileNotFoundError("Invalid local file path.")
        network_component.local_file_path = file_path

        return network_component

    def get_nodes(self):
        return self.nodes.get_inventory_reader()

    def get_links(self):
        return self.links.get_inventory_reader()

    def get_graph(self):
        return self.graph.get_csv_reader()

    def get_graph_networkx(
        self,
        from_node_fld="fromnode",
        to_node_fld="tonode",
        directed=False,
        numeric=True,
    ):
        if directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()
        for edge in list(self.get_graph()):
            # the csv_reader in the get_graph turns integer into string; sometimes the network needs to be
            # constructed with integer as node id
            if numeric:
                G.add_edge(int(edge[from_node_fld]), int(edge[to_node_fld]))
            else:
                G.add_edge(edge[from_node_fld], edge[to_node_fld])

        return G
