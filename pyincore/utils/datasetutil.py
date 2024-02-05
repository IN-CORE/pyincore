# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import geopandas as gpd
import pandas as pd

from pyincore import Dataset, DataService, MappingSet

# for evaluation of retrofit expression
import math
import scipy


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

    @staticmethod
    def construct_updated_inventories(inventory_dataset: Dataset, add_info_dataset: Dataset, mapping: MappingSet):
        """
        This method update the given inventory with retrofit information based on the mapping and additional information

        Args:
            inventory_dataset (gpd.GeoDataFrame): Geopandas DataFrame object
            add_info_dataset (pd.DataFrame): Pandas DataFrame object
            mapping (MappingSet): MappingSet object

        Returns:
            Dataset: Updated inventory dataset
            gpd.GeoDataFrame: Updated inventory geodataframe
        """
        inventory_df = inventory_dataset.get_dataframe_from_shapefile()
        inventory_df.set_index('guid', inplace=True)

        if add_info_dataset is not None:
            add_info_df = add_info_dataset.get_dataframe_from_csv()
            add_info_df.set_index('guid', inplace=True)

            # if additional information e.g. Retrofit presented, merge inventory properties with that additional
            # information
            inventory_df = pd.merge(inventory_df, add_info_df, left_index=True, right_index=True, how='left')

            # prepare retrofit definition into pandas dataframe; need to work with retrofit
            if len(mapping.mappingEntryKeys) > 0:
                mapping_entry_keys_df = pd.DataFrame(mapping.mappingEntryKeys)
                # add suffix to avoid conflict
                mapping_entry_keys_df.columns = [col + '_mappingEntryKey' for col in mapping_entry_keys_df.columns]
                mapping_entry_keys_df.set_index('name_mappingEntryKey', inplace=True)
                inventory_df = pd.merge(inventory_df, mapping_entry_keys_df, left_on='retrofit_key', right_index=True,
                                        how='left')
            else:
                raise ValueError("Missing proper definition for mappingEntryKeys in the mapping!")

            for i, inventory in inventory_df.iterrows():
                # For retrofit: if targetColumn and expression exist, update the targetColumn with the expression
                # TODO wrap to function
                target_column = inventory["config_mappingEntryKey"]["targetColumn"] \
                    if ("config_mappingEntryKey" in inventory.index and
                        isinstance(inventory["config_mappingEntryKey"], dict) and
                        "targetColumn" in inventory["config_mappingEntryKey"].keys()) else None
                expression = inventory["config_mappingEntryKey"]["expression"] \
                    if ("config_mappingEntryKey" in inventory.index and
                        isinstance(inventory["config_mappingEntryKey"], dict) and
                        "expression" in inventory["config_mappingEntryKey"].keys()) else None
                type = inventory["config_mappingEntryKey"]["type"] \
                    if ("config_mappingEntryKey" in inventory.index and
                        isinstance(inventory["config_mappingEntryKey"], dict) and
                        "type" in inventory["config_mappingEntryKey"].keys()) else None

                if target_column is not None and expression is not None:
                    if target_column in inventory.index:
                        retrofit_value = inventory["retrofit_value"]
                        if type and type == "number":
                            retrofit_value = float(retrofit_value)

                        # Dangerous!!! Need to be careful with the expression!!!
                        # e.g. inventory.at["ffe_elev"] = eval("inventory[target_column] + retrofit_value")
                        inventory[target_column] = eval(f"inventory[target_column]{expression}")
                    else:
                        raise ValueError("targetColumn: " + target_column + " not found in inventory properties!")

        # save the updated inventory to a new shapefile
        file_path = "tmp_retrofitted_inventory.shp"
        inventory_df.to_file(file_path)

        # return the updated inventory dataset in geoDataframe for future consumption
        return Dataset.from_file(file_path, inventory_dataset.data_type), inventory_df
