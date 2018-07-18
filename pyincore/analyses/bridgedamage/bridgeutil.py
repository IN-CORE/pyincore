import os
import csv
import collections
import math

class BridgeUtil:
    BRIDGE_FRAGILITY_KEYS = {
        "elastomeric bearing retrofit fragility id code": ["Elastomeric Bearing", "eb"],
        "steel jacket retrofit fragility id code": ["Steel Jacket", "sj"],
        "restrainer cables retrofit fragility id code": ["Restrainer Cables", "rc"],
        "seat extender retrofit fragility id code": ["Seat Extender", "se"],
        "shear key retrofit fragility id code": ["Shear Key", "sk"],
        "non-retrofit fragility id code": ["as built", "none"]
    }

    DEFAULT_FRAGILITY_KEY = "Non-Retrofit Fragility ID Code";

    @staticmethod
    def get_hazard_std_dev():
        '''
        To be developed

        :return:
        '''
        return 0.0

    @staticmethod
    def get_damage_state_intervals(exceedence_probability):
        '''
        Calculates damage state intervals for current fragility.

        :param exceedence_probability: input list of exceedence probability
        :return: damage intervals
        '''
        dmg_intervals = []
        for idx, val in enumerate(exceedence_probability):
            if idx == 0:
                dmg_intervals.append(1.0 - val)
            else:
                dmg_intervals.append(exceedence_probability[idx - 1] - exceedence_probability[idx])

        dmg_intervals.append(exceedence_probability[-1])
        return dmg_intervals

    @staticmethod
    def get_mean_damage(dmg_intervals, start_idx, cur_bridge, dmg_weights):
        """
        Calculates mean damage.

        :param dmg_intervals: list of damage intervals
        :param start_idx:
        :param cur_bridge:
        :return:
        """
        if "spans" in cur_bridge["properties"] and cur_bridge["properties"]["spans"].isdigit():
            n = int(cur_bridge["properties"]["spans"])
        elif "SPANS" in cur_bridge["properties"] and cur_bridge["properties"]["SPANS"].isdigit():
            n = int(cur_bridge["properties"]["SPANS"])
        else:
            n = 1

        if n > 10:
            n = 10
            print("A bridge was found with greater than 10 spans: " + str(cur_bridge))

        weight_slight = dmg_weights[0]
        weight_moderate = dmg_weights[1]
        weight_extensive = dmg_weights[2]
        weight_collapse0 = dmg_weights[3]
        weight_collapse1 = dmg_weights[4]

        mean_damage = weight_slight * dmg_intervals[start_idx] \
                      + weight_moderate * dmg_intervals[start_idx + 1] \
                      + weight_extensive * dmg_intervals[start_idx + 2]

        if n >= 3:
            mean_damage += weight_collapse1 / n * dmg_intervals[start_idx + 3]
        else:
            mean_damage += weight_collapse0 * dmg_intervals[start_idx + 3]

        return mean_damage

    @staticmethod
    def get_expected_damage(mean_damage, dmg_ratios):
        '''
        Calculates expected damage value.

        :param mean_damage:
        :return:
        '''
        no_dmg_bound = [float(dmg_ratios[1]["LowerBound"]), float(dmg_ratios[1]["UpperBound"])]
        slight_bound = [float(dmg_ratios[2]["LowerBound"]), float(dmg_ratios[2]["UpperBound"])]
        moderate_bound = [float(dmg_ratios[3]["LowerBound"]), float(dmg_ratios[3]["UpperBound"])]
        extensive_bound = [float(dmg_ratios[4]["LowerBound"]), float(dmg_ratios[4]["UpperBound"])]
        collapse_bound = [float(dmg_ratios[5]["LowerBound"]), float(dmg_ratios[5]["UpperBound"])]
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
        return dmg_ratios[idx]["MeanDR"]


    @staticmethod
    def get_probability_of_exceedence(cur_fragility, hazard_val, std_dev, use_liquefaction):
        '''
        Calculates probability of exceedence.

        :param cur_fragility:
        :param hazard_val:
        :param std_dev:
        :return:
        '''
        exceedence_probability = []
        for curve in cur_fragility["fragilityCurves"]:
            if use_liquefaction:
                curve = BridgeUtil.adjust_fragility_for_liquefaction(curve, cur_fragility["LIQ"])
            if curve["className"].endswith("StandardFragilityCurve"):
                beta = math.sqrt(math.pow(curve["beta"], 2) + math.pow(std_dev, 2))
            else:
                beta = curve["beta"]
            exceedence_probability.append(BridgeUtil.get_normal_distribution_cumulative_probability(
                (hazard_val - curve["median"]) / beta, 0.0, 1.0))

        return exceedence_probability

    @staticmethod
    def get_normal_distribution_cumulative_probability(x, mean, std_dev):
        '''
        Calculate normal distribution cumulative probability.

        :param x:
        :param mean: mean to initialize normal distribution
        :param std_dev: standard deviation to initialize normal distribution
        :return:
        '''
        return 0.5 * (1.0 + math.erf((x - mean) / (std_dev * math.sqrt(2.0))))

    @staticmethod
    def adjust_fragility_for_liquefaction(fragility_curve, liquefaction):
        '''
        Adjusts fragility curve object by input parameter liquefaction

        :param fragility_curve: original fragility curve
        :param liquefaction: a string parameter indicating liquefaction type
        :return: an adjust fragility curve object
        '''
        liquefaction_unified = str(liquefaction).upper()
        if liquefaction_unified == "U":
            multiplier = 0.85
        elif liquefaction_unified == "Y":
            multiplier = 0.65
        else:
            multiplier = 1.0

        fragility_curve_adj = {"className": fragility_curve["className"],
                               "description": fragility_curve['description'],
                               "median": fragility_curve['median'] * multiplier,
                               "beta": fragility_curve['beta'],
                               'curveType': fragility_curve['curveType']}

        return fragility_curve_adj

    @staticmethod
    def get_retrofit_cost(target_fragility_key):
        '''
        To be continue. This function is not completed yet. Need real data example on the following variable
            private FeatureDataset bridgeRetrofitCostEstimate

        :return:
        '''
        retrofit_cost = 0.0
        if target_fragility_key.lower() == BridgeUtil.DEFAULT_FRAGILITY_KEY.lower():
            return retrofit_cost
        else:
            retrofit_code = BridgeUtil.get_retrofit_code()
        return retrofit_cost


    @staticmethod
    def get_retrofit_type(target_fragility_key):
        """
        Gets retrofit type by looking up BRIDGE_FRAGILITY_KEYS dictionary

        :return: a string retrofit type
        """
        return BridgeUtil.BRIDGE_FRAGILITY_KEYS[target_fragility_key.lower()][0] \
            if target_fragility_key.lower() not in BridgeUtil.BRIDGE_FRAGILITY_KEYS else "none"


    @staticmethod
    def get_retrofit_code(target_fragility_key):
        '''
        Gets retrofit code by looking up BRIDGE_FRAGILITY_KEYS dictionary

        :return: a string retrofit code
        '''
        return BridgeUtil.BRIDGE_FRAGILITY_KEYS[target_fragility_key.lower()][1] \
            if target_fragility_key.lower() not in BridgeUtil.BRIDGE_FRAGILITY_KEYS else "none"


    @staticmethod
    def write_to_file(output, fieldname_list, output_file_name):
        '''
        Generates output csv file with header

        :param output: content to be written to output
        :return:
        '''
        # Write Output to csv
        with open(output_file_name, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, dialect="unix", fieldnames=fieldname_list)
            writer.writeheader()
            writer.writerows(output)
