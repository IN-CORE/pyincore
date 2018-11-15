import collections
from typing import List, Dict
import math
import os
import csv
import re
from scipy.stats import norm, lognorm
from py_expression_eval import Parser
from pyincore import DataService


class AnalysisUtil:
    """
    Utility methods for analysis
    """
    DOCSTR_FORMAT = "$DESC$ \n" \
                    "Args: \n\t" \
                    "$ARGS$ \n" \
                    "\n" \
                    "Returns: \n\t" \
                    "$RETS$ "

    @staticmethod
    def get_building_period(num_stories, fragility_set):
        period = 0.0

        fragility_curve = fragility_set['fragilityCurves'][0]
        if fragility_curve[
            'className'] == 'edu.illinois.ncsa.incore.services.fragility.model.PeriodStandardFragilityCurve':
            period_equation_type = fragility_curve['periodEqnType']
            if period_equation_type == 1:
                period = fragility_curve['periodParam0']
            elif period_equation_type == 2:
                period = fragility_curve['periodParam0'] * num_stories
            elif period_equation_type == 3:
                period = fragility_curve['periodParam1'] * math.pow(
                    fragility_curve['periodParam0'] * num_stories,
                    fragility_curve['periodParam2'])

        return period

    @staticmethod
    def calculate_damage(bridge_fragility, hazard_value):
        output = collections.OrderedDict()
        limit_states = map(str.strip, bridge_fragility.getProperties()[
            'LimitStates'].split(":"))
        for i in range(len(limit_states)):
            limit_state = limit_states[i]
            fragility_curve = bridge_fragility.getFragilities()[i]
            if fragility_curve.getType() == 'Normal':
                median = float(fragility_curve.getProperties()
                ['fragility-curve-median'])
                beta = float(fragility_curve.getProperties()
                ['fragility-curve-beta'])
                sp = (math.log(hazard_value) - math.log(median)) / beta
                p = norm.cdf(sp)
                output['DS_' + limit_state] = p

        return output

    @staticmethod
    def calculate_damage_json(fragility_set, hazard):
        fragility_curves = fragility_set['fragilityCurves']
        output = collections.OrderedDict()

        index = 0
        limit_state = ['immocc', 'lifesfty', 'collprev']
        for fragility_curve in fragility_curves:
            median = float(fragility_curve['median'])
            beta = float(fragility_curve['beta'])
            # limit_state = fragility_curve['description']
            probability = float(0.0)

            if hazard > 0.0:
                if (fragility_curve['curveType'] == 'Normal'):
                    sp = (math.log(hazard) - math.log(median)) / beta
                    probability = norm.cdf(sp)
                elif (fragility_curve['curveType'] == "LogNormal"):
                    x = (math.log(hazard) - median) / beta
                    probability = norm.cdf(x)

            output[limit_state[index]] = probability
            index += 1

        return output

    @staticmethod
    def calculate_damage_json2(fragility_set, hazard):
        # using the "description" for limit_state
        fragility_curves = fragility_set['fragilityCurves']
        output = collections.OrderedDict()

        for fragility_curve in fragility_curves:
            median = float(fragility_curve['median'])
            beta = float(fragility_curve['beta'])
            # limit_state = fragility_curve['description']
            probability = float(0.0)

            if hazard > 0.0:
                if (fragility_curve['curveType'] == 'Normal'):
                    sp = (math.log(hazard) - math.log(median)) / beta
                    probability = norm.cdf(sp)
                elif (fragility_curve['curveType'] == "LogNormal"):
                    x = (math.log(hazard) - median) / beta
                    probability = norm.cdf(x)

            output[fragility_curve['description']] = probability

        return output

    @staticmethod
    def calculate_damage_interval(damage):
        output = collections.OrderedDict()
        if len(damage) == 4:
            output['I_None'] = 1.0 - damage['DS_Slight']
            output['I_Slight'] = damage['DS_Slight'] - damage['DS_Moderate']
            output['I_Moderate'] = damage['DS_Moderate'] - damage[
                'DS_Extensive']
            output['I_Extensive'] = damage['DS_Extensive'] - damage[
                'DS_Complete']
            output['I_Complete'] = damage['DS_Complete']
        elif len(damage) == 3:
            output['insignific'] = 1.0 - damage['immocc']
            output['moderate'] = damage['immocc'] - damage['lifesfty']
            output['heavy'] = damage['lifesfty'] - damage['collprev']
            output['complete'] = damage['collprev']
        return output

    @staticmethod
    def calculate_mean_damage(dmg_ratio_tbl, dmg_intervals):
        output = collections.OrderedDict()
        if len(dmg_ratio_tbl) == 5:
            output['meandamage'] = float(
                dmg_ratio_tbl[1]["Best Mean Damage Ratio"]) * float(
                dmg_intervals['I_Slight']) \
                                   + float(
                dmg_ratio_tbl[2]["Best Mean Damage Ratio"]) * float(
                dmg_intervals['I_Moderate']) \
                                   + float(
                dmg_ratio_tbl[3]["Best Mean Damage Ratio"]) * float(
                dmg_intervals['I_Extensive']) \
                                   + float(
                dmg_ratio_tbl[4]["Best Mean Damage Ratio"]) * float(
                dmg_intervals['I_Complete'])
        elif len(dmg_ratio_tbl) == 4:
            output['meandamage'] = float(
                dmg_ratio_tbl[0]["Mean Damage Factor"]) * float(
                dmg_intervals["insignific"]) + \
                                   float(dmg_ratio_tbl[1][
                                       "Mean Damage Factor"]) * float(
                dmg_intervals['moderate']) + \
                                   float(dmg_ratio_tbl[2][
                                       "Mean Damage Factor"]) * float(
                dmg_intervals['heavy']) + \
                                   float(dmg_ratio_tbl[3][
                                       "Mean Damage Factor"]) * float(
                dmg_intervals['complete'])
        return output

    @staticmethod
    def calculate_mean_damage_std_deviation(dmg_ratio_tbl, dmg_intervals,
                                            mean_damage):
        output = collections.OrderedDict()
        result = 0.0

        idx = 0
        for dmg_interval in dmg_intervals:
            result += dmg_intervals[dmg_interval] * (math.pow(
                float(dmg_ratio_tbl[idx]["Mean Damage Factor"]), 2) +
                                                     math.pow(float(
                                                         dmg_ratio_tbl[idx][
                                                             "Deviation Damage Factor"]),
                                                         2))
            idx += 1

        output['mdamagedev'] = math.sqrt(result - math.pow(mean_damage, 2))
        return output

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
            return number_of_cpu;

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
    def compute_custom_limit_state_probability(fragility_set, variables: dict):
        """Computes custom expression fragility values
        :param fragility_set: fragility set with custom expression
        :param variables: variables to set
        :return:
        """

        fragility_curves = fragility_set['fragilityCurves']
        limit_state_prob = 0.0
        for fragility_curve in fragility_curves:
            if fragility_curve['className'] == \
                    'edu.illinois.ncsa.incore.service.fragility.models.CustomExpressionFragilityCurve':
                expression = fragility_curve['expression']
                parser = Parser()
                limit_state_prob = parser.parse(expression).evaluate(variables)

        return limit_state_prob

    @staticmethod
    def compute_cdf(curve, val, std_dev=0):
        if val == 0:
            return 0

        median = curve['median']
        beta = curve['beta']

        if std_dev != 0:
            beta = math.sqrt(math.pow(beta, 2) + math.pow(std_dev, 2))

        if curve['curveType'].lower() == 'normal':
            x = math.log(val / median) / beta
            return norm.cdf(x)
        elif curve['curveType'].lower() == 'lognormal':
            x = (math.log(val) - median) / beta
            return norm.cdf(x)

    @staticmethod
    def compute_limit_state_probability(fragility_curves, hazard_val, yvalue,
                                        std_dev):
        ls_probs = collections.OrderedDict()
        for fragility in fragility_curves:
            ls_probs['ls_' + fragility['description'].lower()] = \
                AnalysisUtil.compute_cdf(fragility, hazard_val, std_dev)
        return ls_probs

    @staticmethod
    def compute_damage_intervals(ls_probs):
        # Assumes that 4 limit states are present: slight, moderate, extensive and complete
        try:
            dmg_intervals = collections.OrderedDict()
            dmg_intervals['none'] = 1 - ls_probs['ls_slight']
            # what happens when this value is negative ie, moderate > slight
            dmg_intervals['slight-mod'] = ls_probs['ls_slight'] - \
                                          ls_probs['ls_moderate']
            dmg_intervals['mod-extens'] = ls_probs['ls_moderate'] - \
                                          ls_probs['ls_extensive']
            dmg_intervals['ext-comple'] = ls_probs['ls_extensive'] - \
                                          ls_probs['ls_complete']
            dmg_intervals['complete'] = ls_probs['ls_complete']
            return dmg_intervals

        except KeyError as e:
            print('This function only works with the 4 hazus limit states - '
                  'slight, moderate, extensive, complete')
            print(str(e))

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
    def get_csv_table_rows(csv_reader: csv.DictReader):
        csv_rows = []

        # Ignore the header
        row_index = 0
        for row in csv_reader:
            if row_index > 0:
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
