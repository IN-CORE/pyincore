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
        fragility_sets_liq = None
        if geology_dataset_id is not None:
            fragility_sets_liq = self.fragilitysvc.match_inventory(
                self.get_input_dataset("dfr3_mapping_set"), pipelines,
                liquefaction_fragility_key)

        values_payload = []
        values_payload_liq = []  # for liquefaction if used
        unmapped_pipelines = []
        mapped_pipelines = []
        for pipeline in pipelines:
            # if find a match fragility for that pipeline
            if pipeline["id"] in fragility_sets.keys():
                fragility_set = fragility_sets[pipeline["id"]]
                location = GeoUtil.get_location(pipeline)
                loc = str(location.y) + "," + str(location.x)
                demands = fragility_set.demand_types
                units = fragility_set.demand_units
                value = {
                    "demands": demands,
                    "units": units,
                    "loc": loc
                }
                values_payload.append(value)
                mapped_pipelines.append(pipeline)

                # Check if liquefaction is applicable
                if use_liquefaction and \
                        geology_dataset_id is not None and \
                        fragility_sets_liq is not None and \
                        pipeline["id"] in fragility_sets_liq:
                    fragility_set_liq = fragility_sets_liq[pipeline["id"]]
                    demands_liq = fragility_set_liq.demand_types
                    units_liq = fragility_set_liq.demand_units
                    value_liq = {
                        "demands": demands_liq,
                        "units": units_liq,
                        "loc": loc
                    }
                    values_payload_liq.append(value_liq)
            else:
                unmapped_pipelines.append(pipeline)
        del pipelines

        if hazard_type == 'earthquake':
            hazard_resp = self.hazardsvc.post_earthquake_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'tsunami':
            hazard_resp = self.hazardsvc.post_tsunami_hazard_values(hazard_dataset_id, values_payload)
        else:
            raise ValueError("The provided hazard type is not supported yet by this analysis")

        # Check if liquefaction is applicable
        if use_liquefaction is True and \
                fragility_sets_liq is not None and \
                geology_dataset_id is not None:
            liquefaction_resp = self.hazardsvc.post_liquefaction_values(hazard_dataset_id, geology_dataset_id,
                                                                        values_payload_liq)

        # calculate LS and DS
        ds_results = []
        damage_results = []
        for i, pipeline in enumerate(mapped_pipelines):
            # default
            pgv_repairs = None
            pgd_repairs = 0.0
            total_repair_rate = None
            break_rate = None
            leak_rate = None
            failure_probability = None
            num_pgv_repairs = None
            num_pgd_repairs = 0.0
            num_repairs = None

            liq_hazard_vals = None
            liq_demand_types = None
            liq_demand_units = None
            liquefaction_prob = None

            ds_result = dict()
            damage_result = dict()
            ds_result['guid'] = pipeline['properties']['guid']
            damage_result['guid'] = pipeline['properties']['guid']

            fragility_set = fragility_sets[pipeline["id"]]
            # TODO assume there is only one curve
            fragility_curve = fragility_set.fragility_curves[0]

            hazard_vals = AnalysisUtil.update_precision_of_lists(hazard_resp[i]["hazardValues"])
            demand_types = hazard_resp[i]["demands"]
            demand_units = hazard_resp[i]["units"]

            hval_dict = dict()
            for j, d in enumerate(fragility_set.demand_types):
                hval_dict[d] = hazard_vals[j]

            if not AnalysisUtil.do_hazard_values_have_errors(hazard_resp[i]["hazardValues"]):
                pipeline_args = fragility_set.construct_expression_args_from_inventory(pipeline)
                pgv_repairs = \
                    fragility_curve.solve_curve_expression(
                        hval_dict, fragility_set.curve_parameters, **pipeline_args)
                # Convert PGV repairs to SI units
                pgv_repairs = PipelineUtil.convert_result_unit(fragility_curve.return_type["unit"], pgv_repairs)

                length = PipelineUtil.get_pipe_length(pipeline)

                # Number of PGV repairs
                num_pgv_repairs = pgv_repairs * length

                # Check if liquefaction is applicable
                if use_liquefaction is True \
                        and fragility_sets_liq is not None \
                        and geology_dataset_id is not None \
                        and liquefaction_resp is not None:
                    fragility_set_liq = fragility_sets_liq[pipeline["id"]]

                    # TODO assume there is only one curve
                    liq_fragility_curve = fragility_set_liq.fragility_curves[0]

                    liq_hazard_vals = AnalysisUtil.update_precision_of_lists(liquefaction_resp[i]["pgdValues"])
                    liq_demand_types = liquefaction_resp[i]["demands"]
                    liq_demand_units = liquefaction_resp[i]["units"]
                    liquefaction_prob = liquefaction_resp[i]['liqProbability']
                    liq_hval_dict = dict()
                    for j, d in enumerate(liquefaction_resp[i]["demands"]):
                        liq_hval_dict[d] = liq_hazard_vals[j]

                    # !important! removing the liqProbability and passing in the "diameter"
                    # no fragility is actually using liqProbability
                    pipeline_args = fragility_set_liq.construct_expression_args_from_inventory(pipeline)
                    pgd_repairs = \
                        liq_fragility_curve.solve_curve_expression(
                            liq_hval_dict, fragility_set_liq.curve_parameters, **pipeline_args)
                    # Convert PGD repairs to SI units
                    pgd_repairs = PipelineUtil.convert_result_unit(liq_fragility_curve.return_type["unit"], pgd_repairs)
                    num_pgd_repairs = pgd_repairs * length

                    # record results
                    if 'pipetype' in pipeline['properties']:
                        damage_result['pipeclass'] = pipeline['properties']['pipetype']
                    elif 'pipelinesc' in pipeline['properties']:
                        damage_result['pipeclass'] = pipeline['properties']['pipelinesc']
                    else:
                        damage_result['pipeclass'] = ""

                break_rate = 0.2 * pgv_repairs + 0.8 * pgd_repairs
                leak_rate = 0.8 * pgv_repairs + 0.2 * pgd_repairs
                total_repair_rate = pgd_repairs + pgv_repairs
                failure_probability = 1 - math.exp(-1.0 * break_rate * length)
                num_repairs = num_pgd_repairs + num_pgv_repairs

            ds_result['pgvrepairs'] = pgv_repairs
            ds_result['pgdrepairs'] = pgd_repairs
            ds_result['repairspkm'] = total_repair_rate
            ds_result['breakrate'] = break_rate
            ds_result['leakrate'] = leak_rate
            ds_result['failprob'] = failure_probability
            ds_result['numpgvrpr'] = num_pgv_repairs
            ds_result['numpgdrpr'] = num_pgd_repairs
            ds_result['numrepairs'] = num_repairs
            ds_result['haz_expose'] = AnalysisUtil.get_exposure_from_hazard_values(hazard_vals, hazard_type)

            damage_result['fragility_id'] = fragility_set.id
            damage_result['demandtypes'] = demand_types
            damage_result['demandunits'] = demand_units
            damage_result['hazardtype'] = hazard_type
            damage_result['hazardval'] = hazard_vals

            # Check if liquefaction is applicable
            if use_liquefaction is True \
                    and fragility_sets_liq is not None \
                    and geology_dataset_id is not None:
                damage_result['liq_fragility_id'] = fragility_sets_liq[pipeline["id"]].id
                damage_result['liqdemandtypes'] = liq_demand_types
                damage_result['liqdemandunits'] = liq_demand_units
                damage_result['liqhazval'] = liq_hazard_vals
                damage_result['liqprobability'] = liquefaction_prob
            else:
                damage_result['liq_fragility_id'] = None
                damage_result['liqdemandtypes'] = None
                damage_result['liqdemandunits'] = None
                damage_result['liqhazval'] = None
                damage_result['liqprobability'] = None

            ds_results.append(ds_result)
            damage_results.append(damage_result)

        # pipelines do not have matched mappings
        for pipeline in unmapped_pipelines:
            ds_result = dict()
            ds_result['guid'] = pipeline['properties']['guid']

            damage_result = dict()
            damage_result['guid'] = pipeline['properties']['guid']
            if 'pipetype' in pipeline['properties']:
                damage_result['pipeclass'] = pipeline['properties']['pipetype']
            elif 'pipelinesc' in pipeline['properties']:
                damage_result['pipeclass'] = pipeline['properties']['pipelinesc']
            else:
                damage_result['pipeclass'] = ""

            damage_result['fragility_id'] = None
            damage_result['demandtypes'] = None
            damage_result['demandunits'] = None
            damage_result['hazardtype'] = None
            damage_result['hazardval'] = None
            damage_result['liq_fragility_id'] = None
            damage_result['liqdemandtypes'] = None
            damage_result['liqdemandunits'] = None
            damage_result['liqhazval'] = None
            damage_result['liqhazval'] = None

            ds_results.append(ds_result)
            damage_results.append(damage_result)

        return ds_results, damage_results

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
                    'type': 'ergo:pipelineDamageVer3'
                },
                {
                    'id': 'metadata',
                    'parent_type': 'pipeline',
                    'description': 'additional metadata in json file about applied hazard value and '
                                   'fragility',
                    'type': 'incore:pipelineDamageSupplement'
                }
            ]
        }
