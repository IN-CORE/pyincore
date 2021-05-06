# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


"""Buried Pipeline Damage Analysis with Repair Rate Calculation

"""

import collections
import concurrent.futures
import math
from itertools import repeat

from pyincore import BaseAnalysis, HazardService, FragilityService, \
    AnalysisUtil, GeoUtil
from pyincore.analyses.pipelinedamagerepairrate.pipelineutil import \
    PipelineUtil


class PipelineDamageRepairRate(BaseAnalysis):
    """Computes pipeline damage for a hazard.

    Args:
        incore_client: Service client with authentication info

    """

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(PipelineDamageRepairRate, self).__init__(incore_client)

    def run(self):
        """Execute pipeline damage analysis """
        # Pipeline dataset
        pipeline_dataset = self.get_input_dataset(
            "pipeline").get_inventory_reader()

        # Get hazard type
        hazard_type = self.get_parameter("hazard_type")

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

        (ds_results, damage_results) = self.pipeline_damage_concurrent_future(
            self.pipeline_damage_analysis_bulk_input, num_workers,
            inventory_args, repeat(hazard_type), repeat(hazard_dataset_id))

        self.set_result_csv_data("result", ds_results, name=self.get_parameter("result_name"))
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
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """
        output_ds = []
        output_dmg = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output_ds.extend(ret1)
                output_dmg.extend(ret2)

        return output_ds, output_dmg

    def pipeline_damage_analysis_bulk_input(self, pipelines, hazard_type,
                                            hazard_dataset_id):
        """Run pipeline damage analysis for multiple pipelines.

        Args:
            pipelines (list): multiple pipelines from pieline dataset.
            hazard_type (str): Hazard type
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            ds_results (list): A list of ordered dictionaries with pipeline damage values and other data/metadata.
            damage_results (list): A list of ordered dictionaries with pipeline damage metadata.
        """

        ds_results = []
        damage_results = []

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = PipelineUtil.DEFAULT_TSU_FRAGILITY_KEY if hazard_type == 'tsunami' else \
                PipelineUtil.DEFAULT_EQ_FRAGILITY_KEY
            self.set_parameter("fragility_key", fragility_key)

        # get fragility set
        fragility_sets = self.fragilitysvc.match_inventory(
            self.get_input_dataset("dfr3_mapping_set"), pipelines, fragility_key)

        # Get Liquefaction Fragility Key
        liquefaction_fragility_key = self.get_parameter(
            "liquefaction_fragility_key")
        if hazard_type == "earthquake" and liquefaction_fragility_key is None:
            liquefaction_fragility_key = PipelineUtil.LIQ_FRAGILITY_KEY

        # Liquefaction
        use_liquefaction = False
        if hazard_type == "earthquake" and self.get_parameter(
                "use_liquefaction") is not None:
            use_liquefaction = self.get_parameter("use_liquefaction")

        # Get geology dataset id
        geology_dataset_id = self.get_parameter(
            "liquefaction_geology_dataset_id")
        if geology_dataset_id is not None:
            fragility_sets_liq = self.fragilitysvc.match_inventory(
                self.get_input_dataset("dfr3_mapping_set"), pipelines,
                liquefaction_fragility_key)

        for pipeline in pipelines:
            if pipeline["id"] in fragility_sets.keys():
                liq_fragility_set = None
                # Check if mapping contains liquefaction fragility
                if geology_dataset_id is not None and \
                        fragility_sets_liq is not None and \
                        pipeline["id"] in fragility_sets_liq:
                    liq_fragility_set = fragility_sets_liq[pipeline["id"]]

                (ds_result, damage_result) = self.pipeline_damage_analysis(pipeline, hazard_type,
                                                                           fragility_sets[pipeline["id"]],
                                                                           liq_fragility_set, hazard_dataset_id,
                                                                           geology_dataset_id, use_liquefaction)
                ds_results.append(ds_result)
                damage_results.append(damage_result)

        return ds_results, damage_results

    def pipeline_damage_analysis(self, pipeline, hazard_type, fragility_set,
                                 fragility_set_liq, hazard_dataset_id,
                                 geology_dataset_id, use_liquefaction):
        """Run pipeline damage for a single pipeline.

        Args:
            pipeline (obj): a single pipeline.
            hazard_type (str): hazard type.
            fragility_set (obj): A JSON description of fragility assigned to the building.
            fragility_set_liq (obj): A JSON description of fragility assigned to the building with liqufaction.
            hazard_dataset_id (str): A hazard dataset to use.
            geology_dataset_id (str): A dataset id for geology dataset for liqufaction.
            use_liquefaction (bool): Liquefaction. True for using liquefaction information to modify the damage,
                False otherwise.

        Returns:
            OrderedDict: A dictionary with pipeline damage values and other data/metadata.
        """
        ds_result = {}
        damage_result = {}
        ds_result['guid'] = pipeline['properties']['guid']
        damage_result['guid'] = pipeline['properties']['guid']

        pgv_repairs = 0.0
        pgd_repairs = 0.0
        liq_hazard_type = None
        liq_hazard_val = None
        liquefaction_prob = None

        if fragility_set is not None:
            demand_type = fragility_set.demand_types[0].lower()
            demand_unit = fragility_set.demand_units[0]
            location = GeoUtil.get_location(pipeline)
            point = str(location.y) + "," + str(location.x)

            if hazard_type == 'earthquake':
                hazard_resp = self.hazardsvc.get_earthquake_hazard_values(
                    hazard_dataset_id, demand_type, demand_unit, [point])
            elif hazard_type == 'tsunami':
                hazard_resp = self.hazardsvc.get_tsunami_hazard_values(
                    hazard_dataset_id, demand_type, demand_unit, [point])
            elif hazard_type == 'tornado':
                hazard_resp = self.hazardsvc.get_tornado_hazard_values(
                    hazard_dataset_id, demand_unit, [point])
            elif hazard_type == 'hurricane':
                hazard_resp = self.hazardsvc.get_hurricanewf_values(
                    hazard_dataset_id, demand_type, demand_unit, [point])
            else:
                raise ValueError(
                    "Hazard type are not currently supported.")

            hazard_val = hazard_resp[0]['hazardValue']
            if hazard_val <= 0.0:
                hazard_val = 0.0

            diameter = PipelineUtil.get_pipe_diameter(pipeline)
            fragility_vars = {'x': hazard_val, 'y': diameter}
            fragility_curve = fragility_set.fragility_curves[0]

            # TODO: here assume that custom fragility set only has one limit state
            pgv_repairs = fragility_set.calculate_custom_limit_state(fragility_vars)['failure']

            # Convert PGV repairs to SI units
            pgv_repairs = PipelineUtil.convert_result_unit(
                fragility_curve.description, pgv_repairs)

            if use_liquefaction is True and fragility_set_liq is not None and geology_dataset_id is not None:
                liq_fragility_curve = fragility_set_liq.fragility_curves[0]
                liq_hazard_type = fragility_set_liq.demand_types[0]
                pgd_demand_unit = fragility_set_liq.demand_units[0]

                # Get PGD hazard value from hazard service
                location_str = str(location.y) + "," + str(location.x)
                liquefaction = self.hazardsvc.get_liquefaction_values(
                    hazard_dataset_id, geology_dataset_id,
                    pgd_demand_unit, [location_str])
                liq_hazard_val = liquefaction[0]['pgd']
                liquefaction_prob = liquefaction[0]['liqProbability']

                liq_fragility_vars = {'x': liq_hazard_val,
                                      'y': liquefaction_prob}
                pgd_repairs = liq_fragility_curve.compute_custom_limit_state_probability(liq_fragility_vars)
                # Convert PGD repairs to SI units
                pgd_repairs = PipelineUtil.convert_result_unit(
                    liq_fragility_curve.description, pgd_repairs)

            total_repair_rate = pgd_repairs + pgv_repairs
            break_rate = 0.2 * pgv_repairs + 0.8 * pgd_repairs
            leak_rate = 0.8 * pgv_repairs + 0.2 * pgd_repairs

            length = PipelineUtil.get_pipe_length(pipeline)

            failure_probability = 1 - math.exp(-1.0 * break_rate * length)
            num_pgd_repairs = pgd_repairs * length
            num_pgv_repairs = pgv_repairs * length
            num_repairs = num_pgd_repairs + num_pgv_repairs

            if 'pipetype' in pipeline['properties']:
                damage_result['pipeclass'] = pipeline['properties'][
                    'pipetype']
            elif 'pipelinesc' in pipeline['properties']:
                damage_result['pipeclass'] = pipeline['properties'][
                    'pipelinesc']
            else:
                damage_result['pipeclass'] = ""

            ds_result['pgvrepairs'] = pgv_repairs
            ds_result['pgdrepairs'] = pgd_repairs
            ds_result['repairspkm'] = total_repair_rate
            ds_result['breakrate'] = break_rate
            ds_result['leakrate'] = leak_rate
            ds_result['failprob'] = failure_probability
            ds_result['numpgvrpr'] = num_pgv_repairs
            ds_result['numpgdrpr'] = num_pgd_repairs
            ds_result['numrepairs'] = num_repairs
            ds_result['liqprobability'] = liquefaction_prob

            damage_result['fragility_id'] = fragility_set.id
            damage_result['demandtypes'] = demand_type
            damage_result['demandunits'] = demand_unit
            damage_result['hazardtype'] = hazard_type
            damage_result['hazardval'] = hazard_val

            # if there is liquefaction presented
            if use_liquefaction is True and fragility_set_liq is not None and geology_dataset_id is not None:
                damage_result['liq_fragility_id'] = fragility_set_liq.id
            else:
                damage_result['liq_fragility_id'] = None
            damage_result['liqhaztype'] = liq_hazard_type
            damage_result['liqhazval'] = liq_hazard_val

        else:
            damage_result['fragility_id'] = None
            damage_result['liq_fragility_id'] = None
            damage_result['demandtypes'] = None
            damage_result['demandunits'] = None
            damage_result['hazardtype'] = None
            damage_result['hazardval'] = None
            damage_result['liqhaztype'] = None
            damage_result['liqhazval'] = None

        return ds_result, damage_result

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
                    'id': 'hazard_type',
                    'required': True,
                    'description': 'Hazard Type (e.g. earthquake)',
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
                    'id': 'use_liquefaction',
                    'required': False,
                    'description': 'Use liquefaction',
                    'type': bool
                },
                {
                    'id': 'liquefaction_fragility_key',
                    'required': False,
                    'description': 'Fragility key to use in liquefaction mapping dataset',
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
                    'type': 'ergo:pipelineDamageVer2'
                },
                {
                    'id': 'metadata',
                    'parent_type': 'pipeline',
                    'description': 'additional metadata in json file about applied hazard value and '
                                   'fragility',
                    'type': 'incore:pipelineDamageMetadata'
                }
            ]
        }
