# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


""" Buried Pipeline Damage Analysis with limit state calculation """

import concurrent.futures
from itertools import repeat

from pyincore import BaseAnalysis, HazardService, FragilityService, \
    FragilityCurveSet, AnalysisUtil, GeoUtil


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
        """Execute pipeline damage analysis """

        pipeline_dataset = self.get_input_dataset("pipeline").get_inventory_reader()

        # Get hazard input
        hazard_type = self.get_parameter("hazard_type")
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

        (results, damage_results) = self.pipeline_damage_concurrent_future(
            self.pipeline_damage_analysis_bulk_input, num_workers,
            inventory_args, repeat(hazard_type), repeat(hazard_dataset_id))

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"))
        self.set_result_json_data("metadata",
                                  damage_results,
                                  name=self.get_parameter("result_name") + "_additional_info")
        return True

    def pipeline_damage_concurrent_future(self, function_name, num_workers,
                                          *args):
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
                max_workers=num_workers) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output_ds.extend(ret1)
                output_dmg.extend(ret2)

        return output_ds, output_dmg

    def pipeline_damage_analysis_bulk_input(self, pipelines, hazard_type,
                                            hazard_dataset_id):
        """Run pipeline damage analysis for multiple pipelines.

        Args:
            pipelines (list): Multiple pipelines from pipeline dataset.
            hazard_type (str): Hazard type (earthquake or tsunami).
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            dict: An ordered dictionaries with pipeline damage values.
            dict: An ordered dictionaries with other pipeline data/metadata.

        """
        pipeline_results = []
        damage_results = []

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = "Non-Retrofit inundationDepth Fragility ID Code" if hazard_type == 'tsunami' else "pgv"
            self.set_parameter("fragility_key", fragility_key)

        # get fragility set
        fragility_sets = self.fragilitysvc.match_inventory(
            self.get_input_dataset("dfr3_mapping_set"), pipelines, fragility_key)

        for pipeline in pipelines:
            fragility_set = None
            if pipeline["id"] in fragility_sets.keys():
                fragility_set = fragility_sets[pipeline["id"]]

            (pipeline_result, damage_result) = self.pipeline_damage_analysis(pipeline, hazard_type,
                                                        fragility_set, hazard_dataset_id)
            pipeline_results.append(pipeline_result)
            damage_results.append(damage_result)

        return pipeline_results, damage_results

    def pipeline_damage_analysis(self, pipeline, hazard_type, fragility_set, hazard_dataset_id):
        """Run pipeline damage for a single pipeline.

        Args:
            pipeline (obj): a single pipeline.
            hazard_type (str): hazard type (earthquake or tsunami)
            fragility_set (obj): A JSON description of fragility assigned to the pipeline.
            hazard_dataset_id (str): A hazard dataset to use.

        Returns:
            dict: An ordered dictionaries with pipeline damage values.
            dict: An ordered dictionaries with other pipeline data/metadata.
        """
        hazard_val = 0.0
        demand_type = None
        demand_unit = None
        fragility_id = None
        limit_states = FragilityCurveSet._initialize_limit_states("pipeline")
        dmg_intervals = dict()
        damage_result = dict()

        if fragility_set is not None:
            fragility_id = fragility_set.id
            demand_type = fragility_set.demand_types[0].lower()
            demand_unit = fragility_set.demand_units[0]
            location = GeoUtil.get_location(pipeline)
            point = str(location.y) + "," + str(location.x)

            # tsunami pipeline damage produce limit states
            if hazard_type == 'earthquake':
                hazard_resp = self.hazardsvc.get_earthquake_hazard_values(
                    hazard_dataset_id, demand_type, demand_unit, [point])
            elif hazard_type == 'tsunami':
                hazard_resp = self.hazardsvc.get_tsunami_hazard_values(
                    hazard_dataset_id, demand_type, demand_unit, [point])
            else:
                raise ValueError(
                    "Hazard type are not currently supported.")

            hazard_val = hazard_resp[0]['hazardValue']
            if hazard_val <= 0.0:
                hazard_val = 0.0

            limit_states = fragility_set.calculate_limit_state_w_conversion(hazard_val,
                                                                            inventory_type="pipeline")
            dmg_intervals = fragility_set.calculate_damage_interval(limit_states,
                                                                    hazard_type="earthquake",
                                                                    inventory_type="pipeline")

        result = {'guid': pipeline['properties']['guid'], **limit_states, **dmg_intervals}
        damage_result['guid'] = pipeline['properties']['guid']
        damage_result['fragility_id'] = fragility_id
        damage_result['demandtypes'] = demand_type
        damage_result['demandunits'] = demand_unit
        damage_result['hazardtype'] = hazard_type
        damage_result['hazardval'] = hazard_val

        return result, damage_result

    def get_spec(self):
        """Get specifications of the pipeline damage analysis.

        Returns:
            obj: A JSON object of specifications of the pipeline damage analysis.

        """
        return {
            'name': 'pipeline-damage',
            'description': 'Buried pipeline damage analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'Result dataset name',
                    'type': str
                },
                {
                    'id': 'hazard_type',
                    'required': True,
                    'description': 'Hazard Type',
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
                },
                {
                    'id': 'dfr3_mapping_set',
                    'required': True,
                    'description': 'DFR3 Mapping Set Object',
                    'type': ['incore:dfr3MappingSet'],
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'pipeline',
                    'description': 'CSV file of damage states for pipeline damage',
                    'type': 'incore:pipelineDamageVer2'
                },
                {
                    'id': 'metadata',
                    'parent_type': 'pipeline',
                    'description': 'Json file with information about applied hazard value and fragility',
                    'type': 'incore:pipelineDamageMetadata'
                }
            ]
        }

