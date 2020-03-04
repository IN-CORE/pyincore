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
import rasterio
import wntr

from pyincore import DataService


class Dataset:
    """Dataset.

    Args:
        metadata (dict): Dataset metadata.

    """
    def __init__(self, metadata):
        self.metadata = metadata

        # For convenience instead of having to dig through the metadata for these
        self.data_type = metadata["dataType"]
        self.format = metadata["format"]
        self.id = metadata["id"]
        self.file_descriptors = metadata["fileDescriptors"]
        self.local_file_path = None

        self.readers = {}

    @classmethod
    def from_data_service(cls, id: str, data_service: DataService):
        """Get Dataset from Data service, get metadata as well.

        Args:
            id (str): ID of the Dataset.
            data_service (obj): Data service.

        Returns:
            obj: Dataset from Data service.

        """
        metadata = data_service.get_dataset_metadata(id)
        instance = cls(metadata)
        instance.cache_files(data_service)
        return instance

    @classmethod
    def from_json_str(cls, json_str):
        """Get Dataset from json string.

        Args:
            json_str (str): JSON of the Dataset.

        Returns:
            obj: Dataset from JSON.

        """
        return cls(json.loads(json_str))

    @classmethod
    def from_file(cls, file_path, data_type):
        """Get Dataset from the file.

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
        instance = cls(metadata)
        instance.local_file_path = file_path
        return instance

    @classmethod
    def from_dataframe(cls, dataframe, name):
        """Get Dataset from Panda's DataFrame.

        Args:
            dataframe (obj): Panda's DataFrame.
            name (str): filename.

        Returns:
            obj: Dataset from file.

        """
        dataframe.to_csv(name, index=False)
        return Dataset.from_file(name, "csv")

    @classmethod
    def from_csv_data(cls, result_data, name):
        """Get Dataset from CSV data.

        Args:
            result_data (obj): Result data and metadata.
            name (str): A CSV filename.

        Returns:
            obj: Dataset from file.

        """
        if len(result_data) > 0:
            with open(name, 'w') as csv_file:
                # Write the parent ID at the top of the result data, if it is given
                writer = csv.DictWriter(csv_file, dialect="unix", fieldnames=result_data[0].keys())
                writer.writeheader()
                writer.writerows(result_data)
        return Dataset.from_file(name, "csv")

    def cache_files(self, data_service: DataService):
        """Get the set of fragility data, curves.

        Args:
            data_service (obj): Data service.

        Returns:
            str: A path to the local file.

        """
        if self.local_file_path is not None:
            return
        self.local_file_path = data_service.get_dataset_blob(self.id)
        return self.local_file_path

    """Utility methods for reading different standard file formats"""

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

    def get_EPAnet_inp_reader(self):
        """Utility method for reading different standard file formats: EPAnet reader.

        Returns:
            obj: A Winter model.

        """
        filename = self.local_file_path
        if os.path.isdir(filename):
            files = glob.glob(filename + "/*.inp")
            if len(files) > 0:
                filename = files[0]
        wn = wntr.network.WaterNetworkModel(filename)
        return wn

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

    def get_csv_reader(self):
        """Utility method for reading different standard file formats: csv reader.

         Returns:
             obj: CSV reader.

         """
        if "csv" not in self.readers:
            filename = self.local_file_path
            if os.path.isdir(filename):
                files = glob.glob(filename + "/*.csv")
                if len(files) > 0:
                    filename = files[0]

            csvfile = open(filename, 'r')
            return csv.DictReader(csvfile)

        return self.readers["csv"]

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

    def get_dataframe_from_csv(self, low_memory=True):
        """Utility method for reading different standard file formats: Pandas DataFrame from csv.

        Args:
            low_memory (bool): A flag to suppress warning. Pandas is guessing dtypes for each column
            if column dtype is not specified which is very memory demanding.

        Returns:
            obj: Panda's DataFrame.

        """
        filename = self.get_file_path('csv')
        df = pd.DataFrame()
        if os.path.isfile(filename):
            df = pd.read_csv(filename, header="infer", low_memory=low_memory)
        return df

    def close(self):
        for key in self.readers:
            self.readers[key].close()

    def __del__(self):
        self.close()


class DamageRatioDataset:
    """For backwards compatibility until analyses are updated.

    Args:
        filename (str): CSV file with damage ratios.

    """
    def __init__(self, filename):
        self.damage_ratio = None
        csvfile = open(filename, 'r')
        reader = csv.DictReader(csvfile)
        self.damage_ratio = []
        for row in reader:
            self.damage_ratio.append(row)


class InventoryDataset:
    """For backwards compatibility until analyses are updated.

    Args:
        filename (str): file with GIS layers.

    """
    def __init__(self, filename):
        self.inventory_set = None
        if os.path.isdir(filename):
            layers = fiona.listlayers(filename)
            if len(layers) > 0:
                # for now, open a first shapefile
                self.inventory_set = fiona.open(filename, layer=layers[0])
        else:
            self.inventory_set = fiona.open(filename)

    def close(self):
        self.inventory_set.close()

    def __del__(self):
        self.close()
