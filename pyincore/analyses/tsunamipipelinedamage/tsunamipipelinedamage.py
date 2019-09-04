# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


"""Tsunami Buried Pipeline Damage Analysis

"""

from pyincore import BaseAnalysis, HazardService, FragilityService, \
    AnalysisUtil, GeoUtil
import concurrent.futures
from itertools import repeat
import collections
import math


class TsunamiPipelineDamage(BaseAnalysis):
    """Computes pipeline damage for a hazard.

    Args:
        incore_client: Service client with authentication info

    """

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(TsunamiPipelineDamage, self).__init__(incore_client)

    def run(self):
        """Execute pipeline damage analysis """
        # Pipeline dataset
        pipeline_dataset = self.get_input_dataset(
            "pipeline").get_inventory_reader()

        # Get hazard input
        hazard_dataset_id = self.get_parameter("hazard_id")
        user_defined_cpu = 1

        if not self.get_parameter("num_cpu") is None and self.get_parameter(
                "num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        dataset_size = len(pipeline_dataset)
        num_workers = AnalysisUtil.determine_parallelism_locally(self,
                                                                 dataset_size,
                                                                 user_defined_cpu)

        avg_bulk_input_size = int(dataset_size / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(pipeline_dataset)
        while count < len(inventory_list):
            inventory_args.append(
                inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.pipeline_damage_concurrent_future(
            self.pipeline_damage_analysis_bulk_input, num_workers,
            inventory_args, repeat(hazard_dataset_id))

        self.set_result_csv_data("result", results,
                                 name=self.get_parameter("result_name"))

        return True

    def pipeline_damage_concurrent_future(self, function_name, num_workers,
                                          *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            num_workers (int): Maximum number workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """
        output = []
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=num_workers) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def pipeline_damage_analysis_bulk_input(self, pipelines, hazard_dataset_id):
        """Run pipeline damage analysis for multiple pipelines.

        Args:
            pipelines (list): multiple pipelines from pieline dataset.
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with pipeline damage values and other data/metadata.

        """
        result = []

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = "Non-Retrofit inundationDepth Fragility ID Code"

        # get fragility set
        fragility_sets = self.fragilitysvc.map_inventory(
            self.get_parameter("mapping_id"), pipelines, fragility_key)

        for pipeline in pipelines:
            if pipeline["id"] in fragility_sets.keys():
                result.append(self.pipeline_damage_analysis(pipeline,
                                                            fragility_sets[pipeline["id"]],
                                                            hazard_dataset_id))

        return result

    def pipeline_damage_analysis(self, pipeline, fragility_set, hazard_dataset_id):
        """Run pipeline damage for a single pipeline.

        Args:
            pipeline (obj): a single pipeline.
            fragility_set (obj): A JSON description of fragility assigned to the building.
            hazard_dataset_id (str): A hazard dataset to use.

        Returns:
            OrderedDict: A dictionary with pipeline damage values and other data/metadata.
        """

        pipeline_results = collections.OrderedDict()
        hazard_val = 0.0
        demand_type = ""

        if fragility_set is not None:
            demand_type = fragility_set['demandType'].lower()
            demand_units = fragility_set['demandUnits']
            location = GeoUtil.get_location(pipeline)

            # tsunami pipeline damage produce limit states instead of repair rates
            hazard_val = self.hazardsvc.get_tsunami_hazard_value(
                hazard_dataset_id,
                demand_type,
                demand_units,
                location.y, location.x)
            if hazard_val <= 0.0:
                hazard_val = 0.0

            limit_states = AnalysisUtil.compute_limit_state_probability(
                fragility_set['fragilityCurves'], hazard_val, 1.0, 0)
            dmg_intervals = AnalysisUtil.compute_damage_intervals(
                limit_states)
            pipeline_results = {**limit_states, **dmg_intervals}

        pipeline_results['guid'] = pipeline['properties']['guid']
        pipeline_results['hazardval'] = hazard_val
        pipeline_results['demandtype'] = demand_type

        return pipeline_results

    def get_spec(self):
        """Get specifications of the pipeline damage analysis.

        Returns:
            obj: A JSON object of specifications of the pipeline damage analysis.

        """
        return {
            'name': 'pipeline-damage',
            'description': 'buried pipeline damage analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                },
                {
                    'id': 'mapping_id',
                    'required': True,
                    'description': 'Fragility mapping dataset',
                    'type': str
                },
                {
                    'id': 'hazard_id',
                    'required': True,
                    'description': 'Hazard ID',
                    'type': str
                },
                {
                    'id': 'fragility_key',
                    'required': False,
                    'description': 'Fragility key to use in mapping dataset',
                    'type': str
                },
                {
                    'id': 'num_cpu',
                    'required': False,
                    'description': 'If using parallel execution, the number of cpus to request',
                    'type': int
                },
                {
                    'id': 'liquefaction_geology_dataset_id',
                    'required': False,
                    'description': 'Geology dataset id',
                    'type': str,
                }
            ],
            'input_datasets': [
                {
                    'id': 'pipeline',
                    'required': True,
                    'description': 'Pipeline Inventory',
                    'type': ['ergo:buriedPipelineTopology', 'ergo:pipeline'],
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'pipeline',
                    'type': 'ergo:pipelineDamage'
                }
            ]
        }
