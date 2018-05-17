"""Buried Pipeline Damage Analysis

"""

from pyincore import HazardService, FragilityService, AnalysisUtil
import csv
import concurrent.futures
from itertools import repeat
import collections


class PipelineDamage:
    def __init__(self, client):
        print("initialize pipeline damage")

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

    def get_damage(self, inventory_set: dict, mapping_id: str, hazard_input: str, base_dataset_id: str=None, num_threads: int=0):
        """Get pipeline damage

        :param inventory_set:
        :param mapping_id:
        :param hazard_input:
        :param base_dataset_id:
        :param num_threads:
        :return:
        """

        print("get pipe damage")

        # Find hazard type and id
        hazard_input_split = hazard_input.split("/")
        hazard_type = hazard_input_split[0]
        hazard_dataset_id = hazard_input_split[1]

        pipes = range(0, len(inventory_set))

        # for id in pipes:
        #     print(inventory_set[id])

        parallelism = AnalysisUtil.determine_parallelism_locally(self, len(inventory_set), num_threads)

        print(parallelism)
        pipes_per_process = int(len(inventory_set) / parallelism)
        inventory_args = []
        count = 0
        inventory_list = list(inventory_set)

        while count < len(inventory_list):
            inventory_args.append(inventory_list[count:count + pipes_per_process])
            count += pipes_per_process

        output = self.pipeline_damage_concurrent_future(self.pipeline_damage_analysis_bulk_input, parallelism,
                                                        inventory_args, repeat(mapping_id), repeat(self.hazardsvc),
                                                        repeat(hazard_dataset_id), repeat(hazard_type))

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

    def pipeline_damage_analysis_bulk_input(self, pipelines, mapping_id, hazardsvc, hazard_dataset_id, hazard_type):
        result = []
        fragility_sets = self.fragilitysvc.map_fragilities(mapping_id, pipelines, "Non-Retrofit Fragility ID Code")

        for pipeline in pipelines:

            if pipeline["id"] in fragility_sets.keys():
                result.append(self.pipeline_damage_analysis(pipeline, fragility_sets[pipeline["id"]], hazardsvc,
                                                            hazard_dataset_id, hazard_type))

        return result

    def pipeline_damage_analysis(self, pipeline, fragility_set, hazardsvc, hazard_dataset_id, hazard_type):

        pipeline_results = collections.OrderedDict()
        pipeclass = None
        pgv_repairs = 0.0
        pgd_repairs = 0.0
        total_repairs = 0.0
        break_rate = 0.0
        leak_rate = 0.0
        failure_probability = 0.0
        num_pgd_repairs = 0.0
        num_pgv_repairs = 0.0
        num_repairs = 0.0
        demand_type = None
        hazard_val = 0.0

        # pipeline_results['guid'] = "test"
        pipeline_results['guid'] = pipeline['properties']['guid']
        pipeline_results['pipeclass'] = pipeclass
        pipeline_results['pgvrepairs'] = pgv_repairs
        pipeline_results['pgdrepairs'] = pgd_repairs
        pipeline_results['repairspkm'] = total_repairs
        pipeline_results['breakrate'] = break_rate
        pipeline_results['leakrate'] = leak_rate
        pipeline_results['failprob'] = failure_probability
        pipeline_results['hazardtype'] = demand_type
        pipeline_results['hazardval'] = hazard_val
        pipeline_results['numpgvrpr'] = num_pgv_repairs
        pipeline_results['numpgdrpr'] = num_pgd_repairs
        pipeline_results['numrepairs'] = num_repairs

        return pipeline_results
