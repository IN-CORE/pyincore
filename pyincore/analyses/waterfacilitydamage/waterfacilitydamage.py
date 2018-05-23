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
"""

import collections
from pyincore import InsecureIncoreClient, InventoryDataset, HazardService, FragilityService
from pyincore import GeoUtil, AnalysisUtil
from docopt import docopt
import os
import csv
import concurrent.futures
import multiprocessing
import traceback

class WaterFacilityDamage:
    def __init__(self, client, hazard_service: str ):
        # Find hazard type and id
        hazard_service_split = hazard_service.split("/")
        self.hazard_type = hazard_service_split[0]
        self.hazard_dataset_id = hazard_service_split[1]

        # Create Hazard and Fragility service
        self.hazardsvc = HazardService(client)
        self.fragilitysvc = FragilityService(client)

    def get_damage(self, inventory_set: dict, fragility: str, fragility_mapping_id: str):
        # Get the fragility sets
        fragility_sets = self.fragilitysvc.map_fragilities(fragility_mapping_id, inventory_set,
                                                           "pga")
        output = []
        for facility in inventory_set:
            facility_output = self.get_water_facility_damage(inventory_set, self.hazard_type,
                                                self.hazard_dataset_id, self.hazardsvc, fragility_sets)
            output.append(facility_output)

        return output

    def get_water_facility_damage(self, facility, hazard_type, hazard_dataset_id, hazardsvc, fragility_sets):
        try:
            fclty_results = collections.OrderedDict()
            hazardVal = 0.0
            demand_type = "Unknown"

            dmg_probability = collections.OrderedDict()

            hazard_demand_type = "pga"  # get by hazard type and from fragility set
            demand_units = "g"  # Same as above

            location = GeoUtil.get_location(facility)

            # Update this once hazard service supports tornado
            if hazard_type == 'earthquake':
                hazard_val = hazardsvc.get_earthquake_hazard_value(hazard_dataset_id, hazard_demand_type, demand_units,
                                                                   location.y, location.x)

        except Exception as e:
            # This prints the type, value and stacktrace of error being handled.
            traceback.print_exc()
            print()
            raise e

if __name__ == '__main__':
        arguments = docopt(__doc__)

        shp_file1 = None

        facility_path = arguments['INVENTORY']
        hazard = arguments['HAZARD']
        fragility = arguments['FRAGILITY']
        mapping_id = arguments['MAPPING']
        #dmg_ratios = arguments['DMGRATIO']

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
            fcty_dmg.get_damage(facility_set.inventory_set, fragility, mapping_id )


        except Exception as e:
            print(str(e))





