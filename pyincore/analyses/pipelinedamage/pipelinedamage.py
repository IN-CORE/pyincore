# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


"""Buried Pipeline Damage Analysis

"""

from pyincore import BaseAnalysis, HazardService, FragilityService, \
    AnalysisUtil, GeoUtil
from pyincore.analyses.pipelinedamage.pipelineutil import PipelineUtil
import concurrent.futures
from itertools import repeat
import collections
import math


class PipelineDamage(BaseAnalysis):
    """Computes pipeline damage for a hazard.

    Args:
        incore_client: Service client with authentication info

    """

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(PipelineDamage, self).__init__(incore_client)

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

        results = self.pipeline_damage_concurrent_future(
            self.pipeline_damage_analysis_bulk_input, num_workers,
            inventory_args, repeat(hazard_type), repeat(hazard_dataset_id))

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

    def pipeline_damage_analysis_bulk_input(self, pipelines, hazard_type, hazard_dataset_id):
        """Run pipeline damage analysis for multiple pipelines.

        Args:
            pipelines (list): multiple pipelines from pieline dataset.
            hazard_type (str): Hazard type
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with pipeline damage values and other data/metadata.

        """
        result = []

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            if hazard_type == "earthquake":
                fragility_key = PipelineUtil.DEFAULT_EQ_FRAGILITY_KEY
            elif hazard_type == "tsunami":
                fragility_key = PipelineUtil.DEFAULT_TSU_FRAGILITY_KEY

        # get fragility set
        fragility_sets = self.fragilitysvc.map_fragilities(
            self.get_parameter("mapping_id"), pipelines, fragility_key)

        # Get geology dataset id
        geology_dataset_id = self.get_parameter("liquefaction_geology_dataset_id")

        # Get Liquefaction Fragility Key
        liquefaction_fragility_key = self.get_parameter(
            "liquefaction_fragility_key")
        if liquefaction_fragility_key is None:
            liquefaction_fragility_key = PipelineUtil.LIQ_FRAGILITY_KEY

        # Liquefaction
        use_liquefaction = False
        if self.get_parameter("use_liquefaction") is not None:
            use_liquefaction = self.get_parameter("use_liquefaction")

        if geology_dataset_id is not None:
            fragility_sets_liq = self.fragilitysvc.map_fragilities(
                self.get_parameter("mapping_id"), pipelines,
                liquefaction_fragility_key)

        if hazard_type == "earthquake":
            for pipeline in pipelines:
                if pipeline["id"] in fragility_sets.keys():
                    liq_fragility_set = None
                    # Check if mapping contains liquefaction fragility
                    if geology_dataset_id is not None and \
                            fragility_sets_liq is not None and \
                            pipeline["id"] in fragility_sets_liq:
                        liq_fragility_set = fragility_sets_liq[pipeline["id"]]

                    result.append(self.pipeline_damage_analysis(pipeline,
                                                                hazard_type,
                                                                fragility_sets[
                                                                    pipeline[
                                                                        "id"]],
                                                                liq_fragility_set,
                                                                hazard_dataset_id,
                                                                geology_dataset_id,
                                                                use_liquefaction))
        elif hazard_type == "tsunami":
            for pipeline in pipelines:
                if pipeline["id"] in fragility_sets.keys():
                    liq_fragility_set = None
                    geology_dataset_id = ""
                    use_liquefaction = False
                    result.append(self.pipeline_damage_analysis(pipeline,
                                                                hazard_type,
                                                                fragility_sets[
                                                                    pipeline[
                                                                        "id"]],
                                                                liq_fragility_set,
                                                                hazard_dataset_id,
                                                                geology_dataset_id,
                                                                use_liquefaction))

        return result

    def pipeline_damage_analysis(self, pipeline, hazard_type, fragility_set,
                                 fragility_set_liq, hazard_dataset_id,
                                 geology_dataset_id, use_liquefaction):
        """Run pipeline damage for a single pipeline.

        Args:
            pipeline (obj): a single pipeline.
            fragility_set (obj): A JSON description of fragility assigned to the building.
            fragility_set_liq (obj): A JSON description of fragility assigned to the building with liqufaction.
            hazard_dataset_id (str): A hazard dataset to use.
            geology_dataset_id (str): A dataset id for geology dataset for liqufaction.
            use_liquefaction (bool): Liquefaction. True for using liquefaction information to modify the damage,
                False otherwise.

        Returns:
            OrderedDict: A dictionary with pipeline damage values and other data/metadata.
        """

        pipeline_results = collections.OrderedDict()
        pgv_repairs = 0.0
        pgd_repairs = 0.0
        total_repair_rate = 0.0
        break_rate = 0.0
        leak_rate = 0.0
        failure_probability = 0.0
        num_pgd_repairs = 0.0
        num_pgv_repairs = 0.0
        num_repairs = 0.0
        demand_type = None
        hazard_val = 0.0

        if fragility_set is not None:
            demand_type = fragility_set['demandType'].lower()
            demand_units = fragility_set['demandUnits']
            location = GeoUtil.get_location(pipeline)

            # Get PGV hazard from hazardsvc
            if hazard_type == 'earthquake':
                hazard_val = self.hazardsvc.get_earthquake_hazard_value(
                    hazard_dataset_id, demand_type, demand_units,
                    location.y, location.x)
            elif hazard_type == 'tsunami':
                hazard_val = self.hazardsvc.get_tsunami_hazard_value(hazard_dataset_id,
                                                                      demand_type,
                                                                      demand_units,
                                                                      location.y, location.x)

                # Sometimes the geotiffs give large negative values for out of bounds instead of 0
                if hazard_val <= 0.0:
                    hazard_val = 0.0

            # TODO: throw error if other hazard type

            diameter = PipelineUtil.get_pipe_diameter(pipeline)
            fragility_vars = {'x': hazard_val, 'y': diameter}
            pgv_repairs = AnalysisUtil.compute_custom_limit_state_probability(
                fragility_set, fragility_vars)
            fragility_curve = fragility_set['fragilityCurves'][0]

            # Convert PGV repairs to SI units
            pgv_repairs = PipelineUtil.convert_result_unit(
                fragility_curve['description'], pgv_repairs)

            liq_hazard_type = ""
            liq_hazard_val = 0.0
            liquefaction_prob = 0.0

            if use_liquefaction is True and fragility_set_liq is not None and geology_dataset_id is not None:
                liq_fragility_curve = fragility_set_liq['fragilityCurves'][0]
                liq_hazard_type = fragility_set_liq['demandType']
                pgd_demand_units = fragility_set_liq['demandUnits']

                # Get PGD hazard value from hazard service
                location_str = str(location.y) + "," + str(location.x)
                liquefaction = self.hazardsvc.get_liquefaction_values(
                    hazard_dataset_id, geology_dataset_id,
                    pgd_demand_units, [location_str])
                liq_hazard_val = liquefaction[0]['pgd']
                liquefaction_prob = liquefaction[0]['liqProbability']

                liq_fragility_vars = {'x': liq_hazard_val,
                                      'y': liquefaction_prob}
                pgd_repairs = AnalysisUtil.compute_custom_limit_state_probability(
                    fragility_set_liq,
                    liq_fragility_vars)
                # Convert PGD repairs to SI units
                pgd_repairs = PipelineUtil.convert_result_unit(
                    liq_fragility_curve['description'], pgd_repairs)

            total_repair_rate = pgd_repairs + pgv_repairs
            break_rate = 0.2 * pgv_repairs + 0.8 * pgd_repairs
            leak_rate = 0.8 * pgv_repairs + 0.2 * pgd_repairs

            length = PipelineUtil.get_pipe_length(pipeline)

            failure_probability = 1 - math.exp(-1.0 * break_rate * length)
            num_pgd_repairs = pgd_repairs * length
            num_pgv_repairs = pgv_repairs * length
            num_repairs = num_pgd_repairs + num_pgv_repairs

        pipeline_results['guid'] = pipeline['properties']['guid']
        if 'pipetype' in pipeline['properties']:
            pipeline_results['pipeclass'] = pipeline['properties']['pipetype']
        elif 'pipelinesc' in pipeline['properties']:
            pipeline_results['pipeclass'] = pipeline['properties'][
                'pipelinesc']
        else:
            pipeline_results['pipeclass'] = ""

        # TODO consider converting PGD/PGV values to SI units
        pipeline_results['pgvrepairs'] = pgv_repairs
        pipeline_results['pgdrepairs'] = pgd_repairs
        pipeline_results['repairspkm'] = total_repair_rate
        pipeline_results['breakrate'] = break_rate
        pipeline_results['leakrate'] = leak_rate
        pipeline_results['failprob'] = failure_probability
        pipeline_results['hazardtype'] = demand_type
        pipeline_results['hazardval'] = hazard_val
        pipeline_results['liqhaztype'] = liq_hazard_type
        pipeline_results['liqhazval'] = liq_hazard_val
        pipeline_results['liqprobability'] = liquefaction_prob
        pipeline_results['numpgvrpr'] = num_pgv_repairs
        pipeline_results['numpgdrpr'] = num_pgd_repairs
        pipeline_results['numrepairs'] = num_repairs

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

if __name__ == "__main__":

    from pyincore.client import InsecureIncoreClient

    client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "incrtest")

    # Create pipeline damage
    pipeline_dmg = PipelineDamage(client)
    pipeline_dmg.load_remote_input_dataset("pipeline", "5d2666b5b9219c3c5595ee65")
    pipeline_dmg.set_parameter("result_name", "seaside_tsunami_pipeline_result")
    pipeline_dmg.set_parameter("mapping_id", "5d320a87b9219c6d66398b45")
    pipeline_dmg.set_parameter("hazard_type", "tsunami")
    pipeline_dmg.set_parameter("hazard_id", "5bc9ea68f7b08533c7e610dd")
    pipeline_dmg.set_parameter("use_liquefaction", False)
    pipeline_dmg.set_parameter("fragility_key", "Non-Retrofit inundationDepth Fragility ID Code")
    pipeline_dmg.set_parameter("num_cpu", 4)

    # Run bridge damage analysis
    result = pipeline_dmg.run_analysis()