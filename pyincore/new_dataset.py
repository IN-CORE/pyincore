import os
import glob
import csv

import fiona
import geopandas as gpd
import pandas as pd
import wntr
import warnings
from pyincore import DataService
from .io import CSVIO, JSONIO, InventoryIO, EPAnetIO, ShapefileIO, RasterIO

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

    @classmethod
    def from_data_service(cls, dataset_id: str, data_service: DataService) -> NewDataset:
        """Get Dataset from Data service, get metadata as well.

        Args:
            dataset_id (str): ID of the Dataset.
            data_service (obj): Data service.

        Returns:
            obj: Dataset from Data service.

        """
        metadata = data_service.get_dataset_metadata(dataset_id)
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
        if self.local_file_path is None:
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

    @classmethod
    def read(
            cls,
            from_file_type: str,
            local_file_path: str,
            to_data_type: Optional[str] = None,
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
        if from_file_type == 'inventory':
            if not to_data_type:
                return InventoryIO.read(filename)
            return InventoryIO.read(filename, to_data_type=to_data_type, **kwargs)

        elif from_file_type == 'EPAnet':
            if not to_data_type:
                return EPAnetIO.read(filename)
            return EPAnetIO.read(filename, to_data_type=to_data_type, **kwargs)

        elif from_file_type == 'rasterfile':
            location = kwargs.get('location', False)
            if location:
                if not to_data_type:
                    return RasterIO.read(filename, location=location, **kwargs)
                return RasterIO.read(filename, to_data_type=to_data_type, location=location, **kwargs)
            raise ValueError("Reading Raster file requires argument location which was not passed.")

        elif from_file_type == 'shapefile':
            if not to_data_type:
                return ShapefileIO.read(filename)
            return ShapefileIO.read(filename, to_data_type=to_data_type, **kwargs)

        elif from_file_type == 'csv':
            if not to_data_type:
                return CSVIO.read(filename, **kwargs)
            return CSVIO.read(filename, to_data_type=to_data_type, **kwargs)

        elif from_file_type == 'json':
            if not to_data_type:
                return JSONIO.read(filename, **kwargs)
            return JSONIO.read(filename, to_data_type=to_data_type, **kwargs)

        else:
            raise TypeError(f"Unknown from_type = {from_file_type}")

    @classmethod
    def write(
            cls,
            result_data: ResultType,
            name: str,
            data_type: str,
            from_data_type: str,
            to_file_type: Optional[str] = None,
            **kwargs
    ) -> NewDataset:

        if to_file_type == 'csv':
            if not from_data_type:
                CSVIO.write(result_data, name, **kwargs)
            CSVIO.write(result_data, name, from_data_type=from_data_type, **kwargs)

        elif to_file_type == 'json':
            if not from_data_type:
                JSONIO.write(result_data, name, **kwargs)
            JSONIO.write(result_data, name, from_data_type=from_data_type, **kwargs)

        else:
            raise TypeError(f"Unknown from_data_type = {from_data_type}")

        return NewDataset.from_file(name, data_type)

