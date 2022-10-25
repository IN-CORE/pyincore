import os
import glob
import csv

import fiona
import geopandas as gpd
import numpy
import pandas as pd
import rasterio
import wntr
import warnings
from pyincore import DataService
from .io import CSVIO, JSONIO

from typing import TypeVar, Optional, Union

NewDataset = TypeVar('NewDataset', bound="NewDataset")
ResultType = TypeVar('ResultType')
warnings.filterwarnings("ignore", "", UserWarning)


class NewDataset:
    def __init__(self, metadata):
        self.metadata = metadata

        # For convenience instead of having to dig through the metadata for these
        self.data_type = metadata["dataType"]
        self.format = metadata["format"]
        self.id = metadata["id"]
        self.file_descriptors = metadata["fileDescriptors"]
        self.local_file_path = None

        self.raster_reader = None

    @classmethod
    def from_data_service(cls, id: str, data_service: DataService) -> NewDataset:
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
    def from_file(cls, file_path: str, data_type: str) -> NewDataset:
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

    def cache_files(self, data_service: DataService) -> str:
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

    def get_file_path(self, search_type: str = 'csv') -> str:
        """Utility method for reading different standard file formats: file path.

        Args:
            search_type (str): A file type.

        Returns:
            str: File name and path.

        """
        filename = self.local_file_path
        if os.path.isdir(filename):
            files = glob.glob(filename + "/*." + search_type)
            if len(files) > 0:
                filename = files[0]

        return filename

    def get_raster_value(self, location) -> float:
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

    @classmethod
    def read(
            cls,
            from_type: str,
            local_file_path: str,
            to_type: Optional[str] = None,
            **kwargs
    ) -> Optional[
            dict,
            pd.DataFrame,
            fiona.Collection,
            wntr.network.WaterNetworkModel,
            csv.DictReader,
            Union[pd.DataFrame, gpd.GeoDataFrame]
    ]:
        filename = local_file_path
        if from_type == 'inventory':
            if os.path.isdir(filename):
                layers = fiona.listlayers(filename)
                if len(layers) > 0:
                    # for now, open a first shapefile
                    # TODO: Do we need separate IO for this?
                    # TODO: Perform Datavalidation here if needed
                    return fiona.open(filename, layer=layers[0])
            else:
                return fiona.open(filename)

        elif from_type == 'EPAnet':
            if os.path.isdir(filename):
                files = glob.glob(filename + "/*.inp")
                if len(files) > 0:
                    filename = files[0]
            # TODO: Do we need separate IO for this?
            # TODO: Perform Datavalidation here if needed
            return wntr.network.WaterNetworkModel(filename)

        elif from_type == 'shapefile':
            # read shapefile directly by Geopandas.read_file()
            # It will preserve CRS information also
            # TODO: Do we need separate IO for this?
            # TODO: Perform Datavalidation here if needed
            gdf = gpd.read_file(filename)
            return gdf

        elif from_type == 'csv' or from_type == 'df':
            if not to_type:
                return CSVIO.read(filename, **kwargs)
            return CSVIO.read(filename, to_type=to_type, **kwargs)

        elif from_type == 'json':
            if not to_type:
                return JSONIO.read(filename, **kwargs)
            return JSONIO.read(filename, to_type=to_type, **kwargs)

        else:
            raise TypeError(f"Unknown from_type = {from_type}")

    @classmethod
    def write(
            cls,
            result_data: ResultType,
            name: str,
            data_type: str,
            from_type: str,
            to_type: Optional[str] = None,
            **kwargs
    ) -> NewDataset:

        if from_type == 'csv' or from_type == 'df':
            if not to_type:
                CSVIO.write(result_data, name, from_type=from_type, **kwargs)
            CSVIO.write(result_data, name, from_type=from_type, to_type=to_type, **kwargs)

        elif from_type == 'json':
            if not to_type:
                JSONIO.write(result_data, name, from_type=from_type, **kwargs)
            JSONIO.write(result_data, name, from_type=from_type, to_type=to_type, **kwargs)

        else:
            raise TypeError(f"Unknown from_type = {from_type}")

        return NewDataset.from_file(name, data_type)

