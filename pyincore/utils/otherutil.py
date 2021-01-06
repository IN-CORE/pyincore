# Copyright (c) 2020 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import geopandas as gpd
import json
import pandas as pd

from pyincore import IncoreClient, Dataset, FragilityService, MappingSet, DataService, AnalysisUtil


class OtherUtil:
    @staticmethod
    def get_mapped_result_from_analysis(client, inventory_id: str, dmg_result_dataset, archetype_mapping_id: str):
        """

        Args:
            client: Service client with authentication info
            inventory_id: Inventory dataset id
            dmg_result_dataset: Incore dataset for damage result
            archetype_mapping_id: Mapping id dataset for archetype

        Returns:
            ret_json: JSON of the results ordered by cluster and category. Also creates a csv file with max damage state
            mapped_df: Dataframe of max damage state

        """
        bldg_inv = Dataset.from_data_service(inventory_id, DataService(client))
        buildings = pd.DataFrame(gpd.read_file(bldg_inv.local_file_path))
        dmg_result = dmg_result_dataset.get_dataframe_from_csv()
        archtype_mapping_dataset = Dataset.from_data_service(archetype_mapping_id, DataService(client))
        arch_mapping = pd.DataFrame(archtype_mapping_dataset.get_csv_reader())

        ret_json, mapped_df = OtherUtil.create_mapped_result(buildings, dmg_result, arch_mapping)

        return ret_json, mapped_df

    @staticmethod
    def get_mapped_result_from_dataset_id(client, inventory_id: str, dmg_result_id: str, archetype_mapping_id: str):
        """

        Args:
            client: Service client with authentication info
            inventory_id: Inventory dataset id
            dmg_result_id: Damage result dataset id
            archetype_mapping_id: Mapping id dataset for archetype

        Returns:
            ret_json: JSON of the results ordered by cluster and category. Also creates a csv file with max damage state
            mapped_df: Dataframe of max damage state

        """
        bldg_inv = Dataset.from_data_service(inventory_id, DataService(client))
        buildings = pd.DataFrame(gpd.read_file(bldg_inv.local_file_path))
        dmg_result_dataset = Dataset.from_data_service(dmg_result_id, DataService(client))
        dmg_result = dmg_result_dataset.get_dataframe_from_csv()
        archtype_mapping_dataset = Dataset.from_data_service(archetype_mapping_id, DataService(client))
        arch_mapping = archtype_mapping_dataset.get_dataframe_from_csv()

        ret_json, mapped_df = OtherUtil.create_mapped_result(buildings, dmg_result, arch_mapping)

        return ret_json, mapped_df

    @staticmethod
    def get_mapped_result_from_path(inventory_path: str, dmg_result_path: str, archetype_mapping_path: str):
        """

        Args:
            inventory_path: Path to the zip file containing the inventory
                    example: /Users/myuser/5f9091df3e86721ed82f701d.zip
            dmg_result_path: Path to the damage result output file
            archetype_mapping_path: Path to the arechetype mappings

        Returns:
            ret_json: JSON of the results ordered by cluster and category. Also creates a csv file with max damage state
            mapped_df: Dataframe of max damage state

        """
        buildings = pd.DataFrame(gpd.read_file("zip://" + inventory_path))
        dmg_result = pd.read_csv(dmg_result_path)
        arch_mapping = pd.read_csv(archetype_mapping_path)

        ret_json, mapped_df = OtherUtil.create_mapped_result(buildings, dmg_result, arch_mapping)

        return ret_json, mapped_df

    @staticmethod
    def create_mapped_result(buildings, dmg_result, arch_mapping):
        """

        Args:
            inventory_path: Path to the zip file containing the inventory
                    example: /Users/myuser/5f9091df3e86721ed82f701d.zip
            dmg_result_path: Path to the damage result output file
            archetype_mapping_path: Path to the arechetype mappings

        Returns:
            ret_json: JSON of the results ordered by cluster and category. Also creates a csv file with max damage state
            mapped_df: Dataframe of max damage state


        """
        # TODO: Do not hardcode this and fetch them from the damage result columns, if it's possible
        dmg_states = ['insignific', 'moderate', 'heavy', 'complete']

        unique_categories = arch_mapping.groupby(by=['cluster', 'category'], sort=False).count().reset_index()

        guids = dmg_result[['guid']]
        max_val = dmg_result[dmg_states].max(axis=1)
        max_key = dmg_result[dmg_states].idxmax(axis=1)
        dmg_concat = pd.concat([guids, max_val, max_key], axis=1)
        dmg_concat.rename(columns={0: 'max_prob', 1: 'max_state'}, inplace=True)
        dmg_merged = pd.merge(buildings, dmg_concat, on='guid')
        [['guid', 'geometry', 'archetype', 'max_prob', 'max_state']]
        mapped_df = pd.merge(dmg_merged, arch_mapping, on='archetype')

        # mapped.to_csv("bldDmgMaxDamageState.csv", columns=['guid', 'max_state'], index=False)

        group_by = mapped_df.groupby(by=['max_state', 'cluster', 'category']).count().reset_index()
        group_by = group_by.loc[:, ['guid', 'max_state', 'cluster', 'category']]
        group_by.rename(columns={'guid': 'count'}, inplace=True)

        pivot = group_by.pivot_table(values='count', index=['cluster', 'category'], columns='max_state', fill_value=0)

        table = pd.DataFrame()
        table[['category', 'cluster']] = unique_categories[['category', 'cluster']]
        result_by_cluster = pd.merge(table, pivot, how='left', on=['cluster', 'category'])

        # Add missing max damage states. Handles case when no buildings fall under some damage states.
        result_by_cluster = result_by_cluster.reindex(result_by_cluster.columns.union(
            dmg_states, sort=False), axis=1, fill_value=0)

        result_by_category = result_by_cluster.groupby(by=['category'], sort=False).sum(min_count=1).reset_index()

        result_by_cluster[dmg_states] = result_by_cluster[dmg_states].fillna(-1).astype(int)
        result_by_category[dmg_states] = result_by_category[dmg_states].fillna(-1).astype(int)

        cluster_records = result_by_cluster.to_json(orient="records")
        category_records = result_by_category.to_json(orient="records")
        json_by_cluster = json.loads(cluster_records)
        json_by_category = json.loads(category_records)

        ret_json = json.dumps({"by_cluster": json_by_cluster, "by_category": json_by_category})

        return ret_json, mapped_df
