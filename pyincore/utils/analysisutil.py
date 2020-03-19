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

from pyincore import DataService


class AnalysisUtil:
    """
    Utility methods for analysis
    """
    DOCSTR_FORMAT = "$DESC$ \n\n" \
                    "Args: \n\t" \
                    "$ARGS$ " \
                    "\n" \
                    "Returns: \n\t" \
                    "$RETS$ "

    @staticmethod
    def calculate_damage_interval(damage):
        output = collections.OrderedDict()
        if len(damage) == 4:
            output['ds-none'] = 1 - damage['ls-slight']
            output['ds-slight'] = damage['ls-slight'] - \
                                          damage['ls-moderat']
            output['ds-moderat'] = damage['ls-moderat'] - \
                                          damage['ls-extensi']
            output['ds-extensi'] = damage['ls-extensi'] - \
                                          damage['ls-complet']
            output['ds-complet'] = damage['ls-complet']
        elif len(damage) == 3:
            output['insignific'] = 1.0 - damage['immocc']
            output['moderate'] = damage['immocc'] - damage['lifesfty']
            output['heavy'] = damage['lifesfty'] - damage['collprev']
            output['complete'] = damage['collprev']

        return output

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
        '''
        Determine the parallelism on the current compute node
        Args:
            number_of_loops: total number of loops will be executed on current compute node
            user_defined_parallelism: a customized parallelism specified by users
        Returns:
            number_of_cpu: parallelism on current compute node
        '''

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
    def adjust_limit_states_for_pgd(limit_states, pgd_limit_states):
        try:
            adj_limit_states = collections.OrderedDict()

            for key, value in limit_states.items():
                adj_limit_states[key] = limit_states[key] + pgd_limit_states[
                    key] - \
                                        (limit_states[key] * pgd_limit_states[
                                            key])

            return adj_limit_states

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
            specs: Json of the specs for each analysis

        Returns:
            Google format docstrings to copy for the run() method of any analysis

        """
        desc = specs['description']
        args = ""
        rets = ""

        for dataset in specs['input_datasets']:
            isOpt = ""
            if not dataset['required']:
                isOpt = ", " + "optional"

            args = args + dataset['id'] + "(str" + isOpt + ") : " \
                   + dataset['description'] + \
                   ". " + AnalysisUtil.get_custom_types_str(
                dataset['type']) + "\n\t"

        for param in specs['input_parameters']:
            isOpt = ""
            if not param['required']:
                isOpt = ", " + "optional"

            args = args + param['id'] + "(" + AnalysisUtil.get_type_str(
                param['type']) + isOpt + ") : " \
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
            class_type(str): Example: <class 'int'>

        Returns:
            Text inside first single quotes of a string

        """

        t = str(class_type)
        match = re.search('\'([^"]*)\'', t)
        if match != None:
            return match.group(1)
        return None

    @staticmethod
    def get_custom_types_str(types):
        """
        Args:
            types: Can be string or List of strings

        Returns:
            Formatted string with applicable datatypes used to generate docstrigns from specs

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

    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
