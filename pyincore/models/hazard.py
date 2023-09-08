# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import glob
import json
import os

import fiona
import numpy
import rasterio
import warnings
from pyincore import HazardService

warnings.filterwarnings("ignore", "", UserWarning)


class Hazard:
    """Hazard.

    Args:
        metadata (dict): Hazard metadata.

    """

    def __init__(self, metadata):

        self.id = metadata["id"] if "id" in metadata else ""
        self.name = metadata['name'] if "name" in metadata else ""
        self.description = metadata['description'] if "description" in metadata else ""
        self.date = metadata['date'] if "date" in metadata else ""
        self.creator = metadata["creator"] if "creator" in metadata else ""
        self.spaces = metadata["spaces"] if "spaces" in metadata else []
