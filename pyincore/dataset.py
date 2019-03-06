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
        metadata = data_service.get_dataset_metadata(id)
        instance = cls(metadata)
        instance.cache_files(data_service)
        return instance

    @classmethod
    def from_json_str(cls, json_str):
        return cls(json.loads(json_str))

    @classmethod
    def from_file(cls, file_path, data_type):
        metadata = {"dataType": data_type,
                    "format": '',
                    "fileDescriptors": [],
                    "id": file_path}
        instance = cls(metadata)
        instance.local_file_path = file_path
        return instance

    @classmethod
    def from_dataframe(cls, dataframe, name):
        dataframe.to_csv(name, index=False)
        return Dataset.from_file(name, "csv")

    @classmethod
    def from_csv_data(cls, result_data, name):
        if len(result_data) > 0:
            with open(name, 'w') as csv_file:
                # Write the parent ID at the top of the result data, if it is given
                writer = csv.DictWriter(csv_file, dialect="unix", fieldnames=result_data[0].keys())
                writer.writeheader()
                writer.writerows(result_data)
        return Dataset.from_file(name, "csv")

    def cache_files(self, data_service: DataService):
        if self.local_file_path is not None:
            return
        self.local_file_path = data_service.get_dataset_blob(self.id)
        return self.local_file_path

    """Utility methods for reading different standard file formats"""

    def get_inventory_reader(self):

        filename = self.local_file_path
        if os.path.isdir(filename):
            layers = fiona.listlayers(filename)
            if len(layers) > 0:
                # for now, open a first shapefile
                return fiona.open(filename, layer=layers[0])
        else:
            return fiona.open(filename)

    def get_EPAnet_inp_reader(self):
        filename = self.local_file_path
        if os.path.isdir(filename):
            files = glob.glob(filename + "/*.inp")
            if len(files) > 0:
                filename = files[0]
        wn = wntr.network.WaterNetworkModel(filename)
        return wn

    def get_json_reader(self):
        if not "json" in self.readers:
            filename = self.local_file_path
            if os.path.isdir(filename):
                files = glob.glob(filename + "/*.json")
                if len(files) > 0:
                    filename = files[0]

            with open(filename, 'r') as f:
                return json.load(f)

        return self.readers["json"]

    def get_raster_value(self, location):
        if not "raster" in self.readers:
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
        if not "csv" in self.readers:
            filename = self.local_file_path
            if os.path.isdir(filename):
                files = glob.glob(filename + "/*.csv")
                if len(files) > 0:
                    filename = files[0]

            csvfile = open(filename, 'r')
            return csv.DictReader(csvfile)

        return self.readers["csv"]

    def get_file_path(self, type='csv'):
        filename = self.local_file_path
        if os.path.isdir(filename):
            files = glob.glob(filename + "/*." + type)
            if len(files) > 0:
                filename = files[0]

        return filename

    def get_dataframe_from_csv(self):
        filename = self.get_file_path('csv')
        df = pd.DataFrame()
        if os.path.isfile(filename):
            df = pd.read_csv(filename, header="infer")
        return df

    def close(self):
        for key in self.readers:
            self.readers[key].close()

    def __del__(self):
        self.close()


# Added DamageRatioDataset and InventoryDataset for backwards compatibility until analyses are updated
class DamageRatioDataset:
    def __init__(self, filename):
        self.damage_ratio = None
        csvfile = open(filename, 'r')
        reader = csv.DictReader(csvfile)
        self.damage_ratio = []
        for row in reader:
            self.damage_ratio.append(row)


class InventoryDataset:
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
