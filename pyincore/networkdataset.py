# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import json
import os

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
    def from_json_str(cls, json_str, data_service: DataService = None, file_path=None):
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
        elif file_path is not None:
            dataset.local_file_path = file_path
        else:
            raise ValueError("You have to either use data services, or given pass local file path.")

        return cls(dataset)

    @classmethod
    def from_file(cls, file_path, data_type):
        """Create Dataset from the file.

        Args:
            file_path (str): File path.
            data_type (str): Data type.

        Returns:
            obj: Dataset from file.

        """
        metadata = {"dataType": data_type,
                    "format": '',
                    "fileDescriptors": [],
                    "id": file_path}
        dataset = Dataset(metadata)
        dataset.local_file_path = file_path
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
        network_component_metadata = {
            "dataType": dataset.metadata['networkDataset'][network_type]["networkType"],
            "format": f"shp-{network_type}"
        }
        network_component = Dataset(network_component_metadata)
        try:
            link_file_path = os.path.join(dataset.local_file_path,
                                          dataset.metadata['networkDataset'][network_type]["fileName"])
        except FileNotFoundError:
            raise FileNotFoundError("Invalid local file path.")
        network_component.local_file_path = link_file_path

        return network_component

    @staticmethod
    def get_inventory_reader(self):
        """ getter """
        filename = self.file_path
        if os.path.isdir(filename):
            layers = fiona.listlayers(filename)
            if len(layers) > 0:
                # for now, open the first shapefile
                return fiona.open(filename, layer=layers[0])
        else:
            return fiona.open(filename)