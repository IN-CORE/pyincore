#!/usr/bin/env python3

"""
Water Facility Damage
"""

import collections

from itertools import repeat
from pyincore import HazardService, FragilityService, GeoUtil, AnalysisUtil
import os
import csv
import concurrent.futures
import traceback
import random

class WaterFacilityDamage:
    def __init__(self, client):
        #Create Hazard and Fragility service
        self.hazardsvc = HazardService(client)
        self.fragilitysvc = FragilityService(client)

    @staticmethod
    def get_output_metadata():
        output = dict()
        output["dataType"] = "ergo:waterFacilityDamage"
        output["format"] = "table"

        return output

    def get_damage(self, inventory_set:dict, mapping_id: str, hazard_input: str, liq_geology_dataset_id: str=None,
                    uncertainity:bool=False, num_threads: int=0):
        """

        :param inventory_set:
        :param mapping_id:
        :param hazard_input:
        :param liq_geology_dataset_id:
        :param uncertainity:
        :param num_threads:
        :return:
        """

        hazard_input_split = hazard_input.split("/")
        hazard_type = hazard_input_split[0]
        hazard_dataset_id = hazard_input_split[1]

        if num_threads != -1:
            parallel_threads = AnalysisUtil.determine_parallelism_locally(self,
                                        len(inventory_set), num_threads)

            features_per_thread = int(len(inventory_set) / parallel_threads)
            inventory_args = []
            count = 0
            inventory_list = list(inventory_set)

            while count < len(inventory_list):
                inventory_args.append(
                    inventory_list[count:count + features_per_thread])
                count += features_per_thread

            output = self.waterfacility_damage_concurrent_execution(
                self.waterfacilityset_damage_analysis, parallel_threads,
                inventory_args, repeat(mapping_id), repeat(self.hazardsvc),
                repeat(hazard_dataset_id), repeat(liq_geology_dataset_id), repeat(uncertainity))
        else:
            output = self.waterfacilityset_damage_analysis(inventory_set, mapping_id, self.hazardsvc,
                                            hazard_dataset_id,liq_geology_dataset_id,uncertainity)

        out_file_name = "dmg-results.csv"

        return self.write_output(out_file_name, output)

    def waterfacility_damage_concurrent_execution(self, function_name, parallel_processes,
                                          *args):
        output = []
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=parallel_processes) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def waterfacilityset_damage_analysis(self, facilities, mapping_id,
                                            hazardsvc, hazard_dataset_id,
                                            liq_geology_dataset_id, uncertainity):
        result = []
        liq_fragility = None

        pga_fragility_set = self.fragilitysvc.map_fragilities(mapping_id, facilities, "pga")

        if liq_geology_dataset_id is not None:
            liq_fragility_set = self.fragilitysvc.map_fragilities(mapping_id, facilities, "pgd")

        for facility in facilities:
            fragility = pga_fragility_set[facility["id"]]
            if liq_geology_dataset_id is not None and facility["id"] in liq_fragility_set:
                liq_fragility = liq_fragility_set[facility["id"]]

            result.append(self.waterfacility_damage_analysis(facility, fragility, liq_fragility,hazardsvc,
                                hazard_dataset_id, liq_geology_dataset_id, uncertainity))
        return result

    def waterfacility_damage_analysis(self, facility, fragility, liq_fragility,hazardsvc, hazard_dataset_id,
                                      liq_geology_dataset_id, uncertainity):
        std_dev = 0
        #TODO Get this from API once implemented
        if uncertainity:
            std_dev = random.random()

        fragility_yvalue = 1.0  # is this relevant? copied from v1

        hazard_demand_type = "pga" #Move to init?
        demand_units = "g"
        liq_hazard_type = "pgd"
        liq_hazard_val = 0.0
        liquefaction_prob = 0.0
        location = GeoUtil.get_location(facility)
        hazard_val = hazardsvc.get_earthquake_hazard_value(hazard_dataset_id, hazard_demand_type,
                                                        demand_units, location.y, location.x)

        limit_states = AnalysisUtil.compute_limit_state_probability(fragility['fragilityCurves'],
                                                            hazard_val, fragility_yvalue, std_dev)



        if liq_fragility is not None and liq_geology_dataset_id:
            liq_fragility_curve = liq_fragility['fragilityCurves'][0]
            liq_hazard_type = liq_fragility['demandType']
            pgd_demand_units = liq_fragility['demandUnits']
            location_str = str(location.y) + "," + str(location.x)

            liquefaction = hazardsvc.get_liquefaction_values(hazard_dataset_id, liq_geology_dataset_id,
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


    def write_output(self, out_file, output):
        with open(out_file, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, dialect="unix",
                fieldnames=['guid', 'hazardtype','demandtype', 'hazardval',
                            'liqhaztype', 'liqhazval', 'liqprobability',
                            'ls_slight', 'ls_moderate', 'ls_extensive', 'ls_complete',
                            'none', 'slight-mod', 'mod-extens', 'ext-comple', 'complete'
                            ])

            writer.writeheader()
            writer.writerows(output)

        return out_file





