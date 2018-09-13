import json


class Dataset:
    def __init__(self, metadata):
        self.metadata = metadata

        # For convenience instead of having to dig through the metadata for these
        self.data_type = metadata.dataType
        self.format = metadata.format
        self.id = metadata.id
        self.file_descriptors = metadata.fileDescriptors

    @classmethod
    def from_json_str(cls, json_str):
        return cls(json.loads(json_str))


# class InventoryDataset:
#     def __init__(self, filename):
#         self.inventory_set = None
#         if os.path.isdir(filename):
#             layers = fiona.listlayers(filename)
#             if len(layers) > 0:
#                 # for now, open a first shapefile
#                 self.inventory_set = fiona.open(filename, layer = layers[0])
#         else:
#             self.inventory_set = fiona.open(filename)
#
#     def close(self):
#         self.inventory_set.close()
#
#     def __del__(self):
#         self.close()
#
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
