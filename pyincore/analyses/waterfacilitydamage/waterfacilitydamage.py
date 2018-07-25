#!/usr/bin/env python3

"""
Water Facility Damage

Usage:
    waterfacilitydamage.py INVENTORY HAZARD MAPPING UNCERTAINITY LIQUEFACTION

Options:
    INVENTORY   Inventory file
    HAZARD      type/id (e.g. earthquake/59f3315ec7d30d4d6741b0bb)
    MAPPING     fragility mapping
    UNCERTAINITY Include hazard uncertainity
    LIQUEFACTION Include Liquefaction in damage calculations
"""

import collections
import math
from itertools import repeat
from pyincore import InsecureIncoreClient, InventoryDataset, HazardService,\
    FragilityService, GeoUtil, AnalysisUtil
from docopt import docopt
import os
import csv
import concurrent.futures
import multiprocessing
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

    def get_damage1(self, inventory_set:dict, mapping_id: str, hazard_input: str, liq_geology_dataset_id: str=None,
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
        if uncertainity:
            std_dev = random.random()

        fragility_yvalue = 1.0  # is this relevant? copied from v1

        hazard_demand_type = "pga" #Move to init?
        demand_units = "g"
        location = GeoUtil.get_location(facility)
        hazard_val = hazardsvc.get_earthquake_hazard_value(hazard_dataset_id, hazard_demand_type,
                                                        demand_units, location.y, location.x)

        limit_states = AnalysisUtil.compute_limit_state_probability(fragility['fragilityCurves'],
                                                            hazard_val, fragility_yvalue, std_dev)

        liq_hazard_type = ""
        liq_hazard_val = 0.0
        liquefaction_prob = 0.0 #Remove

        if liq_fragility is not None and liq_geology_dataset_id:
            liq_fragility_curve = liq_fragility['fragilityCurves'][0]
            liq_hazard_type = liq_fragility['demandType']
            pgd_demand_units = liq_fragility['demandUnits']
            location_str = str(location.y) + "," + str(location.x)

            liquefaction = hazardsvc.get_liquefaction_values(hazard_dataset_id, liq_geology_dataset_id,
                                                            pgd_demand_units, [location_str])
            liq_hazard_val = liquefaction[0]['pgd']
            liquefaction_prob = liquefaction[0]['liqProbability']
            pgd_limit_states = AnalysisUtil.compute_limit_state_probability(liq_fragility['fragilityCurves'],
                                                                liq_hazard_val, fragility_yvalue, std_dev)

            limit_states = AnalysisUtil.adjust_limit_states_for_pgd(limit_states, pgd_limit_states)

        dmg_intervals = AnalysisUtil.compute_damage_intervals(limit_states)

        result = collections.OrderedDict()
        result = {**limit_states, **dmg_intervals}  # py 3.5+

        for k, v in result.items():
            result[k] = round(v, 2)

        metadata = collections.OrderedDict()
        metadata['guid'] = facility['properties']['guid']
        metadata['hazardtype'] = "earthquake"
        metadata['hazardval'] = round(hazard_val, 4)

        result = {**metadata, **result}
        return result

    def get_damage(self, inventory_set: dict, fragility_mapping_id: str, uncertainity:bool=False,
                   liquefaction:bool=False):
        # Get the fragility sets
        if liquefaction:
            #TODO: No mappings available in database now to test W-Facility PGD.
            fragility_sets = self.fragilitysvc.map_fragilities(
                fragility_mapping_id, inventory_set, "pgd")
        else:
            fragility_sets = self.fragilitysvc.map_fragilities(
            fragility_mapping_id, inventory_set, "pga")

        output = []
        for facility in inventory_set:
            facility_output = self.get_water_facility_damage(facility,
                self.hazard_type, self.hazard_dataset_id, self.hazardsvc,
                fragility_sets[facility['id']], uncertainity, liquefaction )
            output.append(facility_output)

        return output

    def get_water_facility_damage(self, facility, hazard_type,
                                  hazard_dataset_id, hazardsvc, fragility_set,
                                  uncertainity, liquefaction):
        try:
            std_dev = 0

            hazard_demand_type = "pga"  # get by hazard type and 4 fragility set
            demand_units = "g"  # Same as above

            location = GeoUtil.get_location(facility)

            # Update this once hazard service supports tornado
            if hazard_type == 'earthquake':
                hazard_val = hazardsvc.get_earthquake_hazard_value(hazard_dataset_id, hazard_demand_type, demand_units,
                                                                   location.y, location.x)

            #TODO: This will enventually be fetched from API.
            # Pyincore wrapper needs to be developed too
            if uncertainity:
                std_dev = random.random()

            fragility_yvalue = 1.0 # is this relevant? copied from v1

            #If liq.calculate pgd limit states and adjust limit states

            limit_states = AnalysisUtil.compute_limit_state_probability(
                fragility_set['fragilityCurves'], hazard_val, fragility_yvalue,
                std_dev)

            if liquefaction:
                # TODO: Develop Pyincore wrapper for pgd calculation and use it
                # INCORE-415 has the API call.
                pgd = random.randint(120, 140)

                pgd_limit_states = AnalysisUtil.compute_limit_state_probability(
                    fragility_set['fragilityCurves'], pgd, fragility_yvalue,
                    std_dev)

                limit_states = AnalysisUtil.adjustLimitStatesForPGD(
                                            limit_states, pgd_limit_states)


            dmg_intervals = AnalysisUtil.compute_damage_intervals(limit_states)

            result = collections.OrderedDict()
            result = {**limit_states, **dmg_intervals} # py 3.5+


            for k,v in result.items():
                result[k] = round(v,2)


            metadata = collections.OrderedDict()
            metadata['guid'] = facility['properties']['guid']
            metadata['hazardtype'] = hazard_type
            metadata['hazardval'] = round(hazard_val, 4)

            result = {**metadata, **result}
            return result

        except Exception as e:
            # This prints the type, value and stacktrace of error being handled.
            traceback.print_exc()
            print()
            raise e

    def write_output(self, out_file, output):
        with open(out_file, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, dialect="unix",
                fieldnames=['guid', 'hazardtype','hazardval',
                            'ls_slight', 'ls_moderate', 'ls_extensive', 'ls_complete',
                            'none', 'slight-mod', 'mod-extens', 'ext-comple', 'complete'
                            ])

            writer.writeheader()
            writer.writerows(output)

        return out_file

if __name__ == '__main__':
        arguments = docopt(__doc__)

        shp_file1 = None

        facility_path = arguments['INVENTORY']
        hazard = arguments['HAZARD']
        mapping_id = arguments['MAPPING']
        uncertainity = int(arguments['UNCERTAINITY'])
        liquefaction = int(arguments['LIQUEFACTION'])


        # TODO determine the file name
        shp_file = None

        for file in os.listdir(facility_path):
            if file.endswith(".shp"):
                shp_file = os.path.join(facility_path, file)

        facilty_shp = os.path.abspath(shp_file)
        facility_set = InventoryDataset(facilty_shp)

        try:
            with open(".incorepw", 'r') as f:
                cred = f.read().splitlines()

            client = InsecureIncoreClient("http://incore2-services:8888", cred[0])
            fcty_dmg = WaterFacilityDamage(client, hazard)
            dmg_output = fcty_dmg.get_damage(facility_set.inventory_set,
                            mapping_id, bool(uncertainity), bool(liquefaction))
            fcty_dmg.write_output('facility-dmg.csv', dmg_output)

        except Exception as e:
            print(str(e))





