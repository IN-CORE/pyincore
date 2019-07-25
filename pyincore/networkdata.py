# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import errno
import os
import fiona


class NetworkData:
    def __init__(self, network_type: str, file_path: str):
        self.network_type = network_type
        if os.path.exists(file_path):
            self.file_path = file_path
        else:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), file_path)

    def get_inventory_reader(self):
        filename = self.file_path
        if os.path.isdir(filename):
            layers = fiona.listlayers(filename)
            if len(layers) > 0:
                # for now, open the first shapefile
                return fiona.open(filename, layer=layers[0])
        else:
            return fiona.open(filename)
