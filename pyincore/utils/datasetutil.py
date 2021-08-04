# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import geopandas as gpd

from pyincore import Dataset, DataService


class DatasetUtil:
    @staticmethod
    def join_datasets(geodataset, tabledataset):
        """Join Geopands geodataframe and non-geospatial Dataset using GUID field

        Args:
            geodataset (gpd.Dataset):  pyincore Dataset object with geospatial data
            tabledataset (gpd.Dataset): pyincore Dataset object without geospatial data

        Returns:
            gpd.GeoDataFrame: Geopandas DataFrame object

        """
        gdf = gpd.read_file(geodataset.local_file_path)
        df = tabledataset.get_dataframe_from_csv()
        join_gdf = gdf.set_index("guid").join(df.set_index("guid"))

        return join_gdf

    @staticmethod
    def join_table_dataset_with_source_dataset(dataset, client):
        """Creates geopandas geodataframe by joining table dataset and its source dataset

            Args:
                dataset (Dataset): pyincore dataset object
                client (Client): pyincore service client object

            Returns:
                gpd.Dataset: Geopandas geodataframe object.

        """
        is_source_dataset = False
        source_dataset = None

        # check if the given dataset is table dataset
        if dataset.metadata['format'] != 'table' and dataset.metadata['format'] != 'csv':
            print("The given dataset is not a table dataset")
            return None

        # check if source dataset exists
        try:
            source_dataset = dataset.metadata['sourceDataset']
            is_source_dataset = True
        except Exception:
            print("There is no source dataset for the give table dataset")

        if is_source_dataset:
            # merge dataset and source dataset
            geodataset = Dataset.from_data_service(source_dataset, DataService(client))
            joined_gdf = DatasetUtil.join_datasets(geodataset, dataset)
        else:
            return None

        return joined_gdf
