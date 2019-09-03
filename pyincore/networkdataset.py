# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import os
from pyincore import Dataset
from pyincore import NetworkData


class NetworkDataset:
    """ This class wraps around the Dataset class.

    Args:
        dataset (obj): The dataset object we want to extract the network data from.

    """

    def __init__(self, dataset: Dataset):
        if dataset.format == 'shp-network' and dataset.metadata['networkDataset'] is not None:
            try:
                file_path = os.path.join(dataset.local_file_path,
                                         dataset.metadata['networkDataset']["link"]["fileName"])
            except FileNotFoundError:
                raise FileNotFoundError("Invalid local file path.")
            self.link = NetworkData(network_type=dataset.metadata['networkDataset']["link"]["networkType"],
                                    file_path=file_path)
            self.node = NetworkData(network_type=dataset.metadata['networkDataset']["node"]["networkType"],
                                    file_path=os.path.join(dataset.local_file_path,
                                                           dataset.metadata['networkDataset']["node"]["fileName"]))
            self.graph = NetworkData(network_type=dataset.metadata['networkDataset']["graph"]["networkType"],
                                     file_path=os.path.join(dataset.local_file_path,
                                                            dataset.metadata['networkDataset']["graph"]["fileName"]))
        else:
            self._network_data = None
            self._link = None
            self._node = None
            self._graph = None
