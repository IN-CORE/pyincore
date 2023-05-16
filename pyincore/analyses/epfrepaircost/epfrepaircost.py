# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import concurrent.futures
from itertools import repeat

from pyincore import AnalysisUtil, GeoUtil
from pyincore import BaseAnalysis, HazardService, FragilityService
from pyincore.models.dfr3curve import DFR3Curve


class EpfRepairCost(BaseAnalysis):
    """Computes electric power facility repair cost.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(EpfRepairCost, self).__init__(incore_client)

    def run(self):
        """Executes electric power facility repair cost analysis."""

        epf_df = self.get_input_dataset("epfs").get_dataframe_from_shapefile()
        sample_damage_states_df = self.get_input_dataset("sample_damage_states").get_dataframe_from_csv()
        replacement_cost = self.get_input_dataset("replacement_cost").get_dataframe_from_csv()

        # join damage state, replacement cost, with original inventory
        epf_df = epf_df.merge(sample_damage_states_df, on="guid")
        epf_df = epf_df.merge(replacement_cost, on="guid")
        epf_set = epf_df.to_dict(orient="records")

        user_defined_cpu = 1
        if not self.get_parameter("num_cpu") is None and self.get_parameter("num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(self, len(epf_set), user_defined_cpu)

        avg_bulk_input_size = int(len(epf_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(epf_set)
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        repair_costs = self.epf_repair_cost_concurrent_future(self.epf_repair_cost_bulk_input, num_workers,
                                                              inventory_args)
        self.set_result_csv_data("result", repair_costs, name=self.get_parameter("result_name") + "_repair_cost")

        return True

    def epf_repair_cost_concurrent_future(self, function_name, num_workers, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            num_workers (int): Maximum number workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with epf damage values and other data/metadata.

        """

        output_ds = []
        output_dmg = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output_ds.extend(ret1)
                output_dmg.extend(ret2)

        return output_ds, output_dmg

    def epf_repair_cost_bulk_input(self, epfs):
        """Run analysis for multiple epfs.

        Args:
            epfs (list): Multiple epfs from input inventory set.
            hazard_type (str): A type of hazard exposure (earthquake, tsunami, tornado, or hurricane).
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with epf damage values and other data/metadata.

        """
        # read in the damage ratio tables
        substation_dmg_ratios_csv = self.get_input_dataset("substation_dmg_ratios").get_csv_reader()
        substation_dmg_ratio_tbl = AnalysisUtil.get_csv_table_rows(substation_dmg_ratios_csv)

        circuit_dmg_ratios_csv = self.get_input_dataset("substation_dmg_ratios").get_csv_reader()
        circuit_dmg_ratios_tbl = AnalysisUtil.get_csv_table_rows(circuit_dmg_ratios_csv)

        generation_plant_dmg_ratios_csv = self.get_input_dataset("substation_dmg_ratios").get_csv_reader()
        generation_plant_dmg_ratios_tbl = AnalysisUtil.get_csv_table_rows(generation_plant_dmg_ratios_csv)

        epf_substation_types = ["ESSL", "ESSM", "ESSH"]
        if not self.get_parameter("epf_substation_types") is None:
            epf_substation_types = self.get_parameter("epf_substation_types")

        epf_circuit_types = ["EDC"]
        if not self.get_parameter("epf_circuit_types") is None:
            epf_substation_types = self.get_parameter("epf_circuit_types")

        epf_generation_plant_types = ["EPPL", "EPPM", "EPPS"]
        if not self.get_parameter("epf_generation_plant_types") is None:
            epf_substation_types = self.get_parameter("epf_generation_plant_types")

        repair_costs = []

        for epf in epfs:
            rc = dict()
            rc["guid"] = epf["guid"]

            epf_type = epf["utilfcltyc"]
            dmg_ratio_tbl = []

            # substations
            for epf_substation_type in epf_substation_types:
                # partial match since some times it's ESSL2
                if epf_substation_type in epf_type:
                    dmg_ratio_tbl = substation_dmg_ratio_tbl

            # distribution circuits
            for epf_circuit_type in epf_circuit_types:
                if epf_circuit_type in epf_type:
                    dmg_ratio_tbl = circuit_dmg_ratios_tbl

            # generation plant
            for epf_generation_plant_type in epf_generation_plant_types:
                if epf_generation_plant_type in epf_type:
                    dmg_ratio_tbl = generation_plant_dmg_ratios_tbl

            sample_damage_states = epf["sample_damage_states"].split(",")
            repair_cost = ["0"] * len(sample_damage_states)
            for n, ds in enumerate(sample_damage_states):
                for dmg_ratio_row in dmg_ratio_tbl:
                    if dmg_ratio_row["Damage State"] == ds:
                        dr = dmg_ratio_row["Best Mean Damage Ratio"]
                        repair_cost[n] = str(epf["replacement_cost"] * dr)

            rc["p_budget"] = ','.join(repair_cost)
            rc["q"] = ','.join(repair_cost)

            repair_costs.append(rc)

        return repair_costs

    def get_spec(self):
        """Get specifications of the epf damage analysis.

        Returns:
            obj: A JSON object of specifications of the epf damage analysis.

        """
        return {
            "name": "epf-damage",
            "description": "Electric Power Facility damage analysis.",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "A name of the resulting dataset",
                    "type": str
                },
                {
                    "id": "num_cpu",
                    "required": False,
                    "description": "If using parallel execution, the number of cpus to request.",
                    "type": int
                },
                {
                    "id": "epf_substation_types",
                    "required": False,
                    "description": "EPF substation types. Default to HAZUS code ESSL, ESSM, ESSH",
                    "type": list
                },
                {
                    "id": "epf_circuit_types",
                    "required": False,
                    "description": "EPF circuit types. Default to HAZUS code EDC",
                    "type": list
                },
                {
                    "id": "epf_generation_plant_types",
                    "required": False,
                    "description": "EPF substation types. Default to HAZUS code EPPL, EPPM, EPPS",
                    "type": list
                },
            ],
            "input_datasets": [
                {
                    "id": "epfs",
                    "required": True,
                    "description": "Electric Power Facility Inventory",
                    "type": ["incore:epf",
                             "ergo:epf",
                             "incore:epfVer2"
                             ],
                },
                {
                    "id": "replacement_cost",
                    "required": True,
                    "description": "Repair cost of the node in the complete damage state (= Replacement cost)",
                    "type": ["incore:replacementCost"],
                },
                {
                    "id": "sample_damage_states",
                    "required": True,
                    "description": "sample damage states from Monte Carlo Simulation",
                    "type": ["incore:sampleDamageState"]
                },
                {
                    "id": "substation_dmg_ratios",
                    "required": True,
                    "description": "Damage Ratios table",
                    "type": ["incore:epfDamageRatios"]
                },
                {
                    "id": "circuit_dmg_ratios",
                    "required": True,
                    "description": "Damage Ratios table",
                    "type": ["incore:epfDamageRatios"]
                },
                {
                    "id": "generation_plant_dmg_ratios",
                    "required": True,
                    "description": "Damage Ratios table",
                    "type": ["incore:epfDamageRatios"]
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "parent_type": "epfs",
                    "description": "A csv file with repair cost for each electric power facility",
                    "type": "incore:epfRepairCost"
                }
            ]
        }
