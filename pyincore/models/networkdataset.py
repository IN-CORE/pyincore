# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import json
import os
import networkx as nx
import matplotlib.pyplot as plt
from networkx import DiGraph, Graph
from typing import Union

from pyincore.dataservice import DataService

from pyincore import Dataset


class NetworkDataset:
    """ This class wraps around the Dataset class.

    Args:
        dataset (obj): The dataset object we want to extract the network data from.

    """

    def __init__(self, dataset: Dataset):
        if dataset.format == 'shp-network' and dataset.metadata['networkDataset'] is not None:
            self.node = NetworkDataset._network_component_from_dataset(dataset, "node")
            self.link = NetworkDataset._network_component_from_dataset(dataset, "link")
            self.graph = NetworkDataset._network_component_from_dataset(dataset, "graph")
        else:
            self._network_data = None
            self._link = None
            self._node = None
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
    def from_json_str(cls, json_str, data_service: DataService = None, folder_path=None):
        """Get Dataset from json string.

        Args:
            json_str (str): JSON of the Dataset.
            data_service (obj): Data Service class.
            file_path (str): File path.

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
            raise ValueError("You have to either use data services, or given pass local file path.")

        return cls(dataset)

    @classmethod
    def from_files(cls, node_file_path, link_file_path, graph_file_path, link_data_type,
                   node_data_type,
                   graph_data_type):
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
            "dataType": "",
            "fileDescriptors": [],
            "networkDataset": {
                "link": {
                    "networkType": link_data_type,
                    "fileName": link_file_path
                },
                "node": {
                    "networkType": node_data_type,
                    "fileName": node_file_path
                },
                "graph": {
                    "networkType": graph_data_type,
                    "fileName": graph_file_path
                }
            },
            "format": "shp-network"
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
        network_component_filename = dataset.metadata['networkDataset'][network_type]["fileName"]
        network_component_metadata = {
            "dataType": dataset.metadata['networkDataset'][network_type]["networkType"],
            "format": f"shp-{network_type}",
            "id": f"{dataset.id}-{network_type}",
            "fileDescriptors": [fd for fd in dataset.file_descriptors if fd["filename"].find(
                network_component_filename.split(".")[0]) != -1]
        }
        network_component = Dataset(network_component_metadata)
        try:
            file_path = os.path.join(dataset.local_file_path, network_component_filename)
        except FileNotFoundError:
            raise FileNotFoundError("Invalid local file path.")
        network_component.local_file_path = file_path

        return network_component

    def get_node_inventory(self):
        return self.node.get_inventory_reader()

    def get_link_inventory(self):
        return self.link.get_inventory_reader()

    def get_graph_table(self):
        return self.graph.get_csv_reader()

    def get_networkx_graph(self, fromnode_fldname="fromnode", tonode_fldname="tonode", is_directed=False):
        """Create network graph from field.

        Args:
            fromnode_fldname (str): Line feature, from node field name.
            tonode_fldname (str): Line feature, to node field name.
            is_directed (bool, optional (Defaults to False)): Graph type. True for directed Graph,
                False for Graph.

        Returns:
            obj: A graph from field.
            dict: Coordinates.

        """
        if is_directed:
            graph = nx.DiGraph()
        else:
            graph = nx.Graph()

        for row in self.graph.get_csv_reader():
            graph.add_edge(row[fromnode_fldname], row[tonode_fldname])

        # TODO coordination part is so messy
        # TODO the node name shouldn't be hard coded integers from 0 to len(node)
        # initialize coords dictionary
        node_length = len(list(self.node.get_inventory_reader()))
        coords = dict((str(i), None) for i in range(1, node_length))

        # create coordinates
        for line_feature in list(self.link.get_inventory_reader()):
            if fromnode_fldname in line_feature["properties"]:
                from_node_val = line_feature['properties'][fromnode_fldname]
            elif fromnode_fldname.lower() in line_feature["properties"]:
                from_node_val = line_feature['properties'][fromnode_fldname.lower()]
            if tonode_fldname in line_feature["properties"]:
                to_node_val = line_feature['properties'][tonode_fldname]
            elif tonode_fldname.lower() in line_feature["properties"]:
                to_node_val = line_feature['properties'][tonode_fldname.lower()]
            line_geom = (line_feature['geometry'])
            coords_list = line_geom.get('coordinates')
            from_coord = coords_list[0]
            to_coord = coords_list[1]
            coords[str(from_node_val)] = from_coord
            coords[str(to_node_val)] = to_coord

        return graph, coords

    @staticmethod
    def plot_network_graph(graph: Union[Graph, DiGraph], coords: dict):
        nx.draw_networkx_nodes(graph, coords, cmap=plt.get_cmap('jet'), node_size=100, node_color='g')
        nx.draw_networkx_labels(graph, coords)
        nx.draw_networkx_edges(graph, coords, edge_color='r', arrows=True)
        plt.show()
        return plt
