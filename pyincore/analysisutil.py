import collections
from typing import List, Dict
import math
import os
from scipy.stats import norm
from py_expression_eval import Parser
from pyincore import DataService


class AnalysisUtil:
    """
    Utility methods for analysis
    """
    @staticmethod
    def get_building_period(num_stories, fragility_set):
        period = 0.0

        fragility_curve = fragility_set['fragilityCurves'][0]
        if fragility_curve['className'] == 'edu.illinois.ncsa.incore.services.fragility.model.PeriodStandardFragilityCurve':
            period_equation_type = fragility_curve['periodEqnType']
            if period_equation_type == 1:
                period = fragility_curve['periodParam0']
            elif period_equation_type == 2:
                period = fragility_curve['periodParam0'] * num_stories
            elif period_equation_type == 3:
                period = fragility_curve['periodParam1'] * math.pow(fragility_curve['periodParam0'] * num_stories,
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
            output['I_Moderate'] = damage['DS_Moderate'] - damage['DS_Extensive']
            output['I_Extensive'] = damage['DS_Extensive'] - damage['DS_Complete']
            output['I_Complete'] = damage['DS_Complete']
        elif len(damage) == 3:
            output['insignific'] = 1.0 - damage['immocc']
            output['moderate'] = damage['immocc'] - damage['lifesfty']
            output['heavy'] = damage['lifesfty'] - damage['collprev']
            output['complete'] = damage['collprev']
        return output

    @staticmethod
    def calculate_mean_damage(weights, dmg_intervals):
        output = collections.OrderedDict()
        if len(weights) == 5:
            output['MeanDamage'] = weights[0] * float(dmg_intervals['I_None']) \
                                   + weights[1] * float(dmg_intervals['I_Slight']) \
                                   + weights[2] * float(dmg_intervals['I_Moderate']) \
                                   + weights[3] * float(dmg_intervals['I_Extensive']) \
                                   + weights[4] * float(dmg_intervals['I_Complete'])
        elif len(weights) == 4:
            output['meandamage'] = float(weights[0]) * float(dmg_intervals['insignific']) + float(
                weights[1]) * float(
                dmg_intervals['moderate']) + float(weights[2]) * float(dmg_intervals['heavy']) + float(
                weights[3]) * float(
                dmg_intervals['complete'])
        return output

    @staticmethod
    def calculate_mean_damage_std_deviation(weights, weights_std_dev, dmg_intervals, mean_damage):
        output = collections.OrderedDict()
        result = 0.0

        idx = 0
        for dmg_interval in dmg_intervals:
            result += dmg_intervals[dmg_interval] * (math.pow(weights[idx], 2) + math.pow(weights_std_dev[idx], 2))
            idx += 1

        output['mdamagedev'] = math.sqrt(result - math.pow(mean_damage, 2))
        return output

    @staticmethod
    def determine_parallelism_locally(self, number_of_loops, user_defined_parallelism=0):
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
                return min(number_of_cpu, number_of_loops, user_defined_parallelism)
            else:
                return min(number_of_cpu, number_of_loops)
        else:
            return number_of_cpu;

    @staticmethod
    def create_result_dataset(datasvc: DataService, parentid: str, result_files: List[str], title: str, output_metadata: Dict[str, str]):
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
