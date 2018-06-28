"""Buried Pipeline Damage Analysis

"""

from pyincore import HazardService, FragilityService, AnalysisUtil, GeoUtil
from pyincore.analyses.pipelinedamage.pipelineutil import PipelineUtil
import csv
import concurrent.futures
from itertools import repeat
import collections
import random
import math


class PipelineDamage:
    def __init__(self, client):
        # Create Hazard and Fragility service
        self.hazardsvc = HazardService(client)
        self.fragilitysvc = FragilityService(client)

    @staticmethod
    def get_output_metadata():
        output = {}
        # TODO This was ergo-hazusPipelineDamage, it doesn't seem to make sense to include the name Hazus
        output["dataType"] = "ergo:buriedPipelineDamage"
        output["format"] = "table"

        return output

    def get_damage(self, inventory_set: dict, mapping_id: str, hazard_input: str, use_liquefaction: bool, base_dataset_id: str=None, num_threads: int=0):
        """Get pipeline damage

        :param inventory_set:
        :param mapping_id:
        :param hazard_input:
        :param use_liquefaction:
        :param base_dataset_id:
        :param num_threads:
        :return:
        """

        print("get pipe damage")

        # Find hazard type and id
        hazard_input_split = hazard_input.split("/")
        hazard_type = hazard_input_split[0]
        hazard_dataset_id = hazard_input_split[1]

        parallelism = AnalysisUtil.determine_parallelism_locally(self, len(inventory_set), num_threads)

        pipes_per_process = int(len(inventory_set) / parallelism)
        inventory_args = []
        count = 0
        inventory_list = list(inventory_set)

        while count < len(inventory_list):
            inventory_args.append(inventory_list[count:count + pipes_per_process])
            count += pipes_per_process

        output = self.pipeline_damage_concurrent_future(self.pipeline_damage_analysis_bulk_input, parallelism,
                                                        inventory_args, repeat(mapping_id), repeat(self.hazardsvc),
                                                        repeat(hazard_dataset_id), repeat(hazard_type),
                                                        repeat(use_liquefaction))

        output_file_name = "dmg-results.csv"

        # Write Output to csv
        with open(output_file_name, 'w') as csv_file:
            # Write the parent ID at the top of the result data, if it is given
            if base_dataset_id is not None:
                csv_file.write(base_dataset_id + '\n')

            writer = csv.DictWriter(csv_file, dialect="unix",
                                    fieldnames=['guid', 'pipeclass', 'pgvrepairs', 'pgdrepairs', 'repairspkm',
                                                'breakrate', 'leakrate', 'failprob', 'hazardtype', 'hazardval',
                                                'numpgvrpr', 'numpgdrpr', 'numrepairs'])
            writer.writeheader()
            writer.writerows(output)

        return output_file_name

    def pipeline_damage_concurrent_future(self, function_name, parallelism, *args):
        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=parallelism) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def pipeline_damage_analysis_bulk_input(self, pipelines, mapping_id, hazardsvc, hazard_dataset_id, hazard_type,
                                            use_liquefaction):
        result = []
        fragility_sets = self.fragilitysvc.map_fragilities(mapping_id, pipelines, "Non-Retrofit Fragility ID Code")

        # TODO there is a chance the fragility key is pgd, we should either update our mappings or add support here
        if use_liquefaction:
            fragility_sets_liq = self.fragilitysvc.map_fragilities(mapping_id, pipelines, "Liquefaction-Fragility-Key")
        for pipeline in pipelines:

            if pipeline["id"] in fragility_sets.keys():
                liq_fragility_set = None
                # Check if mapping contains liquefaction fragility
                if use_liquefaction and pipeline["id"] in fragility_sets_liq:
                    liq_fragility_set = fragility_sets_liq[pipeline["id"]]

                result.append(self.pipeline_damage_analysis(pipeline, fragility_sets[pipeline["id"]], liq_fragility_set,
                                                            hazardsvc, hazard_dataset_id, hazard_type,
                                                            use_liquefaction))
        return result

    def pipeline_damage_analysis(self, pipeline, fragility_set, fragility_set_liq, hazardsvc, hazard_dataset_id,
                                 hazard_type, use_liquefaction):

        # TODO original pipeline damage does not store the pgd value, this should be added
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
            # TODO - need to modify the earthquake service to convert hazard types if direct match not found
            hazard_val = hazardsvc.get_earthquake_hazard_value(hazard_dataset_id, demand_type, demand_units,
                                                                 location.y, location.x)
            diameter = PipelineUtil.get_pipe_diameter(pipeline)
            fragility_vars = {'x': hazard_val, 'y': diameter}
            pgv_repairs = AnalysisUtil.compute_custom_limit_state_probability(fragility_set, fragility_vars)
            fragility_curve = fragility_set['fragilityCurves'][0]

            # Convert PGV repairs to SI units
            pgv_repairs = PipelineUtil.convert_result_unit(fragility_curve['description'], pgv_repairs)

            pgd_hazard = 0.0
            liquefaction_prob = 0.0
            if fragility_set_liq is not None and use_liquefaction:
                liq_fragility_curve = fragility_set_liq['fragilityCurves'][0]
                # Get PGD hazard value from hazardsvc
                # TODO add liquefaction endpoint to hazard service to return permanent ground deformation and
                # probability of liquefaction and remove the random() call
                pgd_hazard = random.uniform(0.0, 12)
                liquefaction_prob = random.uniform(0.0, 1.0)

                liq_fragility_vars = {'x': pgd_hazard, 'y' : liquefaction_prob}
                pgd_repairs = AnalysisUtil.compute_custom_limit_state_probability(fragility_set_liq,
                                                                                  liq_fragility_vars)
                pgd_repairs = PipelineUtil.convert_result_unit(liq_fragility_curve['description'], pgd_repairs)

            total_repair_rate = pgd_repairs + pgv_repairs
            break_rate = 0.2 * pgv_repairs + 0.8 * pgd_repairs
            leak_rate = 0.8 * pgv_repairs + 0.2 * pgd_repairs

            length = PipelineUtil.get_pipe_length(pipeline)

            failure_probability = 1 - math.exp(-1.0 * break_rate * length)
            num_pgd_repairs = pgd_repairs * length
            num_pgv_repairs = pgv_repairs * length
            num_repairs = num_pgd_repairs + num_pgv_repairs

        # pipeline_results['guid'] = "test"
        pipeline_results['guid'] = pipeline['properties']['guid']
        if 'pipetype' in pipeline['properties']:
            pipeline_results['pipeclass'] = pipeline['properties']['pipetype']
        elif 'pipelinesc' in pipeline['properties']:
            pipeline_results['pipeclass'] = pipeline['properties']['pipelinesc']
        else:
            pipeline_results['pipeclass'] = ""

        pipeline_results['pgvrepairs'] = pgv_repairs
        pipeline_results['pgdrepairs'] = pgd_repairs
        pipeline_results['repairspkm'] = total_repair_rate
        pipeline_results['breakrate'] = break_rate
        pipeline_results['leakrate'] = leak_rate
        pipeline_results['failprob'] = failure_probability
        pipeline_results['hazardtype'] = demand_type
        pipeline_results['hazardval'] = hazard_val
        pipeline_results['numpgvrpr'] = num_pgv_repairs
        pipeline_results['numpgdrpr'] = num_pgd_repairs
        pipeline_results['numrepairs'] = num_repairs

        return pipeline_results
