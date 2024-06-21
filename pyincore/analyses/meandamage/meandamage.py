# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import BaseAnalysis, AnalysisUtil
from itertools import repeat
from typing import List
import concurrent.futures
import collections


class MeanDamage(BaseAnalysis):
    """
    Args:
        incore_client (IncoreClient): Service authentication.
    """

    def __init__(self, incore_client):
        super(MeanDamage, self).__init__(incore_client)

    def get_spec(self):
        """Get specifications of the mean damage calculation.

        Returns:
            obj: A JSON object of specifications of the mean damage calculation.

        """
        return {
            "name": "mean-damage",
            "description": "calculate the mean and expected damage using damage ratio table",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "result dataset name",
                    "type": str,
                },
                {
                    "id": "damage_interval_keys",
                    "required": True,
                    "description": "Column name of the damage interval must be four and ranged in order",
                    "type": List[str],
                },
                {
                    "id": "num_cpu",
                    "required": False,
                    "description": "If using parallel execution, the number of cpus to request",
                    "type": int,
                },
            ],
            "input_datasets": [
                {
                    "id": "damage",
                    "required": True,
                    "description": "damage result that has damage intervals in it",
                    "type": [
                        "ergo:buildingDamageVer4",
                        "ergo:buildingDamageVer5",
                        "ergo:buildingDamageVer6",
                        "ergo:nsBuildingInventoryDamage",
                        "ergo:nsBuildingInventoryDamageVer2",
                        "ergo:nsBuildingInventoryDamageVer3",
                        "ergo:nsBuildingInventoryDamageVer4",
                        "ergo:bridgeDamage",
                        "ergo:bridgeDamageVer2",
                        "ergo:bridgeDamageVer3",
                        "ergo:roadDamage",
                        "ergo:roadDamageVer2",
                        "ergo:roadDamageVer3",
                    ],
                },
                {
                    "id": "dmg_ratios",
                    "required": True,
                    "description": "Damage Ratios table",
                    "type": [
                        "ergo:buildingDamageRatios",
                        "ergo:bridgeDamageRatios",
                        "ergo:buildingContentDamageRatios",
                        "ergo:buildingASDamageRatios",
                        "ergo:buildingDSDamageRatios",
                        "ergo:roadDamageRatios",
                    ],
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "description": "CSV file of mean damage",
                    "type": "ergo:meanDamage",
                }
            ],
        }

    def run(self):
        """Executes mean damage calculation."""

        # read in file and parameters
        damage = self.get_input_dataset("damage").get_csv_reader()
        damage_result = AnalysisUtil.get_csv_table_rows(damage, ignore_first_row=False)

        dmg_ratio_csv = self.get_input_dataset("dmg_ratios").get_csv_reader()
        dmg_ratio_tbl = AnalysisUtil.get_csv_table_rows(dmg_ratio_csv)

        # setting number of cpus to use
        user_defined_cpu = 1
        if (
            not self.get_parameter("num_cpu") is None
            and self.get_parameter("num_cpu") > 0
        ):
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(
            self, len(damage_result), user_defined_cpu
        )

        avg_bulk_input_size = int(len(damage_result) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = damage_result
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count : count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.mean_damage_concurrent_future(
            self.mean_damage_bulk_input,
            num_workers,
            inventory_args,
            repeat(dmg_ratio_tbl),
        )
        self.set_result_csv_data(
            "result", results, name=self.get_parameter("result_name")
        )
        return True

    def mean_damage_concurrent_future(self, function_name, parallelism, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            parallelism (int): Number of workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """
        output = []
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=parallelism
        ) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def mean_damage_bulk_input(self, damage, dmg_ratio_tbl):
        """Run analysis for mean damage calculation

        Args:
            damage (obj): output of building/bridge/waterfacility/epn damage that has damage interval
            dmg_ratio_tbl (list): damage ratio table

        Returns:
            list: A list of ordered dictionaries with mean damage, deviation, and other data/metadata.

        """
        damage_interval_keys = self.get_parameter("damage_interval_keys")

        data_type = self.get_input_dataset("damage").data_type

        if ":bridgeDamage" in data_type:
            is_bridge = True
        else:
            is_bridge = False

        result = []
        for dmg in damage:
            result.append(
                self.mean_damage(dmg, dmg_ratio_tbl, damage_interval_keys, is_bridge)
            )

        return result

    def mean_damage(self, dmg, dmg_ratio_tbl, damage_interval_keys, is_bridge):
        """Calculates mean damage based on damage probabilities and damage ratios

        Args:
            dmg (obj): dmg analysis output for a single entity in the built environment
            dmg_ratio_tbl (list): dmg ratio table.
            damage_interval_keys (list): damage interval keys
            is_bridge (bool): a boolean to indicate if the inventory type is bridge.
            Bridge has its own way of calculating mean damage

        Returns:
            OrderedDict: A dictionary with mean damage, deviation, and other data/metadata.

        """
        results = collections.OrderedDict()
        results.update(dmg)

        if is_bridge:
            # need to calculate bridge span
            if (
                "spans" in dmg.keys()
                and dmg["spans"] is not None
                and dmg["spans"].isdigit()
            ):
                bridge_spans = int(dmg["spans"])
            else:
                bridge_spans = 1

            if bridge_spans > 10:
                bridge_spans = 10
                print(
                    "A bridge was found with greater than 10 spans: "
                    + dmg["guid"]
                    + ". Default to 10 bridge spans."
                )

            mean_damage = AnalysisUtil.calculate_mean_damage(
                dmg_ratio_tbl, dmg, damage_interval_keys, is_bridge, bridge_spans
            )
        else:
            mean_damage = AnalysisUtil.calculate_mean_damage(
                dmg_ratio_tbl, dmg, damage_interval_keys, is_bridge
            )
        results.update(mean_damage)

        # bridge doesn't calculates deviation
        if not is_bridge:
            mean_damage_dev = AnalysisUtil.calculate_mean_damage_std_deviation(
                dmg_ratio_tbl, dmg, mean_damage["meandamage"], damage_interval_keys
            )
            results.update(mean_damage_dev)
        else:
            expected_damage = AnalysisUtil.get_expected_damage(
                mean_damage["meandamage"], dmg_ratio_tbl
            )
            results["expectval"] = expected_damage

        return results
