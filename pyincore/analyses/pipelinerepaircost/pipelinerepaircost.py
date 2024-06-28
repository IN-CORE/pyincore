# Copyright (c) 2023 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import concurrent.futures

from pyincore import AnalysisUtil
from pyincore import BaseAnalysis


class PipelineRepairCost(BaseAnalysis):
    """Computes pipeline repair cost.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(PipelineRepairCost, self).__init__(incore_client)

    def run(self):
        """Executes pipline facility repair cost analysis."""

        pipeline_df = self.get_input_dataset("pipeline").get_dataframe_from_shapefile()
        pipeline_dmg_df = self.get_input_dataset(
            "pipeline_dmg"
        ).get_dataframe_from_csv()
        replacement_cost = self.get_input_dataset(
            "replacement_cost"
        ).get_dataframe_from_csv()

        # join damage, replacement cost, with original inventory
        pipeline_df = pipeline_df.merge(pipeline_dmg_df, on="guid")
        pipeline_df = pipeline_df.merge(replacement_cost, on="guid")
        pipeline_set = pipeline_df.to_dict(orient="records")

        user_defined_cpu = 1
        if (
            not self.get_parameter("num_cpu") is None
            and self.get_parameter("num_cpu") > 0
        ):
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(
            self, len(pipeline_set), user_defined_cpu
        )

        avg_bulk_input_size = int(len(pipeline_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(pipeline_set)
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count : count + avg_bulk_input_size])
            count += avg_bulk_input_size

        repair_costs = self.pipeline_repair_cost_concurrent_future(
            self.pipeline_repair_cost_bulk_input, num_workers, inventory_args
        )
        self.set_result_csv_data(
            "result",
            repair_costs,
            name=self.get_parameter("result_name") + "_repair_cost",
        )

        return True

    def pipeline_repair_cost_concurrent_future(self, function_name, num_workers, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            num_workers (int): Maximum number workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with pipeline repair cost values and other data/metadata.

        """

        output = []
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=num_workers
        ) as executor:
            for ret1 in executor.map(function_name, *args):
                output.extend(ret1)

        return output

    def pipeline_repair_cost_bulk_input(self, pipelines):
        """Run analysis for multiple pipelines.

        Args:
            pipelines (list): Multiple pipelines from input inventory set.

        Returns:
            list: A list of ordered dictionaries with pipeline repair cost values and other data/metadata.

        """
        # read in the damage ratio tables
        pipeline_dmg_ratios_csv = self.get_input_dataset(
            "pipeline_dmg_ratios"
        ).get_csv_reader()
        dmg_ratio_tbl = AnalysisUtil.get_csv_table_rows(
            pipeline_dmg_ratios_csv, ignore_first_row=False
        )

        segment_length = self.get_parameter("segment_length")
        if segment_length is None:
            segment_length = 20  # 20 feet

        diameter = self.get_parameter("diameter")
        if diameter is None:
            diameter = 20  # 20 inch

        repair_costs = []

        for pipeline in pipelines:
            pipe_length = pipeline["length"]  # kilometer
            pipe_length_ft = pipeline["length"] * 3280.84  # foot

            rc = dict()
            rc["guid"] = pipeline["guid"]
            repair_cost = 0

            # read in damage ratio for break and leak
            dr_break = 0
            dr_leak = 0
            if pipeline["diameter"] > diameter:
                for dmg_ratio_row in dmg_ratio_tbl:
                    if (
                        dmg_ratio_row["Inventory Type"] == ">" + str(diameter) + " in"
                        and dmg_ratio_row["Damage State"] == "break"
                    ):
                        dr_break = float(dmg_ratio_row["Best Mean Damage Ratio"])
                    if (
                        dmg_ratio_row["Inventory Type"] == ">" + str(diameter) + " in"
                        and dmg_ratio_row["Damage State"] == "leak"
                    ):
                        dr_leak = float(dmg_ratio_row["Best Mean Damage Ratio"])
            else:
                for dmg_ratio_row in dmg_ratio_tbl:
                    if (
                        dmg_ratio_row["Inventory Type"] == "<" + str(diameter) + " in"
                        and dmg_ratio_row["Damage State"] == "break"
                    ):
                        dr_break = float(dmg_ratio_row["Best Mean Damage Ratio"])
                    if (
                        dmg_ratio_row["Inventory Type"] == "<" + str(diameter) + " in"
                        and dmg_ratio_row["Damage State"] == "leak"
                    ):
                        dr_leak = float(dmg_ratio_row["Best Mean Damage Ratio"])

            num_segment = pipe_length_ft / segment_length

            num_breaks = pipeline["breakrate"] * pipe_length
            if num_breaks > num_segment:
                repair_cost += pipeline["replacement_cost"] * dr_break
            else:
                repair_cost += (
                    pipeline["replacement_cost"] / num_segment * num_breaks * dr_break
                )

            num_leaks = pipeline["leakrate"] * pipe_length
            if num_leaks > num_segment:
                repair_cost += pipeline["replacement_cost"] * dr_leak
            else:
                repair_cost += (
                    pipeline["replacement_cost"] / num_segment * num_leaks * dr_leak
                )
            repair_cost = min(repair_cost, pipeline["replacement_cost"])

            rc["budget"] = repair_cost
            rc["repaircost"] = repair_cost

            repair_costs.append(rc)

        return repair_costs

    def get_spec(self):
        """Get specifications of the pipeline repair cost analysis.

        Returns:
            obj: A JSON object of specifications of the pipeline repair cost analysis.

        """
        return {
            "name": "pipeline-repair-cost",
            "description": "Pipeline repair cost analysis.",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "A name of the resulting dataset",
                    "type": str,
                },
                {
                    "id": "num_cpu",
                    "required": False,
                    "description": "If using parallel execution, the number of cpus to request.",
                    "type": int,
                },
                {
                    "id": "diameter",
                    "required": False,
                    "description": "Pipeline diameter cutoff assumption for different damage ratios. Default is 20 "
                    "inches",
                    "type": int,
                },
                {
                    "id": "segment_length",
                    "required": False,
                    "description": "Segment length assumption. Default is 20 feet",
                    "type": int,
                },
            ],
            "input_datasets": [
                {
                    "id": "pipeline",
                    "required": True,
                    "description": "Pipeline Inventory",
                    "type": ["ergo:buriedPipelineTopology", "ergo:pipeline"],
                },
                {
                    "id": "replacement_cost",
                    "required": True,
                    "description": "Repair cost of the node in the complete damage state (= Replacement cost)",
                    "type": ["incore:replacementCost"],
                },
                {
                    "id": "pipeline_dmg",
                    "required": True,
                    "description": "pipeline damage from PipelineDamageRepairRate Analysis",
                    "type": ["ergo:pipelineDamageVer3"],
                },
                {
                    "id": "pipeline_dmg_ratios",
                    "required": True,
                    "description": "Damage Ratios table",
                    "type": ["incore:pipelineDamageRatios"],
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "parent_type": "pipelines",
                    "description": "A csv file with repair cost for each pipeline",
                    "type": "incore:pipelineRepairCost",
                }
            ],
        }
