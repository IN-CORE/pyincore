import os
import pandas as pd
import collections

from pyincore import AnalysisUtil, DamageRatioDataset


class CumulativeBuildingDamage:

    def __init__(self, eq_damage, tsunami_damage, dmg_ratios, output_name, output_directory):
        self.output_name = output_name
        self.output_directory = output_directory

        if os.path.isfile(eq_damage):
            self.eq_damage = self.load_csv_file(eq_damage)

        if os.path.isfile(tsunami_damage):
            self.tsunami_damage = self.load_csv_file(tsunami_damage)

        dmg_ratio = None
        if os.path.isfile(dmg_ratios):
            dmg_ratio = DamageRatioDataset(dmg_ratios)

        damage_ratios = dmg_ratio.damage_ratio

        # damage weights for buildings
        self.dmg_weights = [
            float(damage_ratios[1]['Mean Damage Factor']),
            float(damage_ratios[2]['Mean Damage Factor']),
            float(damage_ratios[3]['Mean Damage Factor']),
            float(damage_ratios[4]['Mean Damage Factor'])]
        self.dmg_weights_std_dev = [float(damage_ratios[1]['Deviation Damage Factor']),
                                    float(damage_ratios[2]['Deviation Damage Factor']),
                                    float(damage_ratios[3]['Deviation Damage Factor']),
                                    float(damage_ratios[4]['Deviation Damage Factor'])]

    def calculateDamage(self):
        output = pd.DataFrame()
        for idx, eq_building in self.eq_damage.iterrows():
            id = eq_building['guid']
            tsunami_building = self.tsunami_damage.loc[self.tsunami_damage['guid'] == eq_building['guid']]

            if len(tsunami_building) == 0:
                break
            for idy, tsunami_building in tsunami_building.iterrows():
                damage_interval_eq = collections.OrderedDict()
                damage_interval_eq["insignific"] = eq_building["insignific"]
                damage_interval_eq["moderate"] = eq_building["moderate"]
                damage_interval_eq["heavy"] = eq_building["heavy"]
                damage_interval_eq["complete"] = eq_building["complete"]
                eq_limit_states = AnalysisUtil.calculate_limit_states(damage_interval_eq)

                damage_interval_tsunami = collections.OrderedDict()
                damage_interval_tsunami["insignific"] = tsunami_building["insignific"]
                damage_interval_tsunami["moderate"] = tsunami_building["moderate"]
                damage_interval_tsunami["heavy"] = tsunami_building["heavy"]
                damage_interval_tsunami["complete"] = tsunami_building["complete"]

                tsunami_limit_states = AnalysisUtil.calculate_limit_states(damage_interval_tsunami)

                limit_states = collections.OrderedDict()

                limit_states["collprev"] = eq_limit_states["collprev"] + tsunami_limit_states["collprev"] - \
                                  eq_limit_states["collprev"] * tsunami_limit_states["collprev"] + \
                                  ((eq_limit_states["lifesfty"] - eq_limit_states["collprev"]) *
                                   (tsunami_limit_states["lifesfty"] - tsunami_limit_states ["collprev"]))

                limit_states["lifesfty"] = eq_limit_states["lifesfty"] + tsunami_limit_states["lifesfty"] - \
                                   eq_limit_states["lifesfty"] * tsunami_limit_states["lifesfty"] + \
                                  ((eq_limit_states["immocc"] - eq_limit_states["lifesfty"]) *
                                   (tsunami_limit_states["immocc"] - tsunami_limit_states["lifesfty"]))

                limit_states["immocc"] = eq_limit_states["immocc"] + tsunami_limit_states["immocc"] - \
                    eq_limit_states["immocc"] * tsunami_limit_states["immocc"]

                damage_state = AnalysisUtil.calculate_damage_interval(limit_states)

                mean_damage = AnalysisUtil.calculate_mean_damage(self.dmg_weights, damage_state)

                mean_damage_std_dev = AnalysisUtil.calculate_mean_damage_std_deviation(self.dmg_weights,
                                                                                       self.dmg_weights_std_dev,
                                                                                       damage_state,
                                                                                       mean_damage['meandamage'])
                bldg_results = collections.OrderedDict()

                bldg_results["guid"] = eq_building["guid"]
                bldg_results["Immediate Occupancy"] = limit_states["immocc"]
                bldg_results["Life Safety"] = limit_states["lifesfty"]
                bldg_results["Collapse Prevention"] = limit_states["collprev"]
                bldg_results["Insignificant"] = damage_state["insignific"]
                bldg_results["Moderate"] = damage_state["moderate"]
                bldg_results["Heavy"] = damage_state["heavy"]
                bldg_results["Complete"] = damage_state["complete"]
                bldg_results["Mean Damage"] = mean_damage
                bldg_results["Mean Damage Dev"] = mean_damage_std_dev
                bldg_results["Hazard"] = "Earthquake+Tsunami"
                # bldg_results["Period"] = eq_building["period"]

                output.append(pd.Series(bldg_results, name=eq_building["guid"]))

        output_file = os.path.join(output_directory, self.output_name + ".csv")
        output.to_csv(output_file, mode="w+", index=False)

        return output


    @staticmethod
    def load_csv_file(file_name):
        read_file = pd.read_csv(file_name, header="infer")
        return read_file


base_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
eq_damage = base_path + "/eq_bldg_dmg_results.csv"
tsunami_damage = base_path + "/tsunami_bldg_dmg_results.csv"
output_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output'))
damage_ratios = base_path + "/damage_ratios.csv"

cbd = CumulativeBuildingDamage(eq_damage, tsunami_damage, damage_ratios, output_directory, "output")
cbd.calculateDamage()
