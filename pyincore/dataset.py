# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import csv
import glob
import json
import os

import fiona
import pandas as pd
import geopandas as gpd
import rasterio
import warnings
from pyincore import DataService
from pathlib import Path
import shutil


warnings.filterwarnings("ignore", "", UserWarning)


class Dataset:
    """Dataset.

    Args:
        metadata (dict): Dataset metadata.

    """

    def __init__(self, metadata):
        self.metadata = metadata

        # For convenience instead of having to dig through the metadata for these
        self.title = metadata["title"] if "title" in metadata else None
        self.description = (
            metadata["description"] if "description" in metadata else None
        )
        self.data_type = metadata["dataType"]
        self.format = metadata["format"]
        self.id = metadata["id"]
        self.file_descriptors = metadata["fileDescriptors"]
        self.local_file_path = None

        self.readers = {}

    @classmethod
    def from_data_service(cls, id: str, data_service: DataService):
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
            raise ValueError(
                "You have to either use data services, or given pass local file path."
            )

        return instance

    @classmethod
    def from_file(cls, file_path, data_type):
        """Get Dataset from the file.

        Args:
            file_path (str): File path.
            data_type (str): Data type.

        Returns:
            obj: Dataset from file.

        """
        metadata = {
            "dataType": data_type,
            "format": "",
            "fileDescriptors": [],
            "id": file_path,
        }
        instance = cls(metadata)
        instance.local_file_path = file_path
        return instance

    @classmethod
    def from_dataframe(cls, dataframe, name, data_type, index=False):
        """Get Dataset from Panda's DataFrame.

        Args:
            dataframe (obj): Panda's DataFrame.
            name (str): filename.
            data_type (str): Incore data type, e.g. incore:xxxx or ergo:xxxx
            index (bool): Store the index column

        Returns:
            obj: Dataset from file.

        """
        dataframe.to_csv(name, index=index)
        return Dataset.from_file(name, data_type)

    @classmethod
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
            with open(name, "w") as csv_file:
                # Write the parent ID at the top of the result data, if it is given
                writer = csv.DictWriter(
                    csv_file, dialect="unix", fieldnames=result_data[0].keys()
                )
                writer.writeheader()
                writer.writerows(result_data)
        return Dataset.from_file(name, data_type)

    @classmethod
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
            with open(name, "w") as json_file:
                json_dumps_str = json.dumps(result_data, indent=4)
                json_file.write(json_dumps_str)
        return Dataset.from_file(name, data_type)

    def cache_files(self, data_service: DataService):
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

    """Utility methods for reading different standard file formats"""

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

            with open(filename, "r") as f:
                return json.load(f)

        return self.readers["json"]

    def get_raster_value(self, x, y):
        """Utility method for reading different standard file formats: raster value.

        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
        Returns:
            numpy.array: Hazard values.

        """
        if "raster" not in self.readers:
            filename = self.local_file_path
            if os.path.isdir(filename):
                files = glob.glob(filename + "/*.tif")
                if len(files) > 0:
                    filename = files[0]
            self.readers["raster"] = rasterio.open(filename)

        hazard = self.readers["raster"]
        row, col = hazard.index(x, y)
        # assume that there is only 1 band
        data = hazard.read(1)
        xmin, ymin, xmax, ymax = hazard.bounds
        if x < xmin or x > xmax or y < ymin or y > ymax:
            return None
        # TODO check threshold
        return float(data[row, col])

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

            csvfile = open(filename, "r")
            return csv.DictReader(csvfile)

        return self.readers["csv"]

    def get_csv_reader_std(self):
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

            csvfile = open(filename, "r")
            return csv.reader(csvfile)

        return self.readers["csv"]

    def get_file_path(self, type="csv"):
        """Utility method for reading different standard file formats: file path.

        Args:
            type (str): A file type.

        Returns:
            str: File name and path.

        """
        filename = self.local_file_path
        if os.path.isdir(filename):
            files = glob.glob(filename + "/*." + type)
            if len(files) > 0:
                filename = files[0]

        return filename

    def get_dataframe_from_csv(self, low_memory=True, delimiter=None):
        """Utility method for reading different standard file formats: Pandas DataFrame from csv.

        Args:
            low_memory (bool): A flag to suppress warning. Pandas is guessing dtypes for each column
            if column dtype is not specified which is very memory demanding.

        Returns:
            obj: Panda's DataFrame.

        """
        filename = self.get_file_path("csv")
        df = pd.DataFrame()
        if os.path.isfile(filename):
            df = pd.read_csv(
                filename, header="infer", low_memory=low_memory, delimiter=delimiter
            )
        return df

    def get_dataframe_from_shapefile(self):
        """Utility method for reading different standard file formats: GeoDataFrame from shapefile.

        Returns:
            obj: Geopanda's GeoDataFrame.

        """
        # read shapefile directly by Geopandas.read_file()
        # It will preserve CRS information also
        gdf = gpd.read_file(self.local_file_path)

        return gdf

    def delete_temp_file(self):
        """Delete temporary folder."""
        if os.path.exists(self.local_file_path):
            os.remove(self.local_file_path)

    def delete_temp_folder(self):
        """Delete temporary folder."""
        path = Path(self.local_file_path)
        absolute_path = path.parent.absolute()

        if os.path.isdir(absolute_path):
            try:
                shutil.rmtree(absolute_path)
            except PermissionError as e:
                print(f"Error deleting : {e}")

    def close(self):
        for key in self.readers:
            self.readers[key].close()

    def __del__(self):
        self.close()


class DamageRatioDataset:
    """For backwards compatibility until analyses are updated.

    Args:
        filename (str): CSV file with damage ratios.

    """

    def __init__(self, filename):
        self.damage_ratio = None
        csvfile = open(filename, "r")
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
