import fiona
from .base_io import BaseIO
import os


class InventoryIO(BaseIO):

    @classmethod
    def read(cls, local_file_path: str, to_data_type: str = 'fiona.Collection', **kwargs) -> fiona.Collection:
        if to_data_type == 'fiona.Collection':
            if os.path.isdir(local_file_path):
                layers = fiona.listlayers(local_file_path)
                if len(layers) > 0:
                    # for now, open a first shapefile
                    # TODO: Perform Datavalidation here if needed
                    return fiona.open(local_file_path, layer=layers[0])
            else:
                return fiona.open(local_file_path)
        else:
            raise TypeError(f"to_data_type = {to_data_type} is not defined. Possible value is fiona.Collection")

    @classmethod
    def write(cls, *args):
        pass
