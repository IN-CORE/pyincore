# Copyright (c) 2020 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import geopandas as gpd
import json
import pandas as pd
import numpy as np

from pyincore import Dataset, DataService
from functools import reduce


class DataProcessUtil:
    @staticmethod
    def get_mapped_result_from_analysis(
        client,
        inventory_id: str,
        dmg_result_dataset,
        bldg_func_dataset,
        archetype_mapping_id: str,
        groupby_col_name: str = "max_state",
        arch_col="archetype",
    ):
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
            arch_col: column name for the archetype to perform the merge

        """
        bldg_inv = Dataset.from_data_service(inventory_id, DataService(client))
        inventory = pd.DataFrame(gpd.read_file(bldg_inv.local_file_path))

        dmg_result = dmg_result_dataset.get_dataframe_from_csv()

        bldg_func_df = bldg_func_dataset.get_dataframe_from_csv()
        bldg_func_df.rename(
            columns={"building_guid": "guid", "samples": "failure"}, inplace=True
        )

        arch_mapping = Dataset.from_data_service(
            archetype_mapping_id, DataService(client)
        ).get_dataframe_from_csv()

        max_state_df = DataProcessUtil.get_max_damage_state(dmg_result)
        dmg_ret_json = DataProcessUtil.create_mapped_dmg_result(
            inventory, max_state_df, arch_mapping, groupby_col_name, arch_col
        )
        func_ret_json = DataProcessUtil.create_mapped_func_result(
            inventory, bldg_func_df, arch_mapping, arch_col
        )

        return dmg_ret_json, func_ret_json, max_state_df

    @staticmethod
    def get_mapped_result_from_dataset_id(
        client,
        inventory_id: str,
        dmg_result_id: str,
        bldg_func_id,
        archetype_mapping_id: str,
        groupby_col_name: str = "max_state",
        arch_col="archetype",
    ):
        """Use this if your damage results are already stored in the data service and you have their dataset ids.
        All the inputs (except groupby_col_name) are dataset ids.

        Args:
            client: Service client with authentication info
            inventory_id: Inventory dataset id
            dmg_result_id: Damage result dataset id
            bldg_func_id: Incore dataset for building func id
            archetype_mapping_id: Mapping id dataset for archetype
            groupby_col_name: column name to group by, default to max_state
            arch_col: column name for the archetype to perform the merge

        Returns:
            dmg_ret_json: JSON of the damage state results ordered by cluster and category.
            func_ret_json: JSON of the building functionality results ordered by cluster and category.
            max_state_df: Dataframe of max damage state

        """
        bldg_inv = Dataset.from_data_service(inventory_id, DataService(client))
        inventory = pd.DataFrame(gpd.read_file(bldg_inv.local_file_path))

        dmg_result_dataset = Dataset.from_data_service(
            dmg_result_id, DataService(client)
        )
        dmg_result = dmg_result_dataset.get_dataframe_from_csv()

        bldg_func_dataset = Dataset.from_data_service(bldg_func_id, DataService(client))
        bldg_func_df = bldg_func_dataset.get_dataframe_from_csv()
        bldg_func_df.rename(
            columns={"building_guid": "guid", "samples": "failure"}, inplace=True
        )

        archtype_mapping_dataset = Dataset.from_data_service(
            archetype_mapping_id, DataService(client)
        )
        arch_mapping = archtype_mapping_dataset.get_dataframe_from_csv()

        max_state_df = DataProcessUtil.get_max_damage_state(dmg_result)
        dmg_ret_json = DataProcessUtil.create_mapped_dmg_result(
            inventory, max_state_df, arch_mapping, groupby_col_name, arch_col
        )
        func_ret_json = DataProcessUtil.create_mapped_func_result(
            inventory, bldg_func_df, arch_mapping, arch_col
        )

        return dmg_ret_json, func_ret_json, max_state_df

    @staticmethod
    def get_mapped_result_from_path(
        inventory_path: str,
        dmg_result_path: str,
        func_result_path: str,
        archetype_mapping_path: str,
        groupby_col_name: str,
        arch_col="archetype",
    ):
        """

        Args:
            inventory_path: Path to the zip file containing the inventory
                    example: /Users/myuser/5f9091df3e86721ed82f701d.zip
            dmg_result_path: Path to the damage result output file
            func_result_path: Path to the bldg functionality result output file
            archetype_mapping_path: Path to the arechetype mappings
            groupby_col_name: column name to group by, default to max_state
            arch_col: column name for the archetype to perform the merge

        Returns:
            dmg_ret_json: JSON of the damage state results ordered by cluster and category.
            func_ret_json: JSON of the building functionality results ordered by cluster and category.
            mapped_df: Dataframe of max damage state

        """
        inventory = pd.DataFrame(gpd.read_file("zip://" + inventory_path))
        dmg_result = pd.read_csv(dmg_result_path)
        bldg_func_df = pd.read_csv(func_result_path)
        bldg_func_df.rename(
            columns={"building_guid": "guid", "samples": "failure"}, inplace=True
        )
        arch_mapping = pd.read_csv(archetype_mapping_path)

        max_state_df = DataProcessUtil.get_max_damage_state(dmg_result)
        dmg_ret_json = DataProcessUtil.create_mapped_dmg_result(
            inventory, max_state_df, arch_mapping, groupby_col_name, arch_col
        )

        func_ret_json = DataProcessUtil.create_mapped_func_result(
            inventory, bldg_func_df, arch_mapping, arch_col
        )

        return dmg_ret_json, func_ret_json, max_state_df

    @staticmethod
    def create_mapped_dmg(
        inventory,
        dmg_result,
        arch_mapping,
        groupby_col_name="max_state",
        arch_col="archetype",
    ):
        """This is a helper function as the operations performed in create_mapped_dmg_result and create_mapped_dmg_result_gal are same.

        Returns
        -------
        Tuple of two dataframes
            returns dataframes of the results ordered by cluster and category.
        """

        dmg_states = (
            dmg_result[groupby_col_name].unique().tolist()
        )  # get unique damage states
        dmg_merged = pd.merge(inventory, dmg_result, on="guid")
        mapped_df = pd.merge(dmg_merged, arch_mapping, on=arch_col)
        unique_categories = (
            arch_mapping.groupby(by=["cluster", "category"], sort=False)
            .count()
            .reset_index()
        )

        group_by = (
            mapped_df.groupby(by=[groupby_col_name, "cluster", "category"])
            .count()
            .reset_index()
        )
        group_by = group_by.loc[:, ["guid", groupby_col_name, "cluster", "category"]]
        group_by.rename(columns={"guid": "count"}, inplace=True)

        pivot = group_by.pivot_table(
            values="count",
            index=["cluster", "category"],
            columns=groupby_col_name,
            fill_value=0,
        )

        table = pd.DataFrame()
        table[["category", "cluster"]] = unique_categories[["category", "cluster"]]
        result_by_cluster = pd.merge(
            table, pivot, how="left", on=["cluster", "category"]
        )

        # Add missing max damage states. Handles case when no inventory fall under some damage states.
        result_by_cluster = result_by_cluster.reindex(
            result_by_cluster.columns.union(dmg_states, sort=False),
            axis=1,
            fill_value=0,
        )

        result_by_category = (
            result_by_cluster.groupby(by=["category"], sort=False)
            .sum(min_count=1)
            .reset_index()
        )

        result_by_cluster[dmg_states] = (
            result_by_cluster[dmg_states].fillna(-1).astype(int)
        )
        result_by_category[dmg_states] = (
            result_by_category[dmg_states].fillna(-1).astype(int)
        )

        return result_by_cluster, result_by_category

    @staticmethod
    def create_mapped_dmg_result(
        inventory,
        dmg_result,
        arch_mapping,
        groupby_col_name="max_state",
        arch_col="archetype",
    ):
        """

        Args:
            inventory: dataframe represent inventory
            dmg_result: dmg_result that need to merge with inventory and be grouped
            arch_mapping: Path to the archetype mappings

        Returns:
            ret_json: JSON of the results ordered by cluster and category.

        """

        result_by_cluster, result_by_category = DataProcessUtil.create_mapped_dmg(
            inventory, dmg_result, arch_mapping, groupby_col_name, arch_col
        )

        result_by_cluster.rename(
            columns={
                "DS_0": "Insignificant",
                "DS_1": "Moderate",
                "DS_2": "Extensive",
                "DS_3": "Complete",
            },
            inplace=True,
        )
        result_by_category.rename(
            columns={
                "DS_0": "Insignificant",
                "DS_1": "Moderate",
                "DS_2": "Extensive",
                "DS_3": "Complete",
            },
            inplace=True,
        )

        cluster_records = result_by_cluster.to_json(orient="records")
        category_records = result_by_category.to_json(orient="records")
        json_by_cluster = json.loads(cluster_records)
        json_by_category = json.loads(category_records)

        return {"by_cluster": json_by_cluster, "by_category": json_by_category}

    @staticmethod
    def create_mapped_func_result(
        inventory, bldg_func, arch_mapping, arch_col="archetype"
    ):
        """

        Args:
            inventory: dataframe represent inventory
            bldg_func: building func state dataset
            arch_mapping: Path to the archetype mappings
            arch_col: archetype column to use for the clustering

        Returns:
            ret_json: JSON of the results ordered by cluster and category.

        """

        def _sum_average(series):
            return reduce(lambda x, y: np.mean(x + y).round(0), series)

        func_state = [
            "percent_functional",
            "percent_non_functional",
            "num_functional",
            "num_non_functional",
        ]

        # unify mcs and bldg func naming
        bldg_func.rename(
            columns={"building_guid": "guid", "samples": "failure"}, inplace=True
        )

        # drop nan but count their numbers
        count_null = (bldg_func["failure"] == "").sum()
        bldg_func = bldg_func[bldg_func["failure"] != ""]

        func_merged = pd.merge(inventory, bldg_func, on="guid")
        mapped_df = pd.merge(func_merged, arch_mapping, on=arch_col)
        unique_categories = arch_mapping.groupby(
            by=["category"], sort=False, as_index=False
        ).count()["category"]
        unique_cluster = arch_mapping.groupby(
            by=["cluster", "category"], sort=False, as_index=False
        ).count()[["cluster", "category"]]

        mapped_df = mapped_df[["guid", "failure", "category", "cluster"]]
        mapped_df["failure_array"] = mapped_df["failure"].apply(
            lambda x: np.array([int(x) for x in x.split(",")])
        )

        def _group_by(by_column, unique):
            # group by cluster
            result = mapped_df.groupby(by=by_column, sort=False, as_index=False).agg(
                {"guid": "count", "failure_array": [_sum_average]}
            )

            # clean up
            result.rename(
                columns={"guid": "tot_count", "failure_array": "num_functional"},
                inplace=True,
            )

            # 0 (failed), 1 (not failed). MCS
            # 0 otherwise (not functional), 1 (functional),  Functionality
            result["num_non_functional"] = (
                result["tot_count"].squeeze() - result["num_functional"].squeeze()
            )
            result["percent_functional"] = (
                result["num_functional"].squeeze() / result["tot_count"].squeeze()
            )
            result["percent_non_functional"] = 1 - result["percent_functional"]

            # remove the tuples in column
            result.columns = [x[0] if len(x) > 1 else x for x in result.columns]

            # more clean up
            result = pd.merge(unique, result, how="left", on=by_column)

            # Add missing max damage states. Handles case when no inventory fall under some damage states.
            result = result.reindex(
                result.columns.union(func_state, sort=False), axis=1, fill_value=0
            )

            # replace NaN
            result[func_state] = result[func_state].fillna(-1)
            result["tot_count"] = result["tot_count"].fillna(-1)
            result[["num_functional", "num_non_functional"]] = result[
                ["num_functional", "num_non_functional"]
            ].astype(int)

            return result

        result_by_cluster = _group_by(
            by_column=["cluster", "category"], unique=unique_cluster
        )
        result_by_category = _group_by(by_column=["category"], unique=unique_categories)

        cluster_records = result_by_cluster.to_json(orient="records")
        category_records = result_by_category.to_json(orient="records")
        json_by_cluster = json.loads(cluster_records)
        json_by_category = json.loads(category_records)

        return {
            "by_cluster": json_by_cluster,
            "by_category": json_by_category,
            "NA": int(count_null),
        }

    @staticmethod
    def get_max_damage_state(dmg_result):
        """Given damage result output decide the maximum damage state for each guid.

        Args:
            dmg_result (pd.DataFrame): damage result output, such as building damage, EPF damage and etc.

        Returns:
            pd.DataFrame: Pandas dataframe that has column GUID and column max_state.

        """
        if all(
            column in dmg_result.columns for column in ["DS_0", "DS_1", "DS_2", "DS_3"]
        ):
            dmg_states = ["DS_0", "DS_1", "DS_2", "DS_3"]
        elif all(
            column in dmg_result.columns
            for column in ["insignific", "moderate", "heavy", "complete"]
        ):
            dmg_states = ["insignific", "moderate", "heavy", "complete"]
        elif all(
            column in dmg_result.columns
            for column in [
                "ds-none",
                "ds-slight",
                "ds-moderat",
                "ds-extensi",
                "ds-complet",
            ]
        ):
            dmg_states = [
                "ds-none",
                "ds-slight",
                "ds-moderat",
                "ds-extensi",
                "ds-complet",
            ]
        else:
            raise ValueError(
                "Invalid damage state names. Cannot create mapped max damage state."
            )

        guids = dmg_result[["guid"]]
        max_val = dmg_result[dmg_states].max(axis=1)
        max_key = dmg_result[dmg_states].dropna(how="all").idxmax(axis=1)
        dmg_concat = pd.concat([guids, max_val, max_key], axis=1)
        dmg_concat.rename(columns={0: "max_prob", 1: "max_state"}, inplace=True)

        return dmg_concat

    @staticmethod
    def create_mapped_dmg_result_gal(
        inventory,
        max_dmg_result,
        arch_mapping,
        groupby_col_name="max_state",
        arch_col="archetype",
    ):
        """
            This function does similar operation as create_mapped_dmg_result but it is used for Galveston as it has different mapping.
        Args:
            inventory: dataframe represent inventory
            dmg_result: dmg_result that need to merge with inventory and be grouped
            arch_mapping: Path to the archetype mappings

        Returns:
            ret_json: JSON of the results ordered by cluster and category.

        """

        """
            Remap the Damage States to Affected, Minor, Major, Destroyed:
            - DS_0 and DS_1 are Affected
            - DS_2 is Minor
            - DS_3 is Major if it is not DS_3 in the sw_max_ds column
            - and if DS_3 in the max_dmg_result["sw_max_ds"] then set it as Destroyed

            To do this, map DS_1 -> DS_0, DS_2 -> DS_1, DS_3 -> DS_2 and create a new DS_3 based on the sw_max_ds column value.
            Then rename them to their respective categories.
        """

        max_dmg_result.loc[
            max_dmg_result["max_state"] == "DS_0", "max_state"
        ] = "Affected"
        max_dmg_result.loc[
            max_dmg_result["max_state"] == "DS_1", "max_state"
        ] = "Affected"
        max_dmg_result.loc[max_dmg_result["max_state"] == "DS_2", "max_state"] = "Minor"
        max_dmg_result.loc[
            (
                (max_dmg_result["max_state"] == "DS_3")
                & (max_dmg_result["sw_max_ds"] != "DS_3")
            ),
            "max_state",
        ] = "Major"
        max_dmg_result.loc[
            max_dmg_result["sw_max_ds"] == "DS_3", "max_state"
        ] = "Destroyed"

        result_by_cluster, result_by_category = DataProcessUtil.create_mapped_dmg(
            inventory, max_dmg_result, arch_mapping, groupby_col_name, arch_col
        )

        cluster_records = result_by_cluster.to_json(orient="records")
        category_records = result_by_category.to_json(orient="records")
        json_by_cluster = json.loads(cluster_records)
        json_by_category = json.loads(category_records)

        return {"by_cluster": json_by_cluster, "by_category": json_by_category}
