# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


""" Buried Pipeline Damage Analysis with limit state calculation """

import concurrent.futures
from itertools import repeat

from pyincore import (
    BaseAnalysis,
    HazardService,
    FragilityService,
    AnalysisUtil,
    GeoUtil,
)
from pyincore.models.dfr3curve import DFR3Curve


class PipelineDamage(BaseAnalysis):
    """Computes pipeline damage for an earthquake or a tsunami).

    Args:
        incore_client: Service client with authentication info.

    """

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(PipelineDamage, self).__init__(incore_client)

    def run(self):
        """Execute pipeline damage analysis"""

        pipeline_dataset = self.get_input_dataset("pipeline").get_inventory_reader()

        # Get hazard input
        (
            hazard,
            hazard_type,
            hazard_dataset_id,
        ) = self.create_hazard_object_from_input_params()

        user_defined_cpu = 1

        if (
            not self.get_parameter("num_cpu") is None
            and self.get_parameter("num_cpu") > 0
        ):
            user_defined_cpu = self.get_parameter("num_cpu")

        dataset_size = len(pipeline_dataset)
        num_workers = AnalysisUtil.determine_parallelism_locally(
            self, dataset_size, user_defined_cpu
        )
        avg_bulk_input_size = int(dataset_size / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(pipeline_dataset)
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count : count + avg_bulk_input_size])
            count += avg_bulk_input_size

        (results, damage_results) = self.pipeline_damage_concurrent_future(
            self.pipeline_damage_analysis_bulk_input,
            num_workers,
            inventory_args,
            repeat(hazard),
            repeat(hazard_type),
            repeat(hazard_dataset_id),
        )

        self.set_result_csv_data(
            "result", results, name=self.get_parameter("result_name")
        )
        self.set_result_json_data(
            "metadata",
            damage_results,
            name=self.get_parameter("result_name") + "_additional_info",
        )
        return True

    def pipeline_damage_concurrent_future(self, function_name, num_workers, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            num_workers (int): Maximum number workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            dict: An ordered dictionaries with pipeline damage values.
            dict: An ordered dictionaries with other pipeline data/metadata.

        """
        output_ds = []
        output_dmg = []
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=num_workers
        ) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output_ds.extend(ret1)
                output_dmg.extend(ret2)

        return output_ds, output_dmg

    def pipeline_damage_analysis_bulk_input(
        self, pipelines, hazard, hazard_type, hazard_dataset_id
    ):
        """Run pipeline damage analysis for multiple pipelines.

        Args:
            pipelines (list): Multiple pipelines from pipeline dataset.
            hazard (obj): Hazard object.
            hazard_type (str): Hazard type (earthquake or tsunami).
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            dict: An ordered dictionaries with pipeline damage values.
            dict: An ordered dictionaries with other pipeline data/metadata.

        """
        # get allowed demand types for the hazard type
        allowed_demand_types = [
            item["demand_type"].lower()
            for item in self.hazardsvc.get_allowed_demands(hazard_type)
        ]

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = (
                "Non-Retrofit inundationDepth Fragility ID Code"
                if hazard_type == "tsunami"
                else "pgv"
            )
            self.set_parameter("fragility_key", fragility_key)

        # get fragility set
        fragility_sets = self.fragilitysvc.match_inventory(
            self.get_input_dataset("dfr3_mapping_set"), pipelines, fragility_key
        )

        values_payload = []
        unmapped_pipelines = []
        mapped_pipelines = []
        for pipeline in pipelines:
            # if find a match fragility for that pipeline
            if pipeline["id"] in fragility_sets.keys():
                fragility_set = fragility_sets[pipeline["id"]]
                location = GeoUtil.get_location(pipeline)
                loc = str(location.y) + "," + str(location.x)
                demands, units, _ = AnalysisUtil.get_hazard_demand_types_units(
                    pipeline, fragility_set, hazard_type, allowed_demand_types
                )
                value = {"demands": demands, "units": units, "loc": loc}
                values_payload.append(value)
                mapped_pipelines.append(pipeline)

            else:
                unmapped_pipelines.append(pipeline)

        # not needed anymore as they are already split into mapped and unmapped
        del pipelines

        if hazard_type == "earthquake" or "tsunami":
            hazard_vals = hazard.read_hazard_values(values_payload, self.hazardsvc)
        else:
            raise ValueError(
                "The provided hazard type is not supported yet by this analysis"
            )

        pipeline_results = []
        damage_results = []
        for i, pipeline in enumerate(mapped_pipelines):
            limit_states = dict()
            dmg_intervals = dict()
            pipeline_result = dict()
            fragility_set = fragility_sets[pipeline["id"]]

            # TODO: Once all fragilities are migrated to new format, we can remove this condition
            if isinstance(fragility_set.fragility_curves[0], DFR3Curve):
                # Supports multiple demand types in same fragility
                haz_vals = AnalysisUtil.update_precision_of_lists(
                    hazard_vals[i]["hazardValues"]
                )
                demand_types = hazard_vals[i]["demands"]
                demand_units = hazard_vals[i]["units"]

                # construct hazard_value dictionary {"demand_type":"hazard_value", ...}
                hval_dict = dict()
                for j, d in enumerate(fragility_set.demand_types):
                    hval_dict[d] = haz_vals[j]

                if not AnalysisUtil.do_hazard_values_have_errors(
                    hazard_vals[i]["hazardValues"]
                ):
                    pipeline_args = (
                        fragility_set.construct_expression_args_from_inventory(pipeline)
                    )
                    limit_states = fragility_set.calculate_limit_state(
                        hval_dict, inventory_type="pipeline", **pipeline_args
                    )
                    dmg_intervals = fragility_set.calculate_damage_interval(
                        limit_states, hazard_type=hazard_type, inventory_type="pipeline"
                    )

            else:
                raise ValueError(
                    "One of the fragilities is in deprecated format. This should not happen. If you are "
                    "seeing this please report the issue."
                )

            pipeline_result["guid"] = pipeline["properties"]["guid"]
            pipeline_result.update(limit_states)
            pipeline_result.update(dmg_intervals)
            pipeline_result[
                "haz_expose"
            ] = AnalysisUtil.get_exposure_from_hazard_values(haz_vals, hazard_type)
            damage_result = dict()
            damage_result["guid"] = pipeline["properties"]["guid"]
            damage_result["fragility_id"] = fragility_set.id
            damage_result["demandtypes"] = demand_types
            damage_result["demandunits"] = demand_units
            damage_result["hazardtype"] = hazard_type
            damage_result["hazardval"] = haz_vals

            pipeline_results.append(pipeline_result)
            damage_results.append(damage_result)

        # for pipeline does not have matching fragility curves, default to None
        for pipeline in unmapped_pipelines:
            pipeline_result = dict()
            damage_result = dict()
            pipeline_result["guid"] = pipeline["properties"]["guid"]
            damage_result["guid"] = pipeline["properties"]["guid"]
            damage_result["fragility_id"] = None
            damage_result["demandtypes"] = None
            damage_result["demandunits"] = None
            damage_result["hazardtype"] = None
            damage_result["hazardvals"] = None

            pipeline_results.append(pipeline_result)
            damage_results.append(damage_result)

        return pipeline_results, damage_results

    def get_spec(self):
        """Get specifications of the pipeline damage analysis.

        Returns:
            obj: A JSON object of specifications of the pipeline damage analysis.

        """
        return {
            "name": "pipeline-damage",
            "description": "Buried pipeline damage analysis",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "Result dataset name",
                    "type": str,
                },
                {
                    "id": "hazard_type",
                    "required": False,
                    "description": "Hazard Type",
                    "type": str,
                },
                {
                    "id": "hazard_id",
                    "required": False,
                    "description": "Hazard ID",
                    "type": str,
                },
                {
                    "id": "fragility_key",
                    "required": False,
                    "description": "Fragility key to use in mapping dataset",
                    "type": str,
                },
                {
                    "id": "num_cpu",
                    "required": False,
                    "description": "If using parallel execution, the number of cpus to request",
                    "type": int,
                },
                {
                    "id": "liquefaction_geology_dataset_id",
                    "required": False,
                    "description": "Geology dataset id",
                    "type": str,
                },
            ],
            "input_hazards": [
                {
                    "id": "hazard",
                    "required": False,
                    "description": "Hazard object",
                    "type": ["earthquake", "tsunami"],
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
                    "id": "dfr3_mapping_set",
                    "required": True,
                    "description": "DFR3 Mapping Set Object",
                    "type": ["incore:dfr3MappingSet"],
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "parent_type": "pipeline",
                    "description": "CSV file of damage states for pipeline damage",
                    "type": "incore:pipelineDamageVer3",
                },
                {
                    "id": "metadata",
                    "parent_type": "pipeline",
                    "description": "Json file with information about applied hazard value and fragility",
                    "type": "incore:pipelineDamageSupplement",
                },
            ],
        }
