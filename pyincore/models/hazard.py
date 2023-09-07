# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import csv
import glob
import json
import os

import fiona
import numpy
import pandas as pd
import geopandas as gpd
import rasterio
import warnings
from pyincore import DataService, HazardService

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

        self.readers = {}

    @classmethod
    def from_hazard_service(cls, id: str, hazard_service: HazardService):
        """Get Hazard from hazard service, get metadata as well.

        Args:
            id (str): ID of the Hazard.
            hazard_service (obj): Hazard service.

        Returns:
            obj: Hazard from Data service.

        """
        metadata = hazard_service(id)
        instance = cls(metadata)
        instance.cache_files(hazard_service)
        return instance

    @classmethod
    def from_json_str(cls, json_str, hazard_service: DataService = None, file_path=None):
        """Get Hazard from json string.

        Args:
            json_str (str): JSON of the Hazard.
            hazard_service (obj): Data Service class.
            file_path (str): File path.

        Returns:
            obj: Hazard from JSON.

        """
        instance = cls(json.loads(json_str))

        # download file and set local file path using metadata from services
        if hazard_service is not None:
            instance.cache_files(hazard_service)

        # if there is local files associates with the hazard
        elif file_path is not None:
            instance.local_file_path = file_path

        else:
            raise ValueError("You have to either use data services, or given pass local file path.")

        return instance

    @classmethod
    def from_file(cls, file_path, data_type):
        """Get Hazard from the file.

        Args:
            file_path (str): File path.
            data_type (str): Data type.

        Returns:
            obj: Hazard from file.

        """
        metadata = {"dataType": data_type,
                    "format": '',
                    "fileDescriptors": [],
                    "id": file_path}
        instance = cls(metadata)
        instance.local_file_path = file_path
        return instance

    @classmethod
    def from_json_data(cls, result_data, name, data_type):
        """Get Hazard from JSON data.

        Args:
            result_data (obj): Result data and metadata.
            name (str): A JSON filename.
            data_type (str): Incore data type, e.g. incore:xxxx or ergo:xxxx

        Returns:
            obj: Hazard from file.

        """
        if len(result_data) > 0:
            with open(name, 'w') as json_file:
                json_dumps_str = json.dumps(result_data, indent=4)
                json_file.write(json_dumps_str)
        return Hazard.from_file(name, data_type)

    def get_inventory_reader(self):
        """Utility method for reading different standard file formats: Set of inventory.

        Returns:
            obj: A Fiona object.

        """
        filename = self.local_file_path
        if os.path.isdir(filename):
            layers = fiona.listlayers(filename)
            if len(layers) > 0:
                # for now, open a first shapefile
                return fiona.open(filename, layer=layers[0])
        else:
            return fiona.open(filename)

    def get_json_reader(self):
        """Utility method for reading different standard file formats: json reader.

        Returns:
            obj: A json model data.

        """
        if "json" not in self.readers:
            filename = self.local_file_path
            if os.path.isdir(filename):
                files = glob.glob(filename + "/*.json")
                if len(files) > 0:
                    filename = files[0]

            with open(filename, 'r') as f:
                return json.load(f)

        return self.readers["json"]

    def get_raster_value(self, location):
        """Utility method for reading different standard file formats: raster value.

        Args:
            location (obj): A point defined as location.x and location.y.

        Returns:
            numpy.array: Hazard values.

        """
        if "raster" not in self.readers:
            filename = self.local_file_path
            self.readers["raster"] = rasterio.open(filename)

        hazard = self.readers["raster"]
        row, col = hazard.index(location.x, location.y)
        # assume that there is only 1 band
        data = hazard.read(1)
        if row < 0 or col < 0 or row >= hazard.height or col >= hazard.width:
            return 0.0
        return numpy.asscalar(data[row, col])

    def get_shapefile_reader(self):
        """Utility method for reading shapefile.

         Returns:
             obj: CSV reader.

         """

        return


    def get_file_path(self, type='csv'):
        """Utility method for reading different standard file formats: file path.

        Args:
            type (str): A file type.

        Returns:
            str: File name and path.

        """
        filename = self.local_file_path
        if os.path.isdir(filename):
            files = glob.glob(filename + "/*." + type)
            if len(files) > 0:
                filename = files[0]

        return filename

    def close(self):
        for key in self.readers:
            self.readers[key].close()

    def __del__(self):
        self.close()
