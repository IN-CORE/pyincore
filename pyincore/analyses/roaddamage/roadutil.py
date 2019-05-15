# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import collections
import csv
import math
from scipy.stats import norm


class RoadUtil:
    """Utility methods for the road damage analysis."""
    DEFAULT_FRAGILITY_KEY = "Non-Retrofit Fragility ID Code"

    @staticmethod
    def get_damage_ratio_rows(csv_reader: csv.DictReader):
        """Parse a csv file with damage ratios.

        Args:
            csv_reader (csv.DictReader): CSV file reader.

        Returns:
            list: Data rows.

        """
        csv_rows = []

        # Ignore the header
        row_index = 0
        for row in csv_reader:
            if row_index > 0:
                csv_rows.append(row)

            row_index += 1

        return csv_rows

    @staticmethod
    def get_hazard_std_dev():
        """Get hazard standard deviation.

        Note:
            TO DO: To be developed.

        Returns
            float: Standard deviation.

        """
        return 0.0

    @staticmethod
    def get_damage_state_intervals(damage_probability):
        """Calculates damage state intervals for current fragility.

        Args:
            damage_probability (list): An input list of damage probability.

        Returns:
            list of floats: Damage intervals.

        """
        dmg_intervals = []
        for idx, val in enumerate(damage_probability):
            if idx == 0:
                dmg_intervals.append(1.0 - val)
            else:
                dmg_intervals.append(damage_probability[idx - 1] - damage_probability[idx])

        dmg_intervals.append(damage_probability[-1])
        return dmg_intervals

    @staticmethod
    def get_mean_damage(dmg_intervals, start_idx, dmg_ratio_tbl):
        """Calculates mean damage.

        Args:
            dmg_intervals (list): A list of damage intervals.
            start_idx (int): An initial index of damage intervals, starting at 1 ignores the
                no damage interval.
            dmg_ratio_tbl (obj): Damage ratios, descriptions and states.

        Returns:
            float: A value of mean damage.

        """
        weight_slight = float(dmg_ratio_tbl[1]['Best Mean Damage Ratio'])
        weight_moderate = float(dmg_ratio_tbl[2]['Best Mean Damage Ratio'])
        weight_extensive = float(dmg_ratio_tbl[3]['Best Mean Damage Ratio'])

        mean_damage = \
            weight_slight * dmg_intervals[start_idx] + \
            weight_moderate * dmg_intervals[start_idx + 1] + \
            weight_extensive * dmg_intervals[start_idx + 2]

        return mean_damage

    @staticmethod
    def get_expected_damage(mean_damage, dmg_ratios):
        """Calculates mean damage.

        Args:
            mean_damage (float): Mean damage value.
            dmg_ratios (obj): Damage ratios, descriptions and states.

        Returns:
            float: A value of the damage state.

        """
        no_dmg_bound = [float(dmg_ratios[1]["Lower Bound"]), float(dmg_ratios[1]["Upper Bound"])]
        slight_bound = [float(dmg_ratios[2]["Lower Bound"]), float(dmg_ratios[2]["Upper Bound"])]
        moderate_bound = [float(dmg_ratios[3]["Lower Bound"]), float(dmg_ratios[3]["Upper Bound"])]
        extensive_bound = [float(dmg_ratios[4]["Lower Bound"]), float(dmg_ratios[4]["Upper Bound"])]
        if no_dmg_bound[0] <= mean_damage <= no_dmg_bound[1]:
            idx = 1 
        elif slight_bound[0] <= mean_damage <= slight_bound[1]:
            idx = 2
        elif moderate_bound[0] <= mean_damage <= moderate_bound[1]:
            idx = 3
        elif extensive_bound[0] <= mean_damage <= extensive_bound[1]:
            idx = 4
        else:
            idx = 1
        return dmg_ratios[idx]["Damage State"]

    @staticmethod
    def get_probability_of_damage(road, fragility_set, hazard_val, std_dev, use_liquefaction):
        """Calculates probabilities of damage.

        Args:
            road (obj): A JSON mapping of a geometric object from the inventory: current road.
            fragility_set (obj): A JSON description of fragility applicable to the road.
            hazard_val (float): Hazard value.
            std_dev (float): Standard deviation.
            use_liquefaction (bool): Liquefaction. True for using liquefaction, False otherwise.

        Returns:
            list: A list of float probabilities.

        """
        damage_probability = collections.OrderedDict()
        for fragility in fragility_set["fragilityCurves"]:
            median = float(fragility['median'])
            beta = float(fragility['beta'])

            if use_liquefaction and 'liq' in road['properties']:
                fragility = RoadUtil.adjust_fragility_for_liquefaction(fragility, road['properties']['liq'])
                median = float(fragility['median'])
            if fragility["className"].endswith("StandardFragilityCurve"):
                beta = math.sqrt(math.pow(fragility["beta"], 2) + math.pow(std_dev, 2))

            # Compute probability
            probability = 0.0
            if hazard_val > 0.0:
                if fragility['curveType'] == 'Normal':
                    sp = (math.log(hazard_val) - math.log(median)) / beta
                    probability = norm.cdf(sp)
                elif fragility['curveType'] == "LogNormal":
                    x = (math.log(hazard_val) - median) / beta
                    probability = norm.cdf(x)

            if len(damage_probability) < 1:
                damage_probability['immocc'] = probability
            elif len(damage_probability) < 2:
                damage_probability['lifesfty'] = probability
            elif len(damage_probability) < 3:
                damage_probability['collprev'] = probability
            else:
                print("Too many values for damage_probability")

        return damage_probability

    @staticmethod
    def adjust_fragility_for_liquefaction(fragility_curve, liquefaction):
        """Adjusts fragility curve object by input parameter liquefaction.

        Args:
            fragility_curve (obj): A JSON description of current fragility curve.
            liquefaction (str): Liquefaction type.

        Returns:
            obj: An adjusted fragility curve.

        """
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
    def write_to_file(output, fieldname_list, output_file_name):
        """Generates output csv file with header.

        Args:
            output (str): A content to be written to output.
            fieldname_list (list): A list of header names.
            output_file_name (str): Output file name.

        """
        # Write Output to csv
        with open(output_file_name, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, dialect="unix", fieldnames=fieldname_list)
            writer.writeheader()
            writer.writerows(output)
