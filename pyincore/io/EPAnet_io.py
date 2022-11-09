import glob
from .base_io import BaseIO
import os
import wntr


class EPAnetIO(BaseIO):
    @classmethod
    def read(
            cls,
            local_file_path: str,
            to_data_type: str = 'WaterNetworkModel',
            **kwargs
    ) -> wntr.network.WaterNetworkModel:
        if to_data_type == 'WaterNetworkModel':
            if os.path.isdir(local_file_path):
                files = glob.glob(local_file_path + "/*.inp")
                if len(files) > 0:
                    local_file_path = files[0]
            # TODO: Perform Datavalidation here if needed
            return wntr.network.WaterNetworkModel(local_file_path)
        else:
            raise TypeError(f"to_data_type = {to_data_type} is not defined. Possible value is WaterNetworkModel")

    @classmethod
    def write(cls, *args):
        pass
