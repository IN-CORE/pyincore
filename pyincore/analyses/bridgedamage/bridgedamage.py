#!/usr/bin/env python3

from pyincore import InsecureIncoreClient, InventoryDataset, DamageRatioDataset, HazardService, FragilityService
from pyincore import GeoUtil, AnalysisUtil
import os

import requests


class BridgeDamage:
    def __init__(self):

        bridge_path = './input.bridge/'

        # TODO determine the file name
        shp_file = None

        for file in os.listdir(bridge_path):
            if file.endswith(".shp"):
                shp_file = os.path.join(bridge_path, file)

        bridge_shp = os.path.abspath(shp_file)

        self.bridges = InventoryDataset(bridge_shp)

        headers = {'X-Credential-Username': 'jingge2'}  # subtitute with your own username
        self.client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "jingge2")
        #self.client = InsecureIncoreClient("http://localhost:8080", "jingge2")

        # Create Hazard and Fragility service
        self.hazardsvc = HazardService(self.client)
        self.hazard_type = 'earthquake'
        self.hazard_dataset_id = '5aac069a3342c424fc3fb3e2'
        self.fragilitysvc = FragilityService(self.client)

    def compute_bridge_damage_analysis(self):
        mapping_id = "5aa98588949f232724db17fd"
        fragility_set = self.fragilitysvc.map_fragilities(mapping_id, self.bridges.inventory_set,
                                                          "Non-Retrofit Fragility ID Code")
        if len(fragility_set) > 0:
            for item in self.bridges.inventory_set:
                center_point = GeoUtil.get_location(item)
                id = item['id']
                hazard_val = self.hazardsvc.get_earthquake_hazard_values(self.hazard_dataset_id,fragility_set[id]['demandType'].lower(), fragility_set[id]['demandUnits'], [center_point])
                print(hazard_val)


if __name__ == '__main__':
    obj = BridgeDamage()
    obj.compute_bridge_damage_analysis()

