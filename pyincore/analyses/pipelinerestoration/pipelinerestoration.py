# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import collections
import concurrent.futures
import pandas as pd

from pyincore import BaseAnalysis, AnalysisUtil, RestorationService


class PipelineRestoration(BaseAnalysis):
    """
    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        self.restorationsvc = RestorationService(incore_client)
        super(PipelineRestoration, self).__init__(incore_client)

    def get_spec(self):
        """Get specifications of the Pipeline Restoration analysis.

        Returns:
            obj: A JSON object of specifications of the pipeline restoration analysis.

        """
        return {
            "name": "pipeline-restoration",
            "description": "calculate the restoration times for damaged pipelines",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "name of the result csv dataset",
                    "type": str,
                },
                {
                    "id": "num_cpu",
                    "required": False,
                    "description": "If using parallel execution, the number of cpus to request",
                    "type": int,
                },
                {
                    "id": "num_available_workers",
                    "required": True,
                    "description": "Number of available workers to work on the repairs",
                    "type": int,
                },
                {
                    "id": "restoration_key",
                    "required": False,
                    "description": "restoration key to use in mapping dataset",
                    "type": str,
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
                    "id": "pipeline_damage",
                    "required": True,
                    "description": "pipeline damage results with repairs",
                    "type": ["ergo:pipelineDamageVer2", "ergo:pipelineDamageVer3"],
                },
                {
                    "id": "dfr3_mapping_set",
                    "required": True,
                    "description": "DFR3 Mapping Set Object",
                    "type": ["incore:dfr3MappingSet"],
                },
            ],
            "output_datasets": [
                {
                    "id": "pipeline_restoration",
                    "description": "CSV file of pipeline restoration times",
                    "type": "incore:pipelineRestorationVer1",
                }
            ],
        }

    def run(self):
        """Executes pipeline restoration analysis."""

        pipelines_df = self.get_input_dataset("pipeline").get_dataframe_from_shapefile()

        pipeline_dmg = self.get_input_dataset("pipeline_damage").get_csv_reader()
        pipelines_dmg_df = pd.DataFrame(list(pipeline_dmg))

        damage_result = pipelines_dmg_df.merge(pipelines_df, on="guid")
        damage_result = damage_result.to_dict(orient="records")

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

        restoration_results = self.pipeline_restoration_concurrent_future(
            self.pipeline_restoration_bulk_input, num_workers, inventory_args
        )
        self.set_result_csv_data(
            "pipeline_restoration",
            restoration_results,
            name=self.get_parameter("result_name"),
        )
        return True

    def pipeline_restoration_concurrent_future(self, function_name, parallelism, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            parallelism (int): Number of workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of dictionary with restoration details

        """
        res_output = []
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=parallelism
        ) as executor:
            for res_ret in executor.map(function_name, *args):
                res_output.extend(res_ret)

        return res_output

    def pipeline_restoration_bulk_input(self, damage):
        """Run analysis for pipeline restoration calculation

        Args:
            damage (obj): An output of pipeline damage with repair rate

        Returns:
            restoration_results (list): A list of dictionary restoration times and inventory details

        """
        restoration_results = []
        num_available_workers = self.get_parameter("num_available_workers")

        restoration_key = self.get_parameter("restoration_key")
        if restoration_key is None:
            restoration_key = "Restoration ID Code"

        restoration_sets = self.restorationsvc.match_list_of_dicts(
            self.get_input_dataset("dfr3_mapping_set"), damage, restoration_key
        )

        for dmg in damage:
            res = self.restoration_time(
                dmg, num_available_workers, restoration_sets[dmg["guid"]]
            )
            restoration_results.append(res)

        return restoration_results

    @staticmethod
    def restoration_time(dmg, num_available_workers, restoration_set):
        """Calculates restoration time for a single pipeline.

        Args:
            dmg (obj): Pipeline damage analysis output for a single entry.
            num_available_workers (int): Number of available workers working on the repairs.
            restoration_set(obj): Restoration curve(s) to be be used

        Returns:
            dict: A dictionary with id/guid and restoration time, along with some inventory metadata
        """
        res_result = collections.OrderedDict()

        if "guid" in dmg.keys():
            res_result["guid"] = dmg["guid"]
        else:
            res_result["guid"] = "NA"

        res_result["repair_time"] = restoration_set.calculate_restoration_rates(
            **{
                "break_rate": float(dmg["breakrate"]),
                "leak_rate": float(dmg["leakrate"]),
                "pipe_length": dmg["length"],
                "num_workers": num_available_workers,
            }
        )["RT"]

        return res_result
