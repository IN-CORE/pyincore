#!/usr/bin/env python3
from pyincore import InsecureIncoreClient, InventoryDataset, DamageRatioDataset, HazardService, FragilityService
from pyincore import GeoUtil
from pyincore.analyses.bridgedamage.bridgeutil import BridgeUtil
import os
import collections


class BridgeDamage:
    def __init__(self, client, dmg_ratio_dir: str, hazard_service: str, use_liquefaction: bool,
                 use_hazard_uncertainty: bool, output_file_name: str):

        self.client = client

        # Create hazard and fragility service
        self.hazardsvc = HazardService(self.client)

        # Find hazard type and id
        hazard_service_split = hazard_service.split("/")
        self.hazard_type = hazard_service_split[0] if hazard_service_split is not None else "Unknown"
        self.hazard_dataset_id = hazard_service_split[1]

        self.fragilitysvc = FragilityService(self.client)
        # Needs modification
        self.use_liquefaction = use_liquefaction
        self.use_hazard_uncertainty = use_hazard_uncertainty
        self.fragility_key = BridgeUtil.DEFAULT_FRAGILITY_KEY
        dmg_ratio = None
        if (os.path.isfile(dmg_ratio_dir)):
            dmg_ratio = DamageRatioDataset(dmg_ratio_dir)
        else:
            for file in os.listdir(dmg_ratio_dir):
                if file.endswith(".csv"):
                    dmg_ratio = DamageRatioDataset(os.path.abspath(os.path.join(dmg_ratio_dir, file)))

        self.dmg_ratios = dmg_ratio.damage_ratio
        # damage weights for buildings
        self.dmg_weights = [
            float(self.dmg_ratios[1]['MeanDR']),
            float(self.dmg_ratios[2]['MeanDR']),
            float(self.dmg_ratios[3]['MeanDR']),
            float(self.dmg_ratios[4]['MeanDR']),
            float(self.dmg_ratios[5]['MeanDR'])]
        self.output_file_name = output_file_name


    def get_damage(self, inventory_set: dict, mapping_id: str):
        '''
        Main function to perform bridge damage analysis.

        :return: a list of ordered dictionary.
        '''
        output = []

        fragility_set = self.fragilitysvc.map_fragilities(mapping_id, inventory_set, self.fragility_key)
        if len(fragility_set) > 0:
            for item in inventory_set:
                if item["id"] in fragility_set:
                    output.append(self.bridge_damage_analysis(item, fragility_set[item['id']]))
                    BridgeUtil.write_to_file(output, ["ls-slight", "ls-moderat", "ls-extensi", "ls-complet", "none",
                                                "slight-mod", "mod-extens", "ext-comple", "complete", "meandamage",
                                                "expectval", "retrofit", "retro_cost", "hazardtype", "hazardval"], self.output_file_name)

        return output

    def bridge_damage_analysis(self, cur_bridge, cur_fragility):
        '''
        Calculates bridge damage results for single fragility.

        :param cur_bridge: current bridge
        :param cur_fragility: current fragility
        :return: an ordered dictionary with 15 fields listed below
        '''
        bridge_results = collections.OrderedDict()

        center_point = GeoUtil.get_location(cur_bridge)
        hazard_val = self.hazardsvc.get_earthquake_hazard_value(self.hazard_dataset_id,
                                                                cur_fragility['demandType'].lower(),
                                                                cur_fragility['demandUnits'],
                                                                center_point.y, center_point.x)
        hazard_type = cur_fragility['hazardType']
        hazard_std_dev = BridgeUtil.get_hazard_std_dev() if self.use_hazard_uncertainty else 0.0
        exceedence_probability = BridgeUtil.get_probability_of_exceedence(cur_fragility, hazard_val, hazard_std_dev, self.use_liquefaction)
        dmg_intervals = BridgeUtil.get_damage_state_intervals(exceedence_probability)
        mean_damage = BridgeUtil.get_mean_damage(dmg_intervals, 1, cur_bridge, self.dmg_weights)
        expected_damage = BridgeUtil.get_expected_damage(mean_damage, self.dmg_ratios)
        retrofit_cost = BridgeUtil.get_retrofit_cost(self.fragility_key)
        retrofit_type = BridgeUtil.get_retrofit_type(self.fragility_key)

        bridge_results["ls-slight"] = exceedence_probability[0]
        bridge_results["ls-moderat"] = exceedence_probability[1]
        bridge_results["ls-extensi"] = exceedence_probability[2]
        bridge_results["ls-complet"] = exceedence_probability[3]
        bridge_results["none"] = dmg_intervals[0]
        bridge_results["slight-mod"] = dmg_intervals[1]
        bridge_results["mod-extens"] = dmg_intervals[2]
        bridge_results["ext-comple"] = dmg_intervals[3]
        bridge_results["complete"] = dmg_intervals[4]
        bridge_results["meandamage"] = mean_damage
        bridge_results["expectval"] = expected_damage
        bridge_results["retrofit"] = retrofit_type
        bridge_results["retro_cost"] = retrofit_cost
        bridge_results["hazardtype"] = hazard_type
        bridge_results["hazardval"] = hazard_val

        return bridge_results



if __name__ == '__main__':
    client = InsecureIncoreClient("http://localhost:8080", "jingge2")
    bridge_file_path = './input.bridge/shelby_county_bridge'
    dmg_ratio_dir = './dmgratio/'
    hazard_service = "earthquake/5aac087a3342c424fc3fb3e4"
    use_hazard_uncertainty = False
    use_liquefaction = False

    shp_file = None
    for file in os.listdir(bridge_file_path):
        if file.endswith(".shp"):
            shp_file = os.path.join(bridge_file_path, file)

    bridges = InventoryDataset(os.path.abspath(shp_file))

    obj = BridgeDamage(client, dmg_ratio_dir, hazard_service, use_liquefaction,
                       use_hazard_uncertainty, "output-test.csv")
    obj.get_damage(bridges.inventory_set, "5aa98588949f232724db17fd")