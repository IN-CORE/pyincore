import csv
import json
import numpy
import os

import fiona
import rasterio

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
    def from_csv_data(cls, result_data, name):
        if len(result_data) > 0:
            with open(name, 'w') as csv_file:
                # Write the parent ID at the top of the result data, if it is given
                writer = csv.DictWriter(csv_file, dialect="unix", fieldnames= result_data[0].keys())
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
        if "inventory" in self.readers:
            return self.readers["inventory"]

        filename = self.local_file_path
        if os.path.isdir(filename):
            layers = fiona.listlayers(filename)
            if len(layers) > 0:
                # for now, open a first shapefile
                self.readers["inventory"] = fiona.open(filename, layer=layers[0])
        else:
            self.readers["inventory"] = fiona.open(filename)
        return self.readers["inventory"]

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
            csvfile = open(filename, 'r')
            self.readers["csv"] = csv.DictReader(csvfile)

        return self.readers["csv"]

    def close(self):
        for key in self.readers:
            self.readers[key].close()

    def __del__(self):
        self.close()



class InventoryDataset:
    def __init__(self):
        print("inv")


class DamageRatioDataset:
    def __init__(self):
        print("dmgratio")

#
# class HazardDataset:
#     def __init__(self, filename):
#         self.hazard = None
#         self.hazard = rasterio.open(filename)
#
#     def get_hazard_value(self, location):
#         row, col = self.hazard.index(location.x, location.y)
#         # assume that there is only 1 band
#         data = self.hazard.read(1)
#         if row < 0 or col < 0 or row >= self.hazard.height or col >= self.hazard.width:
#             return 0.0
#         return numpy.asscalar(data[row, col])
#
#     def close(self):
#         self.hazard.close()
#
#     def __del__(self):
#         self.close()
#
#
# class DamageRatioDataset:
#     def __init__(self, filename):
#         self.damage_ratio = None
#         csvfile = open(filename, 'r')
#         reader = csv.DictReader(csvfile)
#         self.damage_ratio = []
#         for row in reader:
#             self.damage_ratio.append(row)
