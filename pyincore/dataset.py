import os
import glob
import csv

import fiona
from deprecated import deprecated
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import json
import wntr
import warnings
from pyincore import DataService
from pyincore.io import CSVIO, JSONIO, InventoryIO, EPAnetIO, ShapefileIO, RasterIO
from typing import TypeVar, Optional, Union

Dataset = TypeVar('Dataset', bound="Dataset")
ResultType = TypeVar('ResultType')
warnings.filterwarnings("ignore", "", UserWarning)
write_deprecation_warning = 'This function will be removed in future, please use the write method with appropriate ' \
                            'arguments'
read_deprecation_warning = 'This function will be removed in future, please use the read method with appropriate ' \
                           'arguments'
close_deprecated_msg = "The readers property on Dataset is deprecated and will be removed in future versions. Use " \
                           "read and write methods"
deprecation_warning_version = '1.8.0'


class Dataset:
    def __init__(self, metadata):
        self.metadata = metadata

        # For convenience instead of having to dig through the metadata for these
        self.data_type = metadata["dataType"]
        self.format = metadata["format"]
        self.id = metadata["id"]
        self.file_descriptors = metadata["fileDescriptors"]
        self.local_file_path = None

        # Deprecated remove this in future
        self.readers = {}

    @classmethod
    def from_data_service(cls, dataset_id: str, data_service: DataService) -> Dataset:
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
    @deprecated(reason=write_deprecation_warning, version=deprecation_warning_version)
    def from_json_str(cls, json_str, data_service: DataService = None, file_path=None):
        """Get Dataset from json string.

        Args:
            json_str (str): JSON of the Dataset.
            data_service (obj): Data Service class.
            file_path (str): File path.

        Returns:
            obj: Dataset from JSON.

        """
        instance = cls(json.loads(json_str))

        # download file and set local file path using metadata from services
        if data_service is not None:
            instance.cache_files(data_service)

        # if there is local files associates with the dataset
        elif file_path is not None:
            instance.local_file_path = file_path

        else:
            raise ValueError("You have to either use data services, or given pass local file path.")

        return instance

    @classmethod
    def from_file(cls, file_path: str, data_type: str) -> Dataset:
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

    @classmethod
    @deprecated(reason=write_deprecation_warning, version=deprecation_warning_version)
    def from_dataframe(cls, dataframe, name, data_type):
        """Get Dataset from Panda's DataFrame.

        Args:
            dataframe (obj): Panda's DataFrame.
            name (str): filename.
            data_type (str): Incore data type, e.g. incore:xxxx or ergo:xxxx

        Returns:
            obj: Dataset from file.

        """
        dataframe.to_csv(name, index=False)
        return Dataset.from_file(name, data_type)

    @classmethod
    @deprecated(reason=write_deprecation_warning, version=deprecation_warning_version)
    def from_csv_data(cls, result_data, name, data_type):
        """Get Dataset from CSV data.

        Args:
            result_data (obj): Result data and metadata.
            name (str): A CSV filename.
            data_type (str): Incore data type, e.g. incore:xxxx or ergo:xxxx

        Returns:
            obj: Dataset from file.

        """
        if len(result_data) > 0:
            with open(name, 'w') as csv_file:
                # Write the parent ID at the top of the result data, if it is given
                writer = csv.DictWriter(csv_file, dialect="unix", fieldnames=result_data[0].keys())
                writer.writeheader()
                writer.writerows(result_data)
        return Dataset.from_file(name, data_type)

    @classmethod
    @deprecated(reason=write_deprecation_warning, version=deprecation_warning_version)
    def from_json_data(cls, result_data, name, data_type):
        """Get Dataset from JSON data.

        Args:
            result_data (obj): Result data and metadata.
            name (str): A JSON filename.
            data_type (str): Incore data type, e.g. incore:xxxx or ergo:xxxx

        Returns:
            obj: Dataset from file.

        """
        if len(result_data) > 0:
            with open(name, 'w') as json_file:
                json_dumps_str = json.dumps(result_data, indent=4)
                json_file.write(json_dumps_str)
        return Dataset.from_file(name, data_type)

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

    @deprecated(reason=read_deprecation_warning, version=deprecation_warning_version)
    def get_inventory_reader(self):
        """Utility method for reading different standard file formats: Set of inventory.

        Returns:
            obj: A Fiona object.

        """
        filename = self.local_file_path
        if os.path.isdir(filename):
            layers = fiona.listlayers(filename)
            if len(layers) > 0:
                # for now, open a first shapefile
                return fiona.open(filename, layer=layers[0])
        else:
            return fiona.open(filename)

    @deprecated(reason=read_deprecation_warning, version=deprecation_warning_version)
    def get_EPAnet_inp_reader(self):
        """Utility method for reading different standard file formats: EPAnet reader.

        Returns:
            obj: A Winter model.

        """
        filename = self.local_file_path
        if os.path.isdir(filename):
            files = glob.glob(filename + "/*.inp")
            if len(files) > 0:
                filename = files[0]
        wn = wntr.network.WaterNetworkModel(filename)
        return wn

    @deprecated(reason=read_deprecation_warning, version=deprecation_warning_version)
    def get_json_reader(self):
        """Utility method for reading different standard file formats: json reader.

        Returns:
            obj: A json model data.

        """
        if "json" not in self.readers:
            filename = self.local_file_path
            if os.path.isdir(filename):
                files = glob.glob(filename + "/*.json")
                if len(files) > 0:
                    filename = files[0]

            with open(filename, 'r') as f:
                return json.load(f)

        return self.readers["json"]

    @deprecated(reason=read_deprecation_warning, version=deprecation_warning_version)
    def get_raster_value(self, location):
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
        return np.asscalar(data[row, col])

    @deprecated(reason=read_deprecation_warning, version=deprecation_warning_version)
    def get_csv_reader(self):
        """Utility method for reading different standard file formats: csv reader.

         Returns:
             obj: CSV reader.

         """
        if "csv" not in self.readers:
            filename = self.local_file_path
            if os.path.isdir(filename):
                files = glob.glob(filename + "/*.csv")
                if len(files) > 0:
                    filename = files[0]

            csvfile = open(filename, 'r')
            return csv.DictReader(csvfile)

        return self.readers["csv"]

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

    @deprecated(reason=read_deprecation_warning, version=deprecation_warning_version)
    def get_dataframe_from_csv(self, low_memory=True):
        """Utility method for reading different standard file formats: Pandas DataFrame from csv.

        Args:
            low_memory (bool): A flag to suppress warning. Pandas is guessing dtypes for each column
            if column dtype is not specified which is very memory demanding.

        Returns:
            obj: Panda's DataFrame.

        """
        filename = self.get_file_path('csv')
        df = pd.DataFrame()
        if os.path.isfile(filename):
            df = pd.read_csv(filename, header="infer", low_memory=low_memory)
        return df

    @deprecated(reason=read_deprecation_warning, version=deprecation_warning_version)
    def get_dataframe_from_shapefile(self):
        """Utility method for reading different standard file formats: GeoDataFrame from shapefile.

        Returns:
            obj: Geopanda's GeoDataFrame.

        """
        # read shapefile directly by Geopandas.read_file()
        # It will preserve CRS information also
        gdf = gpd.read_file(self.local_file_path)

        return gdf

    @classmethod
    def read(
            cls,
            from_file_type: str,
            local_file_path: str,
            to_data_type: Optional[str] = None,
            **kwargs
    ) -> Union[
        dict,
        pd.DataFrame,
        fiona.Collection,
        wntr.network.WaterNetworkModel,
        csv.DictReader,
        Union[pd.DataFrame, gpd.GeoDataFrame],
        np.ndarray
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
    ) -> Dataset:

        if to_file_type == 'csv':
            if not from_data_type:
                CSVIO.write(result_data, name, **kwargs)
            CSVIO.write(result_data, name, from_data_type=from_data_type, **kwargs)

        elif to_file_type == 'json':
            if not from_data_type:
                JSONIO.write(result_data, name, **kwargs)
            JSONIO.write(result_data, name, from_data_type=from_data_type, **kwargs)

        else:
            raise TypeError(
                f"Unknown from_data_type = {from_data_type}, you need to specify "
                f"what format you are writing the data to")

        return Dataset.from_file(name, data_type)

    @deprecated(reason=close_deprecated_msg, version='1.8.0')
    def close(self):
        for key in self.readers:
            self.readers[key].close()

    @deprecated(reason=close_deprecated_msg, version='1.8.0')
    def __del__(self):
        self.close()


class DamageRatioDataset:
    """For backwards compatibility until analyses are updated.

    Args:
        filename (str): CSV file with damage ratios.

    """

    def __init__(self, filename):
        self.damage_ratio = None
        csvfile = open(filename, 'r')
        reader = csv.DictReader(csvfile)
        self.damage_ratio = []
        for row in reader:
            self.damage_ratio.append(row)


class InventoryDataset:
    """For backwards compatibility until analyses are updated.

    Args:
        filename (str): file with GIS layers.

    """

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

