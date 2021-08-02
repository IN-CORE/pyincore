# Copyright (c) 2020 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import geopandas as gpd
import json
import pandas as pd

from pyincore import Dataset, DataService


class DataProcessUtil:

    @staticmethod
    def get_mapped_result_from_analysis(client, inventory_id: str, dmg_result_dataset,
                                        bldg_func_dataset, archetype_mapping_id: str,
                                        groupby_col_name: str = "max_state"):
        """Use this if you want to load results directly from the output files of the analysis, than storing the results
        to data service and loading from there using ids.
        It takes the static inputs: inventory & archetypes as dataset ids. The result inputs are taken as
        Dataset class objects, which are created by reading the output result files.

        Args:
            client: Service client with authentication info
            inventory_id: Inventory dataset id
            dmg_result_dataset: Incore dataset for damage result
            bldg_func_dataset: Incore dataset for building func dataset
            archetype_mapping_id: Mapping id dataset for archetype

        Returns:
            dmg_ret_json: JSON of the damage state results ordered by cluster and category.
            func_ret_json: JSON of the building functionality results ordered by cluster and category.
            mapped_df: Dataframe of max damage state

        """
        bldg_inv = Dataset.from_data_service(inventory_id, DataService(client))
        inventory = pd.DataFrame(gpd.read_file(bldg_inv.local_file_path))

        dmg_result = dmg_result_dataset.get_dataframe_from_csv()

        bldg_func_df = bldg_func_dataset.get_dataframe_from_csv()
        bldg_func_df.rename(columns={'building_guid': 'guid'}, inplace=True)

        arch_mapping = Dataset.from_data_service(archetype_mapping_id, DataService(client)).get_dataframe_from_csv()

        max_state_df = DataProcessUtil.get_max_damage_state(dmg_result)
        dmg_ret_json = DataProcessUtil.create_mapped_dmg_result(inventory, max_state_df, arch_mapping,
                                                                groupby_col_name)
        func_ret_json = DataProcessUtil.create_mapped_func_result(inventory, bldg_func_df, arch_mapping)

        return dmg_ret_json, func_ret_json, max_state_df

    @staticmethod
    def get_mapped_result_from_dataset_id(client, inventory_id: str, dmg_result_id: str, bldg_func_id,
                                          archetype_mapping_id: str,
                                          groupby_col_name: str = "max_state"):
        """Use this if your damage results are already stored in the data service and you have their dataset ids.
        All the inputs (except groupby_col_name) are dataset ids.

        Args:
            client: Service client with authentication info
            inventory_id: Inventory dataset id
            dmg_result_id: Damage result dataset id
            bldg_func_id: Incore dataset for building func id
            archetype_mapping_id: Mapping id dataset for archetype
            groupby_col_name: column name to group by, default to max_state

        Returns:
            dmg_ret_json: JSON of the damage state results ordered by cluster and category.
            func_ret_json: JSON of the building functionality results ordered by cluster and category.
            max_state_df: Dataframe of max damage state

        """
        bldg_inv = Dataset.from_data_service(inventory_id, DataService(client))
        inventory = pd.DataFrame(gpd.read_file(bldg_inv.local_file_path))

        dmg_result_dataset = Dataset.from_data_service(dmg_result_id, DataService(client))
        dmg_result = dmg_result_dataset.get_dataframe_from_csv()

        bldg_func_dataset = Dataset.from_data_service(bldg_func_id, DataService(client))
        bldg_func_df = bldg_func_dataset.get_dataframe_from_csv()
        bldg_func_df.rename(columns={'building_guid': 'guid'}, inplace=True)

        archtype_mapping_dataset = Dataset.from_data_service(archetype_mapping_id, DataService(client))
        arch_mapping = archtype_mapping_dataset.get_dataframe_from_csv()

        max_state_df = DataProcessUtil.get_max_damage_state(dmg_result)
        dmg_ret_json = DataProcessUtil.create_mapped_dmg_result(inventory, max_state_df, arch_mapping,
                                                                groupby_col_name)
        func_ret_json = DataProcessUtil.create_mapped_func_result(inventory, bldg_func_df, arch_mapping)

        return dmg_ret_json, func_ret_json, max_state_df

    @staticmethod
    def get_mapped_result_from_path(inventory_path: str, dmg_result_path: str,
                                    func_result_path: str,
                                    archetype_mapping_path: str,
                                    groupby_col_name: str):
        """

        Args:
            inventory_path: Path to the zip file containing the inventory
                    example: /Users/myuser/5f9091df3e86721ed82f701d.zip
            dmg_result_path: Path to the damage result output file
            func_result_path: Path to the bldg functionality result output file
            archetype_mapping_path: Path to the arechetype mappings
            groupby_col_name: column name to group by, default to max_state

        Returns:
            dmg_ret_json: JSON of the damage state results ordered by cluster and category.
            func_ret_json: JSON of the building functionality results ordered by cluster and category.
            mapped_df: Dataframe of max damage state

        """
        inventory = pd.DataFrame(gpd.read_file("zip://" + inventory_path))
        dmg_result = pd.read_csv(dmg_result_path)
        bldg_func_df = pd.read_csv(func_result_path)
        bldg_func_df.rename(columns={'building_guid': 'guid'}, inplace=True)
        arch_mapping = pd.read_csv(archetype_mapping_path)

        max_state_df = DataProcessUtil.get_max_damage_state(dmg_result)
        dmg_ret_json = DataProcessUtil.create_mapped_dmg_result(inventory, max_state_df, arch_mapping,
                                                                groupby_col_name)

        func_ret_json = DataProcessUtil.create_mapped_func_result(inventory, bldg_func_df, arch_mapping)

        return dmg_ret_json, func_ret_json, max_state_df

    @staticmethod
    def create_mapped_dmg_result(inventory, dmg_result, arch_mapping, groupby_col_name="max_state"):
        """

        Args:
            inventory: dataframe represent inventory
            dmg_result: dmg_result that need to merge with inventory and be grouped
            archetype_mapping_path: Path to the arechetype mappings

        Returns:
            ret_json: JSON of the results ordered by cluster and category.

        """
        dmg_states = dmg_result[groupby_col_name].unique().tolist()  # get unique damage states
        dmg_merged = pd.merge(inventory, dmg_result, on='guid')
        mapped_df = pd.merge(dmg_merged, arch_mapping, on='archetype')
        unique_categories = arch_mapping.groupby(by=['cluster', 'category'], sort=False).count().reset_index()

        group_by = mapped_df.groupby(by=[groupby_col_name, 'cluster', 'category']).count().reset_index()
        group_by = group_by.loc[:, ['guid', groupby_col_name, 'cluster', 'category']]
        group_by.rename(columns={'guid': 'count'}, inplace=True)

        pivot = group_by.pivot_table(values='count', index=['cluster', 'category'], columns=groupby_col_name,
                                     fill_value=0)

        table = pd.DataFrame()
        table[['category', 'cluster']] = unique_categories[['category', 'cluster']]
        result_by_cluster = pd.merge(table, pivot, how='left', on=['cluster', 'category'])

        # Add missing max damage states. Handles case when no inventory fall under some damage states.
        result_by_cluster = result_by_cluster.reindex(result_by_cluster.columns.union(
            dmg_states, sort=False), axis=1, fill_value=0)

        result_by_category = result_by_cluster.groupby(by=['category'], sort=False).sum(min_count=1).reset_index()

        result_by_cluster[dmg_states] = result_by_cluster[dmg_states].fillna(-1).astype(int)
        result_by_category[dmg_states] = result_by_category[dmg_states].fillna(-1).astype(int)

        cluster_records = result_by_cluster.to_json(orient="records")
        category_records = result_by_category.to_json(orient="records")
        json_by_cluster = json.loads(cluster_records)
        json_by_category = json.loads(category_records)

        return {"by_cluster": json_by_cluster, "by_category": json_by_category}

    @staticmethod
    def create_mapped_func_result(inventory, bldg_func, arch_mapping):
        """

        Args:
            inventory: dataframe represent inventory
            dmg_result: dmg_result that need to merge with inventory and be grouped
            archetype_mapping_path: Path to the arechetype mappings

        Returns:
            ret_json: JSON of the results ordered by cluster and category.

        """
        func_state = ["percent_functional", "percent_non_functional", "num_functional", "num_non_functional"]
        func_merged = pd.merge(inventory, bldg_func, on='guid')
        mapped_df = pd.merge(func_merged, arch_mapping, on='archetype')
        unique_categories = arch_mapping.groupby(by=['category'], sort=False, as_index=False).count()['category']
        unique_cluster = arch_mapping.groupby(by=['cluster', 'category'], sort=False, as_index=False).count()[[
            'cluster', 'category']]

        # group by cluster
        result_by_cluster = mapped_df.groupby(by=['cluster', 'category'], sort=False, as_index=False).agg(
            {'guid': 'count',
             'probability': 'mean'})
        result_by_cluster.rename(columns={'guid': 'tot_count', 'probability': 'percent_functional'}, inplace=True)
        result_by_cluster["percent_non_functional"] = 1 - result_by_cluster["percent_functional"]
        result_by_cluster["num_functional"] = (result_by_cluster["tot_count"] * result_by_cluster[
            "percent_functional"]).round(0)
        result_by_cluster["num_non_functional"] = (result_by_cluster["tot_count"] * result_by_cluster[
            "percent_non_functional"]).round(0)
        result_by_cluster = result_by_cluster.drop('tot_count', 1)
        result_by_cluster = pd.merge(unique_cluster, result_by_cluster, how='left', on=['cluster', 'category'])
        # Add missing max damage states. Handles case when no inventory fall under some damage states.
        result_by_cluster = result_by_cluster.reindex(result_by_cluster.columns.union(
            func_state, sort=False), axis=1, fill_value=0)
        # replace NaN
        result_by_cluster[func_state] = result_by_cluster[func_state].fillna(-1)
        result_by_cluster[["num_functional", "num_non_functional"]] = result_by_cluster[["num_functional",
                                                                                         "num_non_functional"]].astype(
            int)

        # group by category
        result_by_category = mapped_df.groupby(by=['category'], sort=False, as_index=False).agg({'guid': 'count',
                                                                                                 'probability': 'mean'})
        result_by_category.rename(columns={'guid': 'tot_count', 'probability': 'percent_functional'}, inplace=True)
        result_by_category["percent_non_functional"] = 1 - result_by_category["percent_functional"]
        result_by_category["num_functional"] = (
                result_by_category["tot_count"] * result_by_category["percent_functional"]).round(0)
        result_by_category["num_non_functional"] = (
                result_by_category["tot_count"] * result_by_category["percent_non_functional"]).round(0)
        result_by_category = result_by_category.drop('tot_count', 1)
        result_by_category = pd.merge(unique_categories, result_by_category, how='left', on=['category'])
        # replace NaN
        result_by_category[func_state] = result_by_category[func_state].fillna(-1)
        result_by_category[["num_functional", "num_non_functional"]] = result_by_category[
            ["num_functional", "num_non_functional"]].astype(int)

        cluster_records = result_by_cluster.to_json(orient="records")
        category_records = result_by_category.to_json(orient="records")
        json_by_cluster = json.loads(cluster_records)
        json_by_category = json.loads(category_records)

        return {"by_cluster": json_by_cluster, "by_category": json_by_category}

    @staticmethod
    def get_max_damage_state(dmg_result):
        """Given damage result output decide the maximum damage state for each guid.

        Args:
            dmg_result (pd.DataFrame): damage result output, such as building damage, EPF damage and etc.

        Returns:
            pd.DataFrame: Pandas dataframe that has column GUID and column max_state.

        """
        if all(column in dmg_result.columns for column in ['DS_0', 'DS_1', 'DS_2', 'DS_3']):
            dmg_states = ['DS_0', 'DS_1', 'DS_2', 'DS_3']
        elif all(column in dmg_result.columns for column in ['insignific', 'moderate', 'heavy', 'complete']):
            dmg_states = ['insignific', 'moderate', 'heavy', 'complete']
        elif all(column in dmg_result.columns for column in ["ds-none", "ds-slight", "ds-moderat", "ds-extensi",
                                                             "ds-complet"]):
            dmg_states = ["ds-none", "ds-slight", "ds-moderat", "ds-extensi", "ds-complet"]
        else:
            raise ValueError("Invalid damage state names. Cannot create mapped max damage state.")

        guids = dmg_result[['guid']]
        max_val = dmg_result[dmg_states].max(axis=1)
        max_key = dmg_result[dmg_states].idxmax(axis=1)
        dmg_concat = pd.concat([guids, max_val, max_key], axis=1)
        dmg_concat.rename(columns={0: 'max_prob', 1: 'max_state'}, inplace=True)

        return dmg_concat
