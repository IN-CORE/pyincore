import json
import os

import fiona

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

        self.inventory_set = None

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

    def cache_files(self, data_service: DataService):
        if self.local_file_path is not None:
            return
        self.local_file_path = data_service.get_dataset_blob(self.id)
        return self.local_file_path

    def get_inventory_set(self, data_service=None):
        if self.inventory_set is not None:
            return self.inventory_set

        filename = self.local_file_path
        if os.path.isdir(filename):
            layers = fiona.listlayers(filename)
            if len(layers) > 0:
                # for now, open a first shapefile
                self.inventory_set = fiona.open(filename, layer=layers[0])
        else:
            self.inventory_set = fiona.open(filename)
        return self.inventory_set

    def close(self):
        if self.inventory_set is not None:
            self.inventory_set.close()

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
