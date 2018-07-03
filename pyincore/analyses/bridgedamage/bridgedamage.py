#!/usr/bin/env python3

from pyincore import InsecureIncoreClient, InventoryDataset, DamageRatioDataset, HazardService, FragilityService
from pyincore import GeoUtil, AnalysisUtil
import os
import csv
import collections
import math

DEFAULT_FRAGILITY_KEY = "Non-Retrofit Fragility ID Code";

BRIDGE_FRAGILITY_KEYS = {
    "elastomeric bearing retrofit fragility id code": ["Elastomeric Bearing", "eb"],
    "steel jacket retrofit fragility id code": ["Steel Jacket", "sj"],
    "restrainer cables retrofit fragility id code": ["Restrainer Cables", "rc"],
    "seat extender retrofit fragility id code": ["Seat Extender", "se"],
    "shear key retrofit fragility id code": ["Shear Key", "sk"],
    "non-retrofit fragility id code": ["as built", "none"]
}


class BridgeDamage:
    def __init__(self, client, bridge_file_path: str, dmg_ratio_dir: str):

        bridge_file_path = './input.bridge/'

        # TODO determine the file name
        shp_file = None

        for file in os.listdir(bridge_file_path):
            if file.endswith(".shp"):
                shp_file = os.path.join(bridge_file_path, file)

        bridge_shp = os.path.abspath(shp_file)

        self.bridges = InventoryDataset(bridge_shp)

        headers = {'X-Credential-Username': 'jingge2'}  # subtitute with your own username
        # self.client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "jingge2")
        self.client = InsecureIncoreClient("http://localhost:8080", "jingge2")

        # Create Hazard and Fragility service
        self.hazardsvc = HazardService(self.client)
        self.hazard_type = 'earthquake'
        self.hazard_dataset_id = '5aac087a3342c424fc3fb3e4'
        self.fragilitysvc = FragilityService(self.client)
        self.mapping_id = "5aa98588949f232724db17fd"

        self.fragility_key = DEFAULT_FRAGILITY_KEY

        dmg_ratio_dir = './dmgratio/'
        dmg_ratio = None
        if (os.path.isfile(dmg_ratio_dir)):
            dmg_ratio = DamageRatioDataset(dmg_ratio_dir)
        else:
            for file in os.listdir(dmg_ratio_dir):
                if file.endswith(".csv"):
                    dmg_ratio = DamageRatioDataset(os.path.abspath(os.path.join(dmg_ratio_dir, file)))

        self.dmg_ratios = dmg_ratio.damage_ratio
        print(self.dmg_ratios)
        # damage weights for buildings
        self.dmg_weights = [
            float(self.dmg_ratios[1]['MeanDR']),
            float(self.dmg_ratios[2]['MeanDR']),
            float(self.dmg_ratios[3]['MeanDR']),
            float(self.dmg_ratios[4]['MeanDR']),
            float(self.dmg_ratios[5]['MeanDR'])]

    def get_damage(self):
        output = []

        fragility_set = self.fragilitysvc.map_fragilities(self.mapping_id, self.bridges.inventory_set,
                                                          "Non-Retrofit Fragility ID Code")
        if len(fragility_set) > 0:
            for item in self.bridges.inventory_set:
                output.append(self.bridge_damage_analysis(item, fragility_set[item['id']]))

        self.write_to_file(output)

        return output

    def bridge_damage_analysis(self, cur_bridge, cur_fragility):

        bridge_results = collections.OrderedDict()

        exceedence_probability = [0.0, 0.0, 0.0, 0.0]
        center_point = GeoUtil.get_location(cur_bridge)
        hazard_val = self.hazardsvc.get_earthquake_hazard_value(self.hazard_dataset_id,
                                                                cur_fragility['demandType'].lower(),
                                                                cur_fragility['demandUnits'],
                                                                center_point.y, center_point.x)
        hazard_type = cur_fragility['hazardType']

        dmg_intervals = self.get_damage_state_intervals(exceedence_probability)
        mean_damage = self.get_mean_damage(dmg_intervals, 1)
        expected_damage = self.get_expected_damage(mean_damage)
        retrofit_cost = self.get_retrofit_cost()
        retrofit_type = self.get_retrofit_type()

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

    def get_damage_state_intervals(self, exceedence_probability):
        dmg_intervals = []
        for idx, val in enumerate(exceedence_probability):
            if idx == 0:
                dmg_intervals.append(1.0 - val)
            else:
                dmg_intervals.append(exceedence_probability[idx - 1] - exceedence_probability[idx])

        dmg_intervals.append(exceedence_probability[-1])
        return dmg_intervals

    def get_mean_damage(self, dmg_intervals, start_idx):
        n = 1
        weight_slight = self.dmg_weights[0]
        weight_moderate = self.dmg_weights[1]
        weight_extensive = self.dmg_weights[2]
        weight_collapse0 = self.dmg_weights[3]
        weight_collapse1 = self.dmg_weights[4]

        mean_damage = weight_slight * dmg_intervals[start_idx] \
                      + weight_moderate * dmg_intervals[start_idx + 1] \
                      + weight_extensive * dmg_intervals[start_idx + 2]

        if n >= 3:
            mean_damage += weight_collapse1 / n * dmg_intervals[start_idx + 3]
        else:
            mean_damage += weight_collapse0 * dmg_intervals[start_idx + 3]

        return mean_damage

    def get_expected_damage(self, mean_damage):
        no_dmg_bound = [float(self.dmg_ratios[1]["LowerBound"]), float(self.dmg_ratios[1]["UpperBound"])]
        slight_bound = [float(self.dmg_ratios[2]["LowerBound"]), float(self.dmg_ratios[2]["UpperBound"])]
        moderate_bound = [float(self.dmg_ratios[3]["LowerBound"]), float(self.dmg_ratios[3]["UpperBound"])]
        extensive_bound = [float(self.dmg_ratios[4]["LowerBound"]), float(self.dmg_ratios[4]["UpperBound"])]
        collapse_bound = [float(self.dmg_ratios[5]["LowerBound"]), float(self.dmg_ratios[5]["UpperBound"])]
        if no_dmg_bound[0] <= mean_damage <= no_dmg_bound[1]:
            idx = 0
        elif slight_bound[0] <= mean_damage <= slight_bound[1]:
            idx = 1
        elif moderate_bound[0] <= mean_damage <= moderate_bound[1]:
            idx = 2
        elif extensive_bound[0] <= mean_damage <= extensive_bound[1]:
            idx = 3
        elif collapse_bound[0] <= mean_damage <= collapse_bound[1]:
            idx = 4
        else:
            idx = 0
        return self.dmg_ratios[idx]["MeanDR"]

    def getProbabilityOfExceedence(self, cur_fragility, hazard_val, stddev):
        '''
        fragility_curves = cur_fragility["fragilityCurves"]
        exceedence_probability = []
        for curve in fragility_curves:
            old_beta = curve["beta"]
            new_beta = math.sqrt(math.pow(old_beta, 2) + math.pow(stddev, 2))
            exceedence_probability.append()
        '''

    def get_retrofit_type(self):
        return BRIDGE_FRAGILITY_KEYS[self.fragility_key][
            0] if self.fragility_key.lower() in BRIDGE_FRAGILITY_KEYS.keys() else "none"

    def get_retrofit_cost(self):
        return BRIDGE_FRAGILITY_KEYS[self.fragility_key][
            1] if self.fragility_key.lower() in BRIDGE_FRAGILITY_KEYS.keys() else "none"

    def write_to_file(self, output):
        output_file_name = "bridge-damage-analysis-results.csv"

        # Write Output to csv
        with open(output_file_name, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, dialect="unix",
                                    fieldnames=["ls-slight", "ls-moderat", "ls-extensi", "ls-complet", "none",
                                                "slight-mod", "mod-extens", "ext-comple", "complete", "meandamage",
                                                "expectval", "retrofit", "retro_cost", "hazardtype", "hazardval"])
            writer.writeheader()
            writer.writerows(output)


if __name__ == '__main__':
    obj = BridgeDamage()
    obj.get_damage()

