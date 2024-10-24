# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import geopandas as gpd
import pandas as pd
import tempfile

from pyincore import Dataset, DataService, MappingSet

# for evaluation of retrofit expression
import math  # noqa: F401
import scipy  # noqa: F401


class DatasetUtil:
    @staticmethod
    def join_datasets(geodataset, tabledataset, clean_attributes=False):
        """Join Geopands geodataframe and non-geospatial Dataset using GUID field

        Args:
            geodataset (gpd.Dataset):  pyincore Dataset object with geospatial data
            tabledataset (gpd.Dataset): pyincore Dataset object without geospatial data
            clean_attributes (boolean): flag for deleting the fields except guid and the fields in csv table

        Returns:
            gpd.GeoDataFrame: Geopandas DataFrame object

        """
        gdf = gpd.read_file(geodataset.local_file_path)
        df = tabledataset.get_dataframe_from_csv()

        # remove the tables except guid
        if clean_attributes:
            gdf = gdf[["geometry", "guid"]]

        # joining and indexing
        join_gdf = gdf.set_index("guid").join(df.set_index("guid"))

        return join_gdf

    @staticmethod
    def join_table_dataset_with_source_dataset(dataset, client, clean_attributes=False):
        """Creates geopandas geodataframe by joining table dataset and its source dataset

        Args:
            dataset (Dataset): pyincore dataset object
            client (Client): pyincore service client object
            clean_attributes (boolean): flag for deleting the fields except guid and the fields in csv table

        Returns:
            gpd.Dataset: Geopandas geodataframe object.

        """
        is_source_dataset = False
        source_dataset = None

        # check if the given dataset is table dataset
        if (
            dataset.metadata["format"] != "table"
            and dataset.metadata["format"] != "csv"
        ):
            print("The given dataset is not a table dataset")
            return None

        # check if source dataset exists
        try:
            source_dataset = dataset.metadata["sourceDataset"]
            is_source_dataset = True
        except Exception:
            print("There is no source dataset for the give table dataset")

        if is_source_dataset:
            # merge dataset and source dataset
            geodataset = Dataset.from_data_service(source_dataset, DataService(client))
            joined_gdf = DatasetUtil.join_datasets(
                geodataset, dataset, clean_attributes
            )
        else:
            return None

        return joined_gdf

    @staticmethod
    def construct_updated_inventories(
        inventory_dataset: Dataset, add_info_dataset: Dataset, mapping: MappingSet
    ):
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
        if add_info_dataset is not None:
            inventory_df = inventory_dataset.get_dataframe_from_shapefile()
            inventory_df.set_index("guid", inplace=True)

            add_info_df = add_info_dataset.get_dataframe_from_csv()
            add_info_df.set_index("guid", inplace=True)

            # if additional information e.g. Retrofit presented, merge inventory properties with that additional
            # information
            inventory_df = pd.merge(
                inventory_df, add_info_df, left_index=True, right_index=True, how="left"
            )

            # prepare retrofit definition into pandas dataframe; need to work with retrofit
            if len(mapping.mappingEntryKeys) > 0:
                mapping_entry_keys_df = pd.DataFrame(mapping.mappingEntryKeys)
                # add suffix to avoid conflict
                mapping_entry_keys_df.columns = [
                    col + "_mappingEntryKey" for col in mapping_entry_keys_df.columns
                ]
                mapping_entry_keys_df.set_index("name_mappingEntryKey", inplace=True)
                inventory_df = pd.merge(
                    inventory_df,
                    mapping_entry_keys_df,
                    left_on="retrofit_key",
                    right_index=True,
                    how="left",
                )
                inventory_df.drop(columns=["defaultKey_mappingEntryKey"], inplace=True)
            else:
                raise ValueError(
                    "Missing proper definition for mappingEntryKeys in the mapping!"
                )

            def _apply_retrofit_value(row):
                target_column = (
                    row["config_mappingEntryKey"]["targetColumn"]
                    if (
                        "config_mappingEntryKey" in row.index
                        and isinstance(row["config_mappingEntryKey"], dict)
                        and "targetColumn" in row["config_mappingEntryKey"].keys()
                    )
                    else None
                )
                expression = (
                    row["config_mappingEntryKey"]["expression"]
                    if (
                        "config_mappingEntryKey" in row.index
                        and isinstance(row["config_mappingEntryKey"], dict)
                        and "expression" in row["config_mappingEntryKey"].keys()
                    )
                    else None
                )
                type = (
                    row["config_mappingEntryKey"]["type"]
                    if (
                        "config_mappingEntryKey" in row.index
                        and isinstance(row["config_mappingEntryKey"], dict)
                        and "type" in row["config_mappingEntryKey"].keys()
                    )
                    else None
                )

                if target_column and expression:
                    if target_column in row.index:
                        # Don't delete this line. Retrofit value is calculated based on the expression and will be
                        # used in the later eval
                        retrofit_value = (  # noqa: F841
                            float(row["retrofit_value"])
                            if type == "number"
                            else row["retrofit_value"]
                        )

                        # Dangerous! Be careful with the expression
                        row[target_column] = eval(f"row[target_column]{expression}")
                    else:
                        raise ValueError(
                            f"targetColumn: {target_column} not found in inventory properties!"
                        )

                return row

            inventory_df = inventory_df.apply(_apply_retrofit_value, axis=1)

            # rename columns to fit the character limit of shapefile
            inventory_df.rename(
                columns={
                    "retrofit_key": "retrofit_k",
                    "retrofit_value": "retrofit_v",
                    "description_mappingEntryKey": "descr_map",
                    "config_mappingEntryKey": "config_map",
                },
                inplace=True,
            )

            # save the updated inventory to a new shapefile
            tmpdirname = tempfile.mkdtemp()
            file_path = f"{tmpdirname}/tmp_updated_{inventory_dataset.id}.shp"
            inventory_df.to_file(file_path)

            # return the updated inventory dataset in geoDataframe for future consumption
            return (
                Dataset.from_file(file_path, inventory_dataset.data_type),
                tmpdirname,
                inventory_df,
            )
        else:
            # return original dataset
            return inventory_dataset, None, None
