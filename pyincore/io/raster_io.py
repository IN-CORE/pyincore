import rasterio
from .base_io import BaseIO
import numpy as np
from typing import Any


class RasterIO(BaseIO):
    @classmethod
    def read(
            cls,
            local_file_path: str,
            location: Any,
            to_data_type: str = 'ndarray',
            **kwargs
    ) -> np.ndarray:
        if to_data_type == 'ndarray':
            hazard: Any = rasterio.open(local_file_path)
            # TODO: Perform Datavalidation here if needed
            row, col = hazard.index(location.x, location.y)
            # assume that there is only 1 band
            data = hazard.read(1)
            if row < 0 or col < 0 or row >= hazard.height or col >= hazard.width:
                return 0.0
            return np.asscalar(data[row, col])
        else:
            raise TypeError(f"to_data_type = {to_data_type} is not defined. Possible value is ndarray")

    @classmethod
    def write(cls, *args):
        pass
