# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


"""Buried Pipeline Damage Analysis

"""

from pyincore import HazardService, FragilityService, AnalysisUtil, GeoUtil
from pyincore.analyses.pipelinedamage.pipelineutil import PipelineUtil
import csv
import concurrent.futures
from itertools import repeat
import collections
import math


class PipelineDamage:
    def __init__(self, client):
        # Create Hazard and Fragility service
        self.hazardsvc = HazardService(client)
        self.fragilitysvc = FragilityService(client)

    @staticmethod
    def get_output_metadata():
        output = dict()
        # TODO This was ergo-hazusPipelineDamage, it doesn't seem to make sense to include the name Hazus
        output["dataType"] = "ergo:buriedPipelineDamage"
        output["format"] = "table"

        return output

    def get_damage(self, inventory_set: dict, mapping_id: str, hazard_input: str, geology_dataset_id: str=None,
                   num_threads: int=0):
        """Get pipeline damage

        :param inventory_set:
        :param mapping_id:
        :param hazard_input:
        :param geology_dataset_id:
        :param num_threads:
        :return:
        """

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
                                                        repeat(hazard_dataset_id), repeat(geology_dataset_id))

        # TODO output filename could be a user input
        output_file_name = "dmg-results.csv"

        # Write Output to csv
        with open(output_file_name, 'w') as csv_file:
            # Write the parent ID at the top of the result data, if it is given
            writer = csv.DictWriter(csv_file, dialect="unix",
                                    fieldnames=['guid', 'pipeclass', 'pgvrepairs', 'pgdrepairs', 'repairspkm',
                                                'breakrate', 'leakrate', 'failprob', 'hazardtype', 'hazardval',
                                                'liqhaztype', 'liqhazval', 'numpgvrpr', 'numpgdrpr', 'numrepairs'])
            writer.writeheader()
            writer.writerows(output)

        return output_file_name

    def pipeline_damage_concurrent_future(self, function_name, parallelism, *args):
        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=parallelism) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def pipeline_damage_analysis_bulk_input(self, pipelines, mapping_id, hazardsvc, hazard_dataset_id,
                                            geology_dataset_id):
        result = []
        fragility_sets = self.fragilitysvc.map_fragilities(mapping_id, pipelines, "Non-Retrofit Fragility ID Code")

        # TODO there is a chance the fragility key is pgd, we should either update our mappings or add support here
        if geology_dataset_id is not None:
            fragility_sets_liq = self.fragilitysvc.map_fragilities(mapping_id, pipelines, "Liquefaction-Fragility-Key")
        for pipeline in pipelines:

            if pipeline["id"] in fragility_sets.keys():
                liq_fragility_set = None
                # Check if mapping contains liquefaction fragility
                if geology_dataset_id is not None and pipeline["id"] in fragility_sets_liq:
                    liq_fragility_set = fragility_sets_liq[pipeline["id"]]

                result.append(self.pipeline_damage_analysis(pipeline, fragility_sets[pipeline["id"]], liq_fragility_set,
                                                            hazardsvc, hazard_dataset_id, geology_dataset_id))
        return result

    def pipeline_damage_analysis(self, pipeline, fragility_set, fragility_set_liq, hazardsvc, hazard_dataset_id,
                                 geology_dataset_id):

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
            hazard_val = hazardsvc.get_earthquake_hazard_value(hazard_dataset_id, demand_type, demand_units, location.y,
                                                               location.x)
            diameter = PipelineUtil.get_pipe_diameter(pipeline)
            fragility_vars = {'x': hazard_val, 'y': diameter}
            pgv_repairs = AnalysisUtil.compute_custom_limit_state_probability(fragility_set, fragility_vars)
            fragility_curve = fragility_set['fragilityCurves'][0]

            # Convert PGV repairs to SI units
            pgv_repairs = PipelineUtil.convert_result_unit(fragility_curve['description'], pgv_repairs)

            liq_hazard_type = ""
            liq_hazard_val = 0.0
            liquefaction_prob = 0.0

            if fragility_set_liq is not None and geology_dataset_id is not None:
                liq_fragility_curve = fragility_set_liq['fragilityCurves'][0]
                liq_hazard_type = fragility_set_liq['demandType']
                pgd_demand_units = fragility_set_liq['demandUnits']

                # Get PGD hazard value from hazard service
                point = str(location.y) + "," + str(location.x)
                liquefaction = hazardsvc.get_liquefaction_values(hazard_dataset_id, geology_dataset_id, pgd_demand_units
                                                                 , [point])
                liq_hazard_val = liquefaction[0]['pgd']
                liquefaction_prob = liquefaction[0]['liqProbability']

                liq_fragility_vars = {'x': liq_hazard_val, 'y' : liquefaction_prob}
                pgd_repairs = AnalysisUtil.compute_custom_limit_state_probability(fragility_set_liq,
                                                                                  liq_fragility_vars)
                # Convert PGD repairs to SI units
                pgd_repairs = PipelineUtil.convert_result_unit(liq_fragility_curve['description'], pgd_repairs)

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
            pipeline_results['pipeclass'] = pipeline['properties']['pipelinesc']
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
        pipeline_results['numpgvrpr'] = num_pgv_repairs
        pipeline_results['numpgdrpr'] = num_pgd_repairs
        pipeline_results['numrepairs'] = num_repairs

        return pipeline_results
