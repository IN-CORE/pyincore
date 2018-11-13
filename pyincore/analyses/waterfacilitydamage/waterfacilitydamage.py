#!/usr/bin/env python3

"""
Water Facility Damage
"""

import collections

from itertools import repeat
from pyincore import BaseAnalysis, HazardService, FragilityService, GeoUtil, AnalysisUtil
import csv
import concurrent.futures
import random


class WaterFacilityDamage(BaseAnalysis):
    """Computes water facility damage for an earthquake exposure

    """

    DEFAULT_FRAGILITY_KEY = "pga"
    DEFAULT_LIQ_FRAGILITY_KEY = "pgd"

    def __init__(self, incore_client):
        #Create Hazard and Fragility service
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)
        super(WaterFacilityDamage, self).__init__(incore_client)

    def get_spec(self):
        return {
            'name': 'water-facility-damage',
            'description': 'water facility damage analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': False,
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
                    'id': 'liquefaction_geology_dataset_id',
                    'required': False,
                    'description': 'Liquefaction geology/susceptibility dataset id. '
                                   'If not provided, liquefaction will be ignored',
                    'type': str
                },
                {
                    'id': 'liquefaction_fragility_key',
                    'required': False,
                    'description': 'Fragility key to use in liquefaction mapping dataset',
                    'type': str
                },
                {
                    'id': 'use_hazard_uncertainty',
                    'required': False,
                    'description': 'Use hazard uncertainty',
                    'type': bool
                },
                {
                    'id': 'num_cpu',
                    'required': False,
                    'description': 'If using parallel execution, the number of cpus to request',
                    'type': int
                },
            ],
            'input_datasets': [
                {
                    'id': 'water_facilities',
                    'required': True,
                    'description': 'Water Facility Inventory',
                    'type': ['ergo:waterFacilityTopo'],
                },
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'water_facilities',
                    'type': 'ergo:waterFacilityDamageVer4'
                }
            ]
        }

    def run(self):
        """
        Executes Water Facility Damage Analysis
        Returns:

        """
        # Facility dataset
        inventory_set = self.get_input_dataset("water_facilities").get_inventory_reader()

        # Get hazard input
        hazard_dataset_id = self.get_parameter("hazard_id")

        # Hazard type of the exposure
        hazard_type = self.get_parameter("hazard_type")

        user_defined_cpu = 1

        if not self.get_parameter("num_cpu") is None and self.get_parameter(
                "num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(self,
            len(inventory_set), user_defined_cpu)

        avg_bulk_input_size = int(len(inventory_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(inventory_set)
        while count < len(inventory_list):
            inventory_args.append(
                inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.waterfacility_damage_concurrent_execution(
            self.waterfacilityset_damage_analysis, num_workers,
            inventory_args, repeat(hazard_type), repeat(hazard_dataset_id))

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"))

        #return self.write_output(self.get_parameter("result_name"), results)
        spec = self.get_spec()

        return True


    def waterfacility_damage_concurrent_execution(self, function_name, parallel_processes,
                                          *args):
        output = []
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=parallel_processes) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output


    def waterfacilityset_damage_analysis(self, facilities, hazard_type, hazard_dataset_id):
        result = []
        liq_fragility = None
        mapping_id = self.get_parameter("mapping_id")
        liq_geology_dataset_id = self.get_parameter("liquefaction_geology_dataset_id")
        uncertainty = self.get_parameter("use_hazard_uncertainty")

        # TODO: Use fragility_key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = self.DEFAULT_FRAGILITY_KEY

        pga_fragility_set = self.fragilitysvc.map_fragilities(mapping_id, facilities, fragility_key)

        if liq_geology_dataset_id is not None:
            liq_fragility_key = self.get_parameter("liquefaction_fragility_key")
            if liq_fragility_key is None:
                liq_fragility_key = self.DEFAULT_LIQ_FRAGILITY_KEY
            liq_fragility_set = self.fragilitysvc.map_fragilities(mapping_id, facilities, liq_fragility_key)

        for facility in facilities:
            fragility = pga_fragility_set[facility["id"]]
            if liq_geology_dataset_id is not None and facility["id"] in liq_fragility_set:
                liq_fragility = liq_fragility_set[facility["id"]]

            result.append(self.waterfacility_damage_analysis(facility, fragility, liq_fragility,
                                hazard_dataset_id, liq_geology_dataset_id, uncertainty))
        return result

    def waterfacility_damage_analysis(self, facility, fragility, liq_fragility, hazard_dataset_id,
                                      liq_geology_dataset_id, uncertainty):
        std_dev = 0
        #TODO Get this from API once implemented
        if uncertainty:
            std_dev = random.random()

        fragility_yvalue = 1.0  # is this relevant? copied from v1

        hazard_demand_type = fragility['demandType']
        demand_units = fragility['demandUnits']
        liq_hazard_type = ""
        liq_hazard_val = 0.0
        liquefaction_prob = 0.0
        location = GeoUtil.get_location(facility)
        hazard_val_set = self.hazardsvc.get_earthquake_hazard_values(hazard_dataset_id,hazard_demand_type,
                                                            demand_units, points=[location.y, location.x])
        hazard_val = hazard_val_set[0]['hazardValue']

        limit_states = AnalysisUtil.compute_limit_state_probability(fragility['fragilityCurves'],
                                                            hazard_val, fragility_yvalue, std_dev)



        if liq_fragility is not None and liq_geology_dataset_id:
            liq_hazard_type = liq_fragility['demandType']
            pgd_demand_units = liq_fragility['demandUnits']
            location_str = str(location.y) + "," + str(location.x)

            liquefaction = self.hazardsvc.get_liquefaction_values(hazard_dataset_id, liq_geology_dataset_id,
                                                            pgd_demand_units, [location_str])
            liq_hazard_val = liquefaction[0][liq_hazard_type]
            liquefaction_prob = liquefaction[0]['liqProbability']
            pgd_limit_states = AnalysisUtil.compute_limit_state_probability(liq_fragility['fragilityCurves'],
                                                                liq_hazard_val, fragility_yvalue, std_dev)

            limit_states = AnalysisUtil.adjust_limit_states_for_pgd(limit_states, pgd_limit_states)

        dmg_intervals = AnalysisUtil.compute_damage_intervals(limit_states)

        result = collections.OrderedDict()
        result = {**limit_states, **dmg_intervals}  # Needs py 3.5+

        # for k, v in result.items():
        #     result[k] = round(v, 2)

        metadata = collections.OrderedDict()
        metadata['guid'] = facility['properties']['guid']
        metadata['hazardtype'] = "earthquake"
        metadata['demandtype'] = hazard_demand_type
        metadata['hazardval'] = hazard_val
        metadata['liqhaztype'] = liq_hazard_type
        metadata['liqhazval'] = liq_hazard_val
        metadata['liqprobability'] = liquefaction_prob

        result = {**metadata, **result}
        return result







