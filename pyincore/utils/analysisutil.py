# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import collections
import csv
import math
import os
import re
from typing import List, Dict
from collections import Counter

from decimal import getcontext, Decimal

from pyincore import DataService
from pyincore.globals import DAMAGE_PRECISION
from pyincore.utils import evaluateexpression


class AnalysisUtil:
    """Utility methods for analysis"""
    DOCSTR_FORMAT = "$DESC$ \n\n" \
                    "Args: \n\t" \
                    "$ARGS$ " \
                    "\n" \
                    "Returns: \n\t" \
                    "$RETS$ "

    getcontext().prec = DAMAGE_PRECISION

    @staticmethod
    def update_precision(num, precision: int = DAMAGE_PRECISION):
        try:
            r = round(float(num), precision)
            return r
        except TypeError:
            print("Error trying to round non numeric value")
            raise

    @staticmethod
    def update_precision_of_dicts(states: dict) -> dict:
        updated_states = {key: AnalysisUtil.update_precision(states[key]) for key in states}
        return updated_states

    @staticmethod
    def update_precision_of_lists(hazard_vals: List) -> List:
        updated_hazard_vals = []
        for val in hazard_vals:
            if val is not None:
                if math.ceil(val) == -9999:  # if it's an error code(-9999.x) do not update precision
                    updated_hazard_vals.append(val)
                else:
                    updated_hazard_vals.append(AnalysisUtil.update_precision(val))
            else:
                updated_hazard_vals.append(None)
        return updated_hazard_vals

    @staticmethod
    def float_to_decimal(num: float):
        return Decimal(str(num))

    @staticmethod
    def float_list_to_decimal(num_list: list):
        return [Decimal(str(num)) for num in num_list]

    @staticmethod
    def float_dict_to_decimal(num_dict: dict):
        return {key: Decimal(str(num_dict[key])) for key in num_dict}

    @staticmethod
    def calculate_mean_damage(dmg_ratio_tbl, dmg_intervals,
                              damage_interval_keys, is_bridge=False,
                              bridge_spans=1):
        if len(damage_interval_keys) < 4:
            raise ValueError("we only accept 4 damage or more than 4 interval keys!")

        output = collections.OrderedDict()
        if len(dmg_ratio_tbl) == 5:
            output['meandamage'] = float(
                dmg_ratio_tbl[1]["Best Mean Damage Ratio"]) * float(
                dmg_intervals[damage_interval_keys[0]]) + float(
                dmg_ratio_tbl[2]["Best Mean Damage Ratio"]) * float(
                dmg_intervals[damage_interval_keys[1]]) + float(
                dmg_ratio_tbl[3]["Best Mean Damage Ratio"]) * float(
                dmg_intervals[damage_interval_keys[2]]) + float(
                dmg_ratio_tbl[4]["Best Mean Damage Ratio"]) * float(
                dmg_intervals[damage_interval_keys[3]])

        elif len(dmg_ratio_tbl) == 4:
            output['meandamage'] = float(
                dmg_ratio_tbl[0]["Mean Damage Factor"]) * float(
                dmg_intervals[damage_interval_keys[0]]) + float(
                dmg_ratio_tbl[1]["Mean Damage Factor"]) * float(
                dmg_intervals[damage_interval_keys[1]]) + float(
                dmg_ratio_tbl[2]["Mean Damage Factor"]) * float(
                dmg_intervals[damage_interval_keys[2]]) + float(
                dmg_ratio_tbl[3]["Mean Damage Factor"]) * float(
                dmg_intervals[damage_interval_keys[3]])

        elif len(dmg_ratio_tbl) == 6 and is_bridge:
            # this is for bridge
            weight_slight = float(dmg_ratio_tbl[1]['Best Mean Damage Ratio'])
            weight_moderate = float(dmg_ratio_tbl[2]['Best Mean Damage Ratio'])
            weight_extensive = float(
                dmg_ratio_tbl[3]['Best Mean Damage Ratio'])
            weight_collapse0 = float(
                dmg_ratio_tbl[4]['Best Mean Damage Ratio'])
            weight_collapse1 = float(
                dmg_ratio_tbl[5]['Best Mean Damage Ratio'])

            output['meandamage'] = \
                weight_slight * float(dmg_intervals[damage_interval_keys[1]]) + \
                weight_moderate * float(
                    dmg_intervals[damage_interval_keys[2]]) + \
                weight_extensive * float(
                    dmg_intervals[damage_interval_keys[3]])

            if bridge_spans >= 3:
                output[
                    'meandamage'] += weight_collapse1 / bridge_spans * float(
                    dmg_intervals[damage_interval_keys[4]])
            else:
                output['meandamage'] += weight_collapse0 * float(
                    dmg_intervals[damage_interval_keys[4]])
        else:
            raise ValueError('We cannot handle this damage ratio format.')

        return output

    @staticmethod
    def calculate_mean_damage_std_deviation(dmg_ratio_tbl, dmg,
                                            mean_damage, damage_interval_keys):
        output = collections.OrderedDict()
        result = 0.0
        idx = 0
        for key in damage_interval_keys:
            result += float(dmg[key]) * (math.pow(
                float(dmg_ratio_tbl[idx]["Mean Damage Factor"]), 2) + math.pow(
                float(dmg_ratio_tbl[idx]["Deviation Damage Factor"]), 2))
            idx += 1

        output['mdamagedev'] = math.sqrt(result - math.pow(mean_damage, 2))
        return output

    @staticmethod
    def get_expected_damage(mean_damage, dmg_ratios):
        """Calculates mean damage.

        Args:
            mean_damage (float): Mean damage value.
            dmg_ratios (obj): Damage ratios, descriptions and states.

        Returns:
            float: A value of the damage state.

        """
        no_dmg_bound = [float(dmg_ratios[1]["Lower Bound"]),
                        float(dmg_ratios[1]["Upper Bound"])]
        slight_bound = [float(dmg_ratios[2]["Lower Bound"]),
                        float(dmg_ratios[2]["Upper Bound"])]
        moderate_bound = [float(dmg_ratios[3]["Lower Bound"]),
                          float(dmg_ratios[3]["Upper Bound"])]
        extensive_bound = [float(dmg_ratios[4]["Lower Bound"]),
                           float(dmg_ratios[4]["Upper Bound"])]
        collapse_bound = [float(dmg_ratios[5]["Lower Bound"]),
                          float(dmg_ratios[5]["Upper Bound"])]
        if no_dmg_bound[0] <= mean_damage <= no_dmg_bound[1]:
            idx = 1
        elif slight_bound[0] <= mean_damage <= slight_bound[1]:
            idx = 2
        elif moderate_bound[0] <= mean_damage <= moderate_bound[1]:
            idx = 3
        elif extensive_bound[0] <= mean_damage <= extensive_bound[1]:
            idx = 4
        elif collapse_bound[0] <= mean_damage <= collapse_bound[1]:
            idx = 5
        else:
            idx = 1
        return dmg_ratios[idx]["Damage State"]

    @staticmethod
    def determine_parallelism_locally(self, number_of_loops,
                                      user_defined_parallelism=0):
        """Determine the parallelism on the current compute node.

        Args:
            number_of_loops: total number of loops will be executed on current compute node
            user_defined_parallelism: a customized parallelism specified by users

        Returns:
            int: parallelism on current compute node

        """

        # gets the local cpu number
        number_of_cpu = os.cpu_count()
        if number_of_loops > 0:
            if user_defined_parallelism > 0:
                return min(number_of_cpu, number_of_loops,
                           user_defined_parallelism)
            else:
                return min(number_of_cpu, number_of_loops)
        else:
            return number_of_cpu

    @staticmethod
    def create_result_dataset(datasvc: DataService, parentid: str,
                              result_files: List[str], title: str,
                              output_metadata: Dict[str, str]):
        # Result metadata
        properties = output_metadata
        properties["title"] = title
        properties["sourceDataset"] = parentid

        # Create child dataset with parent dataset as sourceDataset
        result_dataset = datasvc.create_dataset(properties)
        result_dataset_id = result_dataset["id"]

        # Attach files to result dataset
        datasvc.add_files_to_dataset(result_dataset_id, result_files)

        return result_dataset_id

    @staticmethod
    def adjust_damage_for_liquefaction(limit_state_probabilities, ground_failure_probabilities):
        """Adjusts building damage probability based on liquefaction ground failure probability
        with the liq_dmg, we know that it is 3 values, the first two are the same.
        The 3rd might be different.
        We always want to apply the first two to all damage states except the highest.

        Args:
            limit_state_probabilities (obj): Limit state probabilities.
            ground_failure_probabilities (list): Ground failure probabilities.

        Returns:
            OrderedDict: Adjusted limit state probability.

        """
        keys = list(limit_state_probabilities.keys())
        adjusted_limit_state_probabilities = collections.OrderedDict()

        for i in range(len(keys)):
            # check and see...if we are trying to use the last ground failure
            # number for something other than the
            # last limit-state-probability, then we should use the
            # second-to-last probability of ground failure instead.

            if i > len(ground_failure_probabilities) - 1:
                prob_ground_failure = ground_failure_probabilities[len(ground_failure_probabilities) - 2]
            else:
                prob_ground_failure = ground_failure_probabilities[i]

            adjusted_limit_state_probabilities[keys[i]] = \
                limit_state_probabilities[keys[i]] + prob_ground_failure \
                - limit_state_probabilities[keys[i]] * prob_ground_failure

        # the final one is the last of limitStates should match with the last of ground failures
        j = len(limit_state_probabilities) - 1
        prob_ground_failure = ground_failure_probabilities[-1]
        adjusted_limit_state_probabilities[keys[j]] = \
            limit_state_probabilities[keys[j]] \
            + prob_ground_failure - limit_state_probabilities[keys[j]] * prob_ground_failure

        return adjusted_limit_state_probabilities

    @staticmethod
    def adjust_limit_states_for_pgd(limit_states, pgd_limit_states):
        try:
            adj_limit_states = collections.OrderedDict()

            for key, value in limit_states.items():
                adj_limit_states[key] = limit_states[key] + pgd_limit_states[key] - \
                                        (limit_states[key] * pgd_limit_states[key])

            return AnalysisUtil.update_precision_of_dicts(adj_limit_states)

        except KeyError as e:
            print('Mismatched keys encountered in the limit states')
            print(str(e))

    @staticmethod
    def get_csv_table_rows(csv_reader: csv.DictReader, ignore_first_row=True):
        csv_rows = []

        row_index = 0
        for row in csv_reader:
            if ignore_first_row:
                # Ignore the first row
                if row_index > 0:
                    csv_rows.append(row)
            else:
                csv_rows.append(row)

            row_index += 1

        return csv_rows

    @staticmethod
    def create_gdocstr_from_spec(specs):
        """

        Args:
            specs (dict): Json of the specs for each analysis

        Returns:
            str: Google format docstrings to copy for the run() method of any analysis

        """
        desc = specs['description']
        args = ""
        rets = ""

        for dataset in specs['input_datasets']:
            is_opt = ""
            if not dataset['required']:
                is_opt = ", " + "optional"

            args = \
                args + dataset['id'] + "(str" + is_opt + ") : " \
                + dataset['description'] + ". " \
                + AnalysisUtil.get_custom_types_str(dataset['type']) + "\n\t"

        for param in specs['input_parameters']:
            is_opt = ""
            if not param['required']:
                is_opt = ", " + "optional"

            args = \
                args + param['id'] + "(" + AnalysisUtil.get_type_str(param['type']) + is_opt + ") : " \
                + param['description'] + "\n\t"

        for dataset in specs['output_datasets']:
            rets = rets + dataset['id'] + ": " \
                   + dataset[
                       'description'] + ". " + AnalysisUtil.get_custom_types_str(
                dataset['type']) + "\n\t"

        docstr = AnalysisUtil.DOCSTR_FORMAT.replace("$DESC$", desc).replace(
            "$ARGS$",
            args).replace("$RETS$", rets)

        print(docstr)

    @staticmethod
    def get_type_str(class_type):
        """

        Args:
            class_type (str): Example: <class 'int'>

        Returns:
            str: Text inside first single quotes of a string

        """

        t = str(class_type)
        match = re.search('\'([^"]*)\'', t)
        if match is not None:
            return match.group(1)
        return None

    @staticmethod
    def get_custom_types_str(types):
        """

        Args:
            types (str, list): Can be string or List of strings

        Returns:
            str: Formatted string with applicable datatypes used to generate docstrigns from specs

        """
        custom_types_str = 'Applicable dataset type(s): '
        if (isinstance(types, str)):
            return custom_types_str + types
        if (isinstance(types, list)):
            if (len(types) > 1):
                idx = 0
                for type in types:
                    if idx < len(types) - 1:
                        custom_types_str += type + ", "
                    else:
                        custom_types_str += type
                    idx = idx + 1
                return custom_types_str
            else:
                return types[0]

    @staticmethod
    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    @staticmethod
    def get_hazard_demand_type(building, fragility_set, hazard_type):
        """
        Get hazard demand type. This method is intended to replace get_hazard_demand_type. Fragility_set is not a
        json but a fragilityCurveSet object now.

        Args:
            building (obj): A JSON mapping of a geometric object from the inventory: current building.
            fragility_set (obj): FragilityCurveSet object
            hazard_type (str): A hazard type such as earthquake, tsunami etc.

        Returns:
            str: A hazard demand type.

        """
        BLDG_STORIES = "no_stories"
        PROPERTIES = "properties"
        BLDG_PERIOD = "period"

        fragility_hazard_type = fragility_set.demand_types[0].lower()
        hazard_demand_type = fragility_hazard_type

        if hazard_type.lower() == "earthquake":
            num_stories = building[PROPERTIES][BLDG_STORIES]
            # Get building period from the fragility if possible

            building_args = fragility_set.construct_expression_args_from_inventory(building)
            building_period = fragility_set.fragility_curves[0].get_building_period(
                fragility_set.curve_parameters, **building_args)

            if fragility_hazard_type.endswith('sa') and fragility_hazard_type != 'sa':
                # This fixes a bug where demand type is in a format similar to 1.0 Sec Sa
                if len(fragility_hazard_type.split()) > 2:
                    building_period = fragility_hazard_type.split()[0]
                    fragility_hazard_type = "Sa"

            hazard_demand_type = fragility_hazard_type

            # This handles the case where some fragilities only specify Sa, others a specific period of Sa
            if not hazard_demand_type.endswith('pga'):
                # If the fragility does not contain the period calculation, check if the dataset has it
                if building_period == 0.0 and BLDG_PERIOD in building[PROPERTIES]:
                    if building[PROPERTIES][BLDG_PERIOD] > 0.0:
                        building_period = building[PROPERTIES][BLDG_PERIOD]

                hazard_demand_type = str(building_period) + " " + fragility_hazard_type
        elif hazard_type.lower() == "tsunami":
            if hazard_demand_type == "momentumflux":
                hazard_demand_type = "mmax"
            elif hazard_demand_type == "inundationdepth":
                hazard_demand_type = "hmax"

        return hazard_demand_type

    @staticmethod
    def get_hazard_demand_types(building, fragility_set, hazard_type):
        """
        Get hazard demand type. This method is intended to replace get_hazard_demand_type. Fragility_set is not a
        json but a fragilityCurveSet object now.

        Args:
            building (obj): A JSON mapping of a geometric object from the inventory: current building.
            fragility_set (obj): FragilityCurveSet object
            hazard_type (str): A hazard type such as earthquake, tsunami etc.

        Returns:
            str: A hazard demand type.

        """
        BLDG_STORIES = "no_stories"
        PROPERTIES = "properties"
        BLDG_PERIOD = "period"

        fragility_demand_types = fragility_set.demand_types
        adjusted_demand_types = []

        for demand_type in fragility_demand_types:
            adjusted_demand_type = demand_type
            # TODO: Due to the mismatch in demand types names on DFR3 vs hazard service, we should refactor this before
            # TODO: using expression based fragilities for tsunami & earthquake
            if hazard_type.lower() == "tsunami":
                demand_type = demand_type.lower()
                if demand_type == "momentumflux":
                    adjusted_demand_type = "mmax"
                elif demand_type == "inundationdepth":
                    adjusted_demand_type = "hmax"
            elif hazard_type.lower() == "earthquake":
                demand_type = demand_type.lower()
                num_stories = building[PROPERTIES][BLDG_STORIES]
                # Get building period from the fragility if possible
                building_args = fragility_set.construct_expression_args_from_inventory(building)
                building_period = fragility_set.fragility_curves[0].get_building_period(
                    fragility_set.curve_parameters, **building_args)

                # TODO: There might be a bug here as this is not handling SD
                if demand_type.endswith('sa'):
                    # This fixes a bug where demand type is in a format similar to 1.0 Sec Sa
                    if demand_type != 'sa':
                        if len(demand_type.split()) > 2:
                            building_period = demand_type.split()[0]
                            adjusted_demand_type = str(building_period) + " " + "SA"
                    else:
                        if building_period == 0.0:
                            if BLDG_PERIOD in building[PROPERTIES] and building[PROPERTIES][BLDG_PERIOD] > 0.0:

                                building_period = building[PROPERTIES][BLDG_PERIOD]
                            else:
                                # try to calculate the period from the expression
                                for param in fragility_set.curve_parameters:
                                    if param["name"].lower() == "period":
                                        # TODO: This is a hack and expects a parameter with name "period" present.
                                        #  This can potentially cause naming conflicts in some fragilities

                                        building_period = evaluateexpression.evaluate(param["expression"],
                                                                                      {"num_stories": num_stories})
                                        # TODO: num_stories logic is not tested. should find a fragility with
                                        #  periodEqnType = 2 or 3 to test. periodEqnType = 1 doesn't need num_stories.

                        adjusted_demand_type = str(building_period) + " " + "SA"

            adjusted_demand_types.append(adjusted_demand_type)
        return adjusted_demand_types

    @staticmethod
    def group_by_demand_type(inventories, fragility_sets, hazard_type="earthquake", is_building=False):
        """
        This method should replace group_by_demand_type in the future. Fragility_sets is not list of dictionary (
        json) anymore but a list of FragilityCurveSet objects

        Args:
            inventories (dict): dictionary of {id: intentory}
            fragility_sets (dict): fragility_sets
            hazard_type (str): default to earthquake
            is_building (bool): if the inventory is building or not

        Returns:
            dict: dGrouped inventory with { (demandunit, demandtype):[inventory ids] }

        """
        grouped_inventory = dict()
        for fragility_id, frag in fragility_sets.items():

            # TODO this method will be deprecated so this is temporary fix
            demand_type = frag.demand_types[0]
            demand_unit = frag.demand_units[0]

            if is_building:
                inventory = inventories[fragility_id]
                demand_type = AnalysisUtil.get_hazard_demand_type(inventory, frag, hazard_type)

            tpl = (demand_type, demand_unit)
            grouped_inventory.setdefault(tpl, []).append(fragility_id)

        return grouped_inventory

    @staticmethod
    def get_exposure_from_hazard_values(hazard_vals, hazard_type):
        """Finds if a point is exposed to hazard based on all the demand values present.
        Returns \"n/a\" for earthquake, tsunami, hurricane and hurricane windfields

        Args:
            hazard_vals (list): List of hazard values returned by the service for a particular point
            hazard_type (str): Type of the hazard

        Returns:
            str: If hazard is exposed or not. Can be one of 'yes', 'no', 'partial', 'error' or 'n/a'

        """

        # This method should handle other 'error' cases when service is able to handle exceptions by returning -9999/NaN
        # and return "error". hazard_type parameter should be removed when all hazards are supported on the service.

        if len(hazard_vals) == 0:
            return "error"

        supported_hazards = ["earthquake", "tsunami", "tornado", "hurricane", "flood"]
        hazard_exposure = "n/a"
        if hazard_type.lower() in supported_hazards:
            if AnalysisUtil.do_hazard_values_have_errors(hazard_vals):
                hazard_exposure = "error"
            else:
                cnt_hazard_vals = Counter(hazard_vals)
                if None in cnt_hazard_vals:
                    if cnt_hazard_vals.get(None) == len(hazard_vals):
                        hazard_exposure = "no"
                    else:
                        hazard_exposure = "partial"
                else:
                    hazard_exposure = "yes"  # none of the values are nulls

        return hazard_exposure

    @staticmethod
    def do_hazard_values_have_errors(hazard_vals):
        """ Checks if any of the hazard values have errors

        Args:
            hazard_vals(list): List of hazard values returned by the service for a particular point

        Returns: True if any of the values are error codes such as -9999.1, -9999.2 etc.

        """
        return any("-9999" in str(val) for val in hazard_vals)
