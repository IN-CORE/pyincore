#!/usr/bin/env python3

"""
Water Facility Damage

Usage:
    waterfacilitydamage.py INVENTORY HAZARD FRAGILITY MAPPING

Options:
    INVENTORY   Inventory file
    HAZARD      type/id (e.g. earthquake/59f3315ec7d30d4d6741b0bb)
    FRAGILITY   fragility
    MAPPING     fragility mapping
    UNCERTAINITY Include hazard uncertainity
    LIQUEFACTION Include Liquefaction in damage calculations
"""

import collections
from pyincore import InsecureIncoreClient, InventoryDataset, HazardService,\
    FragilityService
from pyincore import GeoUtil, AnalysisUtil
from pyincore.analyses.waterfacilitydamage.LifelineUtil import LifelineUtil
from docopt import docopt
import os
import csv
import concurrent.futures
import multiprocessing
import traceback
import random

class WaterFacilityDamage:
    def __init__(self, client, hazard_service: str):
        # Find hazard type and id
        hazard_service_split = hazard_service.split("/")
        self.hazard_type = hazard_service_split[0]
        self.hazard_dataset_id = hazard_service_split[1]

        # Create Hazard and Fragility service
        self.hazardsvc = HazardService(client)
        self.fragilitysvc = FragilityService(client)

    def get_damage(self, inventory_set: dict, fragility: str,
                   fragility_mapping_id: str, uncertainity:bool=False,
                   liquefaction:bool=False):
        # Get the fragility sets
        if liquefaction:
            # None available in database now for W-Facility PGD
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
            fclty_results = collections.OrderedDict()
            pdg = 0
            std_dev = 0

            dmg_probability = collections.OrderedDict()

            hazard_demand_type = "pga"  # get by hazard type and 4 fragility set
            demand_units = "g"  # Same as above

            location = GeoUtil.get_location(facility)

            # Update this once hazard service supports tornado
            if hazard_type == 'earthquake':
                hazard_val = hazardsvc.get_earthquake_hazard_value(hazard_dataset_id, hazard_demand_type, demand_units,
                                                                   location.y, location.x)

            #limit_states = ['ls-slight', 'ls-moderat', 'ls-extensi', 'ls-complet']
            #dmg_intervals = ['none', 'slight-mod', 'mod-extens', 'ext-comple', 'complete']
            if liquefaction:
                pdg = random.randint(120, 140) #implement API to get pgd

            if uncertainity:
                std_dev = random.random()

            fragility_yvalue = 1.0

            limit_states = LifelineUtil.compute_limit_state_probability(
                fragility_set['fragilityCurves'], hazard_val, fragility_yvalue,
                std_dev)
            dmg_intervals = LifelineUtil.compute_damage_intervals(limit_states)

            result = collections.OrderedDict()
            result = {**limit_states, **dmg_intervals} # py 3.5+


            for k,v in result.items():
                result[k] = round(v,2)

            #result = limit_states.copy()
            #result.update(dmg_intervals)

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
                            'ls_slight', 'ls_moderate', 'ls_extensive',
                            'ls_complete',
                            'none', 'slight-mod', 'mod-extens', 'ext-comple',
                            'complete'
                            ])

            writer.writeheader()
            writer.writerows(output)

        return out_file

if __name__ == '__main__':
        arguments = docopt(__doc__)

        shp_file1 = None

        facility_path = arguments['INVENTORY']
        hazard = arguments['HAZARD']
        fragility = arguments['FRAGILITY']
        mapping_id = arguments['MAPPING']
        uncertainity = arguments['UNCERTAINITY']
        liquefaction = arguments['LIQUEFACTION']

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

            client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", cred[0])
            fcty_dmg = WaterFacilityDamage(client, hazard)
            dmg_output = fcty_dmg.get_damage(facility_set.inventory_set,
                fragility, mapping_id, bool(uncertainity), bool(liquefaction))
            fcty_dmg.write_output('facility-dmg.csv', dmg_output)

        except Exception as e:
            print(str(e))





