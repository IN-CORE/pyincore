import geopandas as gpd
from .base_io import BaseIO
import pandas as pd
from typing import Union


class ShapefileIO(BaseIO):
    @classmethod
    def read(
            cls,
            local_file_path: str,
            to_data_type: str = 'GeoDataFrame',
            **kwargs
    ) -> Union[pd.DataFrame, gpd.GeoDataFrame]:
        if to_data_type == 'GeoDataFrame':
            # read shapefile directly by Geopandas.read_file()
            # It will preserve CRS information also
            # TODO: Perform Datavalidation here if needed
            gdf = gpd.read_file(local_file_path)
            return gdf
        else:
            raise TypeError(f"to_data_type = {to_data_type} is not defined. Possible value is GeoDataFrame")

    @classmethod
    def write(cls, *args):
        pass
